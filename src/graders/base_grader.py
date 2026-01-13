"""
Base grader class defining the grading interface.
"""

from abc import ABC, abstractmethod
import logging
from datetime import datetime
from typing import Optional

from src.models import GradingRequest, GradingResult, CriterionScore
from src.llm import OpenAIClient, ResponseParser

logger = logging.getLogger(__name__)


class BaseGrader(ABC):
    """
    Abstract base class for all grading strategies.

    Subclasses must implement the grade() method.
    """

    def __init__(self, llm_client: OpenAIClient):
        """
        Initialize the grader.

        Args:
            llm_client: OpenAI API client
        """
        self.llm_client = llm_client
        self.response_parser = ResponseParser()

    @abstractmethod
    def grade(self, request: GradingRequest) -> GradingResult:
        """
        Grade a student submission.

        Args:
            request: Grading request containing problem, solution, rubric, and code

        Returns:
            GradingResult with scores and feedback
        """
        pass

    def _parse_llm_response(self, response_text: str) -> dict:
        """
        Parse and validate LLM response.

        Args:
            response_text: Raw response from LLM

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If response cannot be parsed or is invalid
        """
        try:
            parsed = self.response_parser.extract_json(response_text)

            if not self.response_parser.validate_grading_response(parsed):
                logger.warning("LLM response missing required fields")

            return parsed
        except ValueError as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            raise

    def _build_result(
        self,
        parsed_response: dict,
        request: GradingRequest,
        strategy_name: str,
        reasoning_trace: Optional[str] = None,
    ) -> GradingResult:
        """
        Build a GradingResult from parsed LLM response.

        Args:
            parsed_response: Parsed JSON from LLM
            request: Original grading request
            strategy_name: Name of grading strategy used
            reasoning_trace: Optional reasoning trace for transparency

        Returns:
            GradingResult object
        """
        final_grade = parsed_response.get("final_grade", {})
        breakdown_data = parsed_response.get("breakdown", [])

        # Extract scores
        total_score = final_grade.get("total_score", 0)
        total_possible = final_grade.get("total_possible", request.rubric.total_points)
        percentage = final_grade.get("percentage", 0)

        # Ensure we have the right total
        if total_possible != request.rubric.total_points:
            total_possible = request.rubric.total_points
            if total_score > 0:
                percentage = (total_score / total_possible) * 100

        # Build breakdown
        breakdown = []
        for item in breakdown_data:
            breakdown.append(
                CriterionScore(
                    criterion_name=item.get("criterion", item.get("criterion_name", "")),
                    points_awarded=float(item.get("score", item.get("points_awarded", 0))),
                    max_points=float(item.get("max_score", item.get("max_points", 0))),
                    feedback=item.get("feedback", ""),
                )
            )

        # Build result
        result = GradingResult(
            final_score=total_score,
            total_points=total_possible,
            percentage=percentage,
            breakdown=breakdown,
            overall_feedback=final_grade.get(
                "overall_feedback",
                parsed_response.get("overall_feedback", ""),
            ),
            grading_strategy=strategy_name,
            model_used=self.llm_client.model,
            timestamp=datetime.utcnow(),
            reasoning_trace=reasoning_trace,
        )

        # Validate the result
        if not result.validate_score():
            logger.warning("Breakdown scores do not sum to final score")

        return result

    @staticmethod
    def validate_request(request: GradingRequest) -> bool:
        """
        Validate a grading request.

        Args:
            request: Grading request

        Returns:
            True if valid, False otherwise
        """
        if not request.validate_rubric():
            logger.error("Rubric totals do not match")
            return False

        if not request.problem_description or not request.student_code:
            logger.error("Missing problem or student code")
            return False

        return True
