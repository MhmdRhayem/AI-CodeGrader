"""
Optimizer agent for the Evaluator-Optimizer workflow.
"""

import json
import logging
from typing import Dict, Any

from src.models import GradingRequest
from src.llm import OpenAIClient
from prompts import (
    PromptBuilder,
    ResponseParser,
    OPTIMIZER_SYSTEM_PROMPT,
    OPTIMIZER_CRITIQUE_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


class Optimizer:
    """
    Optimizer agent that critiques and validates grades.
    """

    def __init__(self, llm_client: OpenAIClient, temperature: float = 0.4):
        """
        Initialize the optimizer.

        Args:
            llm_client: OpenAI API client
            temperature: LLM temperature (slightly higher for critical analysis)
        """
        self.llm_client = llm_client
        self.temperature = temperature
        self.response_parser = ResponseParser()

    def critique(
        self,
        request: GradingRequest,
        grade: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Critique a grade for fairness and accuracy.

        Args:
            request: Grading request
            grade: Grade to critique

        Returns:
            Critique response with approval status and issues
        """
        logger.debug("Optimizer critiquing grade...")

        try:
            # Build critique prompt
            prompt = OPTIMIZER_CRITIQUE_PROMPT_TEMPLATE.format(
                problem_description=request.problem_description,
                reference_solution=PromptBuilder.format_code_block(
                    request.reference_solution
                ),
                rubric_json=PromptBuilder.format_rubric_json(request.rubric),
                student_code=PromptBuilder.format_code_block(request.student_code),
                current_grade=json.dumps(grade, indent=2),
            )

            # Call LLM
            response_text = self.llm_client.chat_completion(
                system=OPTIMIZER_SYSTEM_PROMPT,
                user=prompt,
                temperature=self.temperature,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            # Parse response
            parsed = self.response_parser.extract_json(response_text)

            # Check if approved
            approved = parsed.get("approved", False)
            issues = parsed.get("issues_found", [])
            assessment = parsed.get("overall_assessment", "")
            confidence = parsed.get("confidence", 0.5)

            logger.debug(
                f"Critique complete. Approved: {approved}, Issues: {len(issues)}, "
                f"Confidence: {confidence:.2f}"
            )

            return {
                "approved": approved,
                "issues_found": issues,
                "overall_assessment": assessment,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Error in optimizer.critique: {str(e)}")
            raise

    @staticmethod
    def has_issues(critique: Dict[str, Any]) -> bool:
        """
        Check if critique found any issues.

        Args:
            critique: Critique response

        Returns:
            True if issues were found, False otherwise
        """
        issues = critique.get("issues_found", [])
        return len(issues) > 0 and not critique.get("approved", False)
