"""
FastAPI backend for C++ Grading Agent.
"""

import logging
from typing import Dict, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from src.llm import OpenAIClient
from src.graders import (
    ChainOfThoughtGrader,
    FewShotCoTGrader,
    VotingGrader,
    EvaluatorOptimizerGrader,
)
from src.models import GradingRequest, GradingResult
from src.models import GradingRequest, GradingResult
from src.models.batch import BatchGradingRequest, BatchGradingResult, BatchItemResult

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LLM-Based C++ Grading Agent",
    description="Automated grading of C++ submissions using Large Language Models",
    version="1.0.0",
)

# Add CORS middleware to allow Gradio frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM client
logger.info(f"Initializing OpenAI client with model: {settings.model_name}")
llm_client = OpenAIClient(
    api_key=settings.openai_api_key,
    model=settings.model_name,
    temperature=settings.temperature,
    max_tokens=settings.max_tokens,
)

# Initialize graders
graders: Dict = {
    "cot": ChainOfThoughtGrader(llm_client),
    "few_shot_cot": FewShotCoTGrader(llm_client),
    "voting": VotingGrader(
        llm_client, num_voters=settings.voting_num_voters
    ),
    "evaluator_optimizer": EvaluatorOptimizerGrader(
        llm_client, max_iterations=settings.evaluator_optimizer_max_iterations
    ),
}

logger.info(f"Initialized {len(graders)} grading strategies")


@app.on_event("startup")
async def startup_event():
    """Called when the app starts."""
    logger.info("Grading Agent API starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """Called when the app shuts down."""
    logger.info("Grading Agent API shutting down")


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint with API information.
    """
    return {
        "message": "LLM-Based C++ Grading Agent API",
        "version": "1.0.0",
        "model": settings.model_name,
        "endpoints": {
            "grade": "/api/v1/grade",
            "strategies": "/api/v1/grade/strategies",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


@app.post("/api/v1/grade", response_model=GradingResult)
async def grade_submission(request: GradingRequest) -> GradingResult:
    try:
        logger.info(
            f"Received grading request with strategy: {request.grading_strategy}"
        )
        logger.debug(f"Request validation details: "
                    f"problem_len={len(request.problem_description)}, "
                    f"student_code_len={len(request.student_code)}, "
                    f"rubric_criteria_count={len(request.rubric.criteria)}")

        # Validate rubric
        if not request.validate_rubric():
            criteria_sum = sum(c.max_points for c in request.rubric.criteria)
            error_detail = (
                f"Rubric validation failed: Sum of criteria points ({criteria_sum:.1f}) "
                f"does not match total_points ({request.rubric.total_points:.1f}). "
                f"Criteria breakdown: {[f'{c.name}({c.max_points})' for c in request.rubric.criteria]}"
            )
            logger.warning(error_detail)
            raise HTTPException(status_code=400, detail=error_detail)

        # Get the appropriate grader
        grader = graders.get(request.grading_strategy)
        if not grader:
            available_strategies = list(graders.keys())
            error_detail = (
                f"Invalid grading strategy '{request.grading_strategy}'. "
                f"Available: {', '.join(available_strategies)}"
            )
            logger.warning(error_detail)
            raise HTTPException(status_code=400, detail=error_detail)

        logger.debug(f"Using grader: {grader.__class__.__name__}")

        # Perform grading
        result = grader.grade(request)

        logger.info(
            f"Grading successful. Score: {result.final_score}/{result.total_points} "
            f"({result.percentage:.1f}%)"
        )

        return result

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during grading: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/v1/grade_batch", response_model=BatchGradingResult)
async def grade_submissions_batch(request: BatchGradingRequest) -> BatchGradingResult:
    try:
        logger.info(
            f"Received BATCH grading request with strategy: {request.grading_strategy}, "
            f"files: {len(request.submissions)}"
        )

        # Validate rubric (same behavior as single endpoint)
        if not request.validate_rubric():
            criteria_sum = sum(c.max_points for c in request.rubric.criteria)
            error_detail = (
                f"Rubric validation failed: Sum of criteria points ({criteria_sum:.1f}) "
                f"does not match total_points ({request.rubric.total_points:.1f}). "
                f"Criteria breakdown: {[f'{c.name}({c.max_points})' for c in request.rubric.criteria]}"
            )
            logger.warning(error_detail)
            raise HTTPException(status_code=400, detail=error_detail)

        # Validate strategy
        grader = graders.get(request.grading_strategy)
        if not grader:
            available_strategies = list(graders.keys())
            error_detail = (
                f"Invalid grading strategy '{request.grading_strategy}'. "
                f"Available: {', '.join(available_strategies)}"
            )
            logger.warning(error_detail)
            raise HTTPException(status_code=400, detail=error_detail)

        results = []
        ok = 0

        # Grade each file independently, but return all results (even if some fail)
        for sub in request.submissions:
            try:
                single_req = GradingRequest(
                    problem_description=request.problem_description,
                    reference_solution=request.reference_solution,
                    rubric=request.rubric,
                    student_code=sub.student_code,
                    grading_strategy=request.grading_strategy,
                )

                res: GradingResult = grader.grade(single_req)
                results.append(BatchItemResult(filename=sub.filename, result=res, error=None))
                ok += 1

            except Exception as e:
                logger.error(f"Batch item failed ({sub.filename}): {str(e)}", exc_info=True)
                results.append(BatchItemResult(filename=sub.filename, result=None, error=str(e)))

        return BatchGradingResult(count=len(results), ok=ok, results=results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during batch grading: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v1/grade/strategies")
async def list_strategies() -> Dict[str, Dict[str, str]]:
    """
    List available grading strategies.

    Returns:
    - Dictionary mapping strategy names to descriptions
    """
    return {
        "cot": {
            "name": "Chain-of-Thought",
            "description": "Instructs LLM to reason step-by-step before grading",
            "speed": "Fast",
            "cost": "Low",
            "accuracy": "Good",
        },
        "few_shot_cot": {
            "name": "Few-Shot Chain-of-Thought",
            "description": "Provides grading examples to teach the LLM patterns",
            "speed": "Fast",
            "cost": "Medium",
            "accuracy": "Better",
        },
        "voting": {
            "name": "Voting/Parallelization",
            "description": "Generates multiple independent grades and aggregates with voting",
            "speed": "Slower",
            "cost": "High",
            "accuracy": "Best",
        },
        "evaluator_optimizer": {
            "name": "Evaluator-Optimizer",
            "description": "Two-agent iterative refinement with critique and improvement",
            "speed": "Slower",
            "cost": "High",
            "accuracy": "Best",
        },
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(
        f"Starting Grading Agent API on {settings.api_host}:{settings.api_port}"
    )
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
