"""
Chain-of-Thought (CoT) grading strategy.
"""

import logging
from typing import Optional

from src.models import GradingRequest, GradingResult
from src.graders.base_grader import BaseGrader
from src.llm import OpenAIClient, PromptBuilder
from config.prompts.cot_prompt import COT_SYSTEM_PROMPT, COT_USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class ChainOfThoughtGrader(BaseGrader):
    """
    Grader using Chain-of-Thought prompting.

    Instructs the LLM to reason step-by-step before providing a grade.
    This improves accuracy by making the reasoning process explicit.
    """

    def __init__(
        self,
        llm_client: OpenAIClient,
        temperature: float = 0.3,
        max_tokens: int = 3000,
    ):
        """
        Initialize the CoT grader.

        Args:
            llm_client: OpenAI API client
            temperature: Temperature for LLM (lower = more consistent)
            max_tokens: Maximum tokens in response
        """
        super().__init__(llm_client)
        self.temperature = temperature
        self.max_tokens = max_tokens

    def grade(self, request: GradingRequest) -> GradingResult:
        """
        Grade a student submission using Chain-of-Thought prompting.

        Args:
            request: Grading request

        Returns:
            GradingResult with scores and reasoning trace

        Raises:
            ValueError: If LLM response cannot be parsed
        """
        # Validate request
        if not self.validate_request(request):
            raise ValueError("Invalid grading request")

        logger.info(f"Grading submission using Chain-of-Thought strategy")

        try:
            # Build the prompt
            user_prompt = PromptBuilder.build_grading_prompt(
                request, COT_USER_PROMPT_TEMPLATE
            )

            # Call LLM with explicit JSON response format
            response_text = self.llm_client.chat_completion(
                system=COT_SYSTEM_PROMPT,
                user=user_prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            logger.debug(f"LLM response received (length: {len(response_text)})")

            # Parse response
            parsed_response = self._parse_llm_response(response_text)

            # Extract reasoning trace for transparency
            reasoning_trace = self._format_reasoning_trace(parsed_response)

            # Build and return result
            result = self._build_result(
                parsed_response,
                request,
                strategy_name="cot",
                reasoning_trace=reasoning_trace,
            )

            logger.info(f"Grading complete. Score: {result.final_score}/{result.total_points}")
            return result

        except Exception as e:
            logger.error(f"Error in Chain-of-Thought grading: {str(e)}")
            raise

    def _format_reasoning_trace(self, parsed_response: dict) -> str:
        """
        Format the reasoning trace from the LLM response.

        Args:
            parsed_response: Parsed JSON from LLM

        Returns:
            Formatted reasoning trace string
        """
        reasoning = parsed_response.get("reasoning", {})

        trace_parts = []

        # Understanding phase
        if "understanding" in reasoning:
            trace_parts.append("## Problem Understanding")
            trace_parts.append(reasoning["understanding"])
            trace_parts.append("")

        # Reference analysis
        if "reference_analysis" in reasoning:
            trace_parts.append("## Reference Solution Analysis")
            trace_parts.append(reasoning["reference_analysis"])
            trace_parts.append("")

        # Code analysis
        if "code_analysis" in reasoning:
            trace_parts.append("## Student Code Analysis")
            trace_parts.append(reasoning["code_analysis"])
            trace_parts.append("")

        # Criterion evaluations
        if "criterion_evaluations" in reasoning:
            trace_parts.append("## Criterion-by-Criterion Evaluation")
            for criterion_eval in reasoning["criterion_evaluations"]:
                criterion_name = criterion_eval.get("criterion_name", "Unknown")
                analysis = criterion_eval.get("analysis", "")
                points = criterion_eval.get("points_awarded", 0)
                max_points = criterion_eval.get("max_points", 0)

                trace_parts.append(f"\n### {criterion_name} ({points}/{max_points})")
                trace_parts.append(analysis)

        return "\n".join(trace_parts)
