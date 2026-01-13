"""
Evaluator-Optimizer agentic grading strategy.
"""

import logging
from typing import List, Tuple

from src.models import GradingRequest, GradingResult
from src.graders.base_grader import BaseGrader
from src.llm import OpenAIClient
from src.agentic.evaluator import Evaluator
from src.agentic.optimizer import Optimizer
from datetime import datetime

logger = logging.getLogger(__name__)


class EvaluatorOptimizerGrader(BaseGrader):
    """
    Grader using two-agent Evaluator-Optimizer workflow.

    The Evaluator creates an initial grade with detailed reasoning.
    The Optimizer critiques it for fairness and accuracy.
    If issues are found, the Evaluator refines the grade.
    This iterative process continues until convergence or max iterations.
    """

    def __init__(
        self,
        llm_client: OpenAIClient,
        max_iterations: int = 3,
    ):
        """
        Initialize the Evaluator-Optimizer grader.

        Args:
            llm_client: OpenAI API client
            max_iterations: Maximum refinement iterations
        """
        super().__init__(llm_client)
        self.max_iterations = max_iterations
        self.evaluator = Evaluator(llm_client)
        self.optimizer = Optimizer(llm_client)

    def grade(self, request: GradingRequest) -> GradingResult:
        """
        Grade a student submission using Evaluator-Optimizer workflow.

        Args:
            request: Grading request

        Returns:
            GradingResult with refined consensus grade

        Raises:
            ValueError: If validation fails
        """
        # Validate request
        if not self.validate_request(request):
            raise ValueError("Invalid grading request")

        logger.info(
            f"Starting Evaluator-Optimizer grading (max {self.max_iterations} iterations)"
        )

        try:
            # Initialize iteration history
            iteration_history: List[Tuple[dict, dict]] = []

            # Step 1: Evaluator creates initial grade
            logger.debug("Iteration 1: Evaluator creating initial grade...")
            current_grade = self.evaluator.grade(request)
            iteration_history.append((current_grade, {}))

            # Iterative refinement loop
            for iteration in range(1, self.max_iterations):
                logger.debug(f"Iteration {iteration + 1}: Optimizer critiquing grade...")

                # Step 2: Optimizer critiques the grade
                critique = self.optimizer.critique(request, current_grade)
                iteration_history[-1] = (current_grade, critique)

                # Check if optimizer approved the grade
                if critique.get("approved", False):
                    logger.info(
                        f"Grade approved by optimizer at iteration {iteration + 1}"
                    )
                    break

                # If issues found and not at max iterations, refine
                if Optimizer.has_issues(critique) and iteration < self.max_iterations - 1:
                    logger.debug(
                        f"Iteration {iteration + 1}: Evaluator refining grade based on feedback..."
                    )

                    # Step 3: Evaluator refines based on critique
                    refined_grade = self.evaluator.refine(
                        request, current_grade, critique
                    )
                    current_grade = refined_grade
                    iteration_history.append((refined_grade, {}))
                else:
                    # No more iterations or no issues
                    break

            logger.info(
                f"Evaluator-Optimizer workflow complete after {len(iteration_history)} iterations"
            )

            # Build result from final grade
            reasoning_trace = self._format_iteration_history(
                iteration_history, self.max_iterations
            )

            result = self._build_result(
                current_grade,
                request,
                strategy_name="evaluator_optimizer",
                reasoning_trace=reasoning_trace,
            )

            logger.info(
                f"Final grade: {result.final_score}/{result.total_points} "
                f"({result.percentage:.1f}%)"
            )
            return result

        except Exception as e:
            logger.error(f"Error in Evaluator-Optimizer grading: {str(e)}")
            raise

    def _format_iteration_history(
        self,
        iteration_history: List[Tuple[dict, dict]],
        max_iterations: int,
    ) -> str:
        """
        Format the iteration history for the reasoning trace.

        Args:
            iteration_history: History of grades and critiques
            max_iterations: Maximum iterations

        Returns:
            Formatted iteration trace
        """
        parts = []

        parts.append(
            f"## Evaluator-Optimizer Workflow ({len(iteration_history)} iterations)\n"
        )
        parts.append(f"Max iterations: {max_iterations}\n")

        for i, (grade, critique) in enumerate(iteration_history, 1):
            parts.append(f"\n### Iteration {i}")

            # Grade information
            final_grade = grade.get("final_grade", {})
            total_score = final_grade.get("total_score", 0)
            percentage = final_grade.get("percentage", 0)
            parts.append(f"**Grade:** {total_score:.1f} ({percentage:.0f}%)")

            # Critique information if available
            if critique:
                approved = critique.get("approved", False)
                confidence = critique.get("confidence", 0)
                issues = critique.get("issues_found", [])

                parts.append(
                    f"\n**Optimizer Review:**\n"
                    f"- Approved: {approved}\n"
                    f"- Confidence: {confidence:.0%}\n"
                    f"- Issues found: {len(issues)}"
                )

                if issues:
                    for issue in issues:
                        criterion = issue.get("criterion", "Unknown")
                        problem = issue.get("issue", "")
                        suggested = issue.get("suggested_score", "N/A")
                        parts.append(f"  - {criterion}: {suggested} ({problem})")

        return "\n".join(parts)
