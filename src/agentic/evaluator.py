"""
Evaluator agent for the Evaluator-Optimizer workflow.
"""

import logging
from typing import Dict, Any

from src.models import GradingRequest
from src.llm import OpenAIClient
from prompts import (
    PromptBuilder,
    ResponseParser,
    EVALUATOR_SYSTEM_PROMPT,
    EVALUATOR_GRADE_PROMPT_TEMPLATE,
    EVALUATOR_REFINE_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


class Evaluator:
    """
    Evaluator agent that creates detailed grades.
    """

    def __init__(self, llm_client: OpenAIClient, temperature: float = 0.3):
        """
        Initialize the evaluator.

        Args:
            llm_client: OpenAI API client
            temperature: LLM temperature for consistency
        """
        self.llm_client = llm_client
        self.temperature = temperature
        self.response_parser = ResponseParser()

    def grade(self, request: GradingRequest) -> Dict[str, Any]:
        """
        Create an initial grade for the submission.

        Args:
            request: Grading request

        Returns:
            Parsed grading response
        """
        logger.debug("Evaluator creating initial grade...")

        try:
            # Build prompt
            prompt = PromptBuilder.build_grading_prompt(
                request, EVALUATOR_GRADE_PROMPT_TEMPLATE
            )

            # Call LLM
            response_text = self.llm_client.chat_completion(
                system=EVALUATOR_SYSTEM_PROMPT,
                user=prompt,
                temperature=self.temperature,
                max_tokens=3000,
                response_format={"type": "json_object"},
            )

            # Parse response
            parsed = self.response_parser.extract_json(response_text)
            logger.debug("Initial grade created successfully")
            return parsed

        except Exception as e:
            logger.error(f"Error in evaluator.grade: {str(e)}")
            raise

    def refine(
        self,
        request: GradingRequest,
        previous_grade: Dict[str, Any],
        critique: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Refine the grade based on optimizer feedback.

        Args:
            request: Grading request
            previous_grade: Previous grade from evaluator
            critique: Critique from optimizer

        Returns:
            Refined grade
        """
        logger.debug("Evaluator refining grade based on feedback...")

        try:
            import json

            # Build refinement prompt
            prompt = EVALUATOR_REFINE_PROMPT_TEMPLATE.format(
                problem_description=request.problem_description,
                reference_solution=PromptBuilder.format_code_block(
                    request.reference_solution
                ),
                rubric_json=PromptBuilder.format_rubric_json(request.rubric),
                student_code=PromptBuilder.format_code_block(request.student_code),
                previous_grade=json.dumps(previous_grade, indent=2),
                critique=json.dumps(critique, indent=2),
            )

            # Call LLM
            response_text = self.llm_client.chat_completion(
                system=EVALUATOR_SYSTEM_PROMPT,
                user=prompt,
                temperature=self.temperature,
                max_tokens=3000,
                response_format={"type": "json_object"},
            )

            # Parse response
            parsed = self.response_parser.extract_json(response_text)
            logger.debug("Grade refined successfully")
            return parsed

        except Exception as e:
            logger.error(f"Error in evaluator.refine: {str(e)}")
            raise
