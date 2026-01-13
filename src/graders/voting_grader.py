"""
Voting/Parallelization grading strategy.
"""

import asyncio
import logging
from typing import Optional

from src.models import GradingRequest, GradingResult
from src.graders.base_grader import BaseGrader
from src.llm import OpenAIClient
from src.agentic.voting_system import VotingSystem

logger = logging.getLogger(__name__)


class VotingGrader(BaseGrader):
    """
    Grader using parallelization with voting consensus.

    Generates N independent grades with different temperatures in parallel,
    then aggregates using median voting and consensus feedback.
    Reduces variance and improves robustness.
    """

    def __init__(
        self,
        llm_client: OpenAIClient,
        num_voters: int = 5,
        temperature_range: tuple = (0.3, 0.7),
    ):
        """
        Initialize the Voting grader.

        Args:
            llm_client: OpenAI API client
            num_voters: Number of independent graders to use in voting
            temperature_range: (min_temp, max_temp) for voter temperature variation
        """
        super().__init__(llm_client)
        self.num_voters = num_voters
        self.temperature_range = temperature_range
        self.voting_system = VotingSystem(llm_client, num_voters)

    def grade(self, request: GradingRequest) -> GradingResult:
        """
        Grade a student submission using parallel voting.

        Spawns N independent graders with different temperatures,
        collects their grades, and aggregates using median voting.

        Args:
            request: Grading request

        Returns:
            GradingResult with aggregated consensus grade

        Raises:
            ValueError: If validation fails or no valid grades received
        """
        # Validate request
        if not self.validate_request(request):
            raise ValueError("Invalid grading request")

        logger.info(f"Grading submission using Voting strategy with {self.num_voters} voters")

        try:
            # Run the async voting process
            # Check if there's already a running event loop (e.g., from FastAPI)
            try:
                loop = asyncio.get_running_loop()
                # If we're already in an async context, we need to use a different approach
                # Create a task and run it in the current loop
                import nest_asyncio
                nest_asyncio.apply()
                result = asyncio.run(
                    self.voting_system.grade(request, self.temperature_range)
                )
            except RuntimeError:
                # No running loop, safe to use asyncio.run()
                result = asyncio.run(
                    self.voting_system.grade(request, self.temperature_range)
                )

            logger.info(f"Voting grading complete. Score: {result.final_score}/{result.total_points}")
            return result

        except Exception as e:
            logger.error(f"Error in Voting grading: {str(e)}")
            raise
