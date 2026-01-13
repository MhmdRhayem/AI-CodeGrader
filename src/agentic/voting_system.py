"""
Voting system for parallelized grading with consensus.
"""

import asyncio
import logging
import statistics
from typing import List, Dict, Any

from src.models import GradingRequest, GradingResult, CriterionScore
from src.llm import OpenAIClient
from prompts import PromptBuilder, ResponseParser, COT_SYSTEM_PROMPT, COT_USER_PROMPT_TEMPLATE
from datetime import datetime

logger = logging.getLogger(__name__)


class VotingSystem:
    """
    Consensus voting system for multiple independent LLM graders.

    Generates N independent grades with different temperatures,
    then aggregates using median voting and consensus feedback.
    """

    def __init__(self, llm_client: OpenAIClient, num_voters: int = 5):
        self.llm_client = llm_client
        self.num_voters = num_voters
        self.response_parser = ResponseParser()

    async def grade(
        self,
        request: GradingRequest,
        llm_temperature_range: tuple = (0.3, 0.7),
    ) -> GradingResult:
        logger.info(
            f"Starting parallel grading with {self.num_voters} voters"
        )

        # Generate requests for each voter with different temperatures
        min_temp, max_temp = llm_temperature_range
        temp_step = (max_temp - min_temp) / (self.num_voters - 1)

        voter_requests = []
        for i in range(self.num_voters):
            temperature = min_temp + (i * temp_step)
            voter_requests.append({
                "system": COT_SYSTEM_PROMPT,
                "user": PromptBuilder.build_grading_prompt(
                    request, COT_USER_PROMPT_TEMPLATE
                ),
                "temperature": temperature,
                "max_tokens": 3000,
                "response_format": {"type": "json_object"},
            })

        logger.debug(f"Created {len(voter_requests)} grading requests with temperatures: "
                    f"{[r['temperature'] for r in voter_requests]}")

        try:
            # Execute all grading requests in parallel
            responses = await self.llm_client.batch_chat_completions(voter_requests)

            # Parse all responses
            grades = []
            for i, response_text in enumerate(responses):
                try:
                    parsed = self.response_parser.extract_json(response_text)
                    grades.append((i, parsed))
                    logger.debug(f"Voter {i+1} grading parsed successfully")
                except Exception as e:
                    logger.warning(f"Voter {i+1} response parsing failed: {str(e)}")
                    continue

            if not grades:
                raise ValueError("No valid grades received from voters")

            logger.info(f"Received {len(grades)} valid grades from {self.num_voters} voters")

            # Aggregate grades using voting
            aggregated_grade = self._aggregate_votes(
                grades, request
            )

            return aggregated_grade

        except Exception as e:
            logger.error(f"Error in parallel voting: {str(e)}")
            raise

    def _aggregate_votes(
        self,
        grades: List[tuple],
        request: GradingRequest,
    ) -> GradingResult:
        """
        Aggregate multiple grades using voting and consensus.

        Args:
            grades: List of (voter_id, parsed_response) tuples
            request: Original grading request

        Returns:
            Aggregated GradingResult
        """
        logger.debug("Starting vote aggregation")

        # Extract scores for each criterion
        criterion_votes = {}
        feedback_collection = {}

        for voter_id, parsed_response in grades:
            # Breakdown can be at root or inside final_grade (backward compatibility)
            breakdown = parsed_response.get("breakdown", [])
            if not breakdown:
                final_grade = parsed_response.get("final_grade", {})
                breakdown = final_grade.get("breakdown", [])

            for criterion_score in breakdown:
                criterion_name = criterion_score.get("criterion_name",
                                                     criterion_score.get("criterion"))
                score = float(criterion_score.get("points_awarded",
                                                  criterion_score.get("score", 0)))
                feedback = criterion_score.get("feedback", "")

                if criterion_name not in criterion_votes:
                    criterion_votes[criterion_name] = []
                    feedback_collection[criterion_name] = []

                criterion_votes[criterion_name].append(score)
                feedback_collection[criterion_name].append(feedback)

        # Compute median score for each criterion
        aggregated_breakdown = []
        for criterion in request.rubric.criteria:
            if criterion.name not in criterion_votes:
                logger.warning(f"No votes for criterion: {criterion.name}")
                continue

            scores = criterion_votes[criterion.name]
            median_score = statistics.median(scores)
            mean_score = statistics.mean(scores)

            # Collect feedback from voters near the median
            relevant_feedbacks = []
            for score, feedback in zip(scores, feedback_collection[criterion.name]):
                if abs(score - median_score) <= 0.5:  # Within 0.5 points of median
                    relevant_feedbacks.append(feedback)

            # Merge feedback
            merged_feedback = self._merge_feedback(relevant_feedbacks)

            aggregated_breakdown.append(
                CriterionScore(
                    criterion_name=criterion.name,
                    points_awarded=mean_score,
                    max_points=criterion.max_points,
                    feedback=merged_feedback,
                )
            )

            logger.debug(
                f"{criterion.name}: median={median_score:.1f}, "
                f"mean={mean_score:.1f}, votes={len(scores)}"
            )

        # Calculate total score
        total_score = sum(c.points_awarded for c in aggregated_breakdown)
        percentage = (total_score / request.rubric.total_points) * 100

        # Generate consensus overall feedback
        overall_feedbacks = []
        for _, parsed in grades:
            # Check root level first, then final_grade
            feedback = parsed.get("overall_feedback")
            if not feedback:
                feedback = parsed.get("final_grade", {}).get("overall_feedback", "")
            if feedback:
                overall_feedbacks.append(feedback)
        consensus_feedback = self._merge_feedback(overall_feedbacks)

        result = GradingResult(
            final_score=total_score,
            total_points=request.rubric.total_points,
            percentage=percentage,
            breakdown=aggregated_breakdown,
            overall_feedback=consensus_feedback,
            grading_strategy="voting",
            model_used=self.llm_client.model,
            timestamp=datetime.utcnow(),
            reasoning_trace=f"Aggregated from {len(grades)} independent graders "
                            f"using median voting (temperature range: 0.3-0.7)",
        )

        logger.info(f"Voting aggregation complete. Final score: {total_score:.1f}")
        return result

    @staticmethod
    def _merge_feedback(feedback_list: List[str]) -> str:
        """
        Merge multiple feedback strings into a single summary.

        Args:
            feedback_list: List of feedback strings

        Returns:
            Merged feedback string
        """
        if not feedback_list:
            return "Consensus evaluation"

        # Remove duplicates and empty strings
        unique_feedbacks = list(dict.fromkeys(f for f in feedback_list if f.strip()))

        if len(unique_feedbacks) == 0:
            return "Consensus evaluation"
        elif len(unique_feedbacks) == 1:
            return unique_feedbacks[0]
        else:
            # Combine multiple feedback items
            return " ".join(unique_feedbacks[:2])  # Take first 2 unique feedbacks
