"""
Benchmark runner for comparing grading strategies.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from src.llm import OpenAIClient
from src.graders import (
    ChainOfThoughtGrader,
    FewShotCoTGrader,
    VotingGrader,
    EvaluatorOptimizerGrader,
)
from src.models import GradingRequest, BenchmarkDataset, BenchmarkQuestion
from src.evaluation.metrics import BenchmarkComparison, GradingMetrics

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Run all grading strategies on benchmark dataset."""

    def __init__(self, llm_client: OpenAIClient):
        """
        Initialize benchmark runner.

        Args:
            llm_client: OpenAI API client
        """
        self.llm_client = llm_client
        self.graders = {
            "cot": ChainOfThoughtGrader(llm_client),
            "few_shot_cot": FewShotCoTGrader(llm_client),
            "voting": VotingGrader(llm_client, num_voters=3),  # 3 voters for faster benchmark
            "evaluator_optimizer": EvaluatorOptimizerGrader(
                llm_client, max_iterations=2
            ),
        }

    def load_dataset(self, dataset_path: str) -> List[BenchmarkQuestion]:
        """
        Load benchmark dataset from JSON file.

        Args:
            dataset_path: Path to dataset JSON file

        Returns:
            List of BenchmarkQuestion objects
        """
        logger.info(f"Loading benchmark dataset from {dataset_path}")

        with open(dataset_path, "r") as f:
            data = json.load(f)

        questions = []
        for q_data in data.get("questions", []):
            # Load rubric
            rubric_data = q_data.get("rubric", {})
            rubric_criteria = [
                {
                    "name": c["name"],
                    "description": c["description"],
                    "max_points": c["max_points"],
                    "evaluation_guidelines": c.get("evaluation_guidelines"),
                }
                for c in rubric_data.get("criteria", [])
            ]

            # Load submissions with human grades
            submissions_data = q_data.get("student_submissions", [])

            logger.info(
                f"Loaded {q_data['question_id']}: {len(submissions_data)} submissions"
            )
            questions.append(
                {
                    "id": q_data["question_id"],
                    "difficulty": q_data.get("difficulty"),
                    "problem": q_data.get("problem_description"),
                    "reference": q_data.get("reference_solution"),
                    "rubric_criteria": rubric_criteria,
                    "rubric_total": rubric_data.get("total_points"),
                    "submissions": submissions_data,
                }
            )

        logger.info(f"Successfully loaded {len(questions)} questions")
        return questions

    def run_benchmark(
        self, dataset_path: str, output_dir: str = "experiments/runs"
    ) -> str:
        """
        Run all strategies on the benchmark dataset.

        Args:
            dataset_path: Path to benchmark dataset
            output_dir: Directory to save results

        Returns:
            Path to results file
        """
        logger.info("Starting benchmark run...")

        # Load dataset
        questions = self.load_dataset(dataset_path)

        # Initialize comparison tracker
        comparison = BenchmarkComparison()

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Run each strategy on each submission
        results = {strategy: {"grades": [], "times": [], "cost": 0.0}
                  for strategy in self.graders.keys()}

        total_submissions = sum(len(q["submissions"]) for q in questions)
        processed = 0

        for question in questions:
            logger.info(f"\nProcessing {question['id']}")
            logger.info(f"  Submissions: {len(question['submissions'])}")

            for submission_data in question["submissions"]:
                processed += 1
                logger.debug(
                    f"Processing submission {processed}/{total_submissions}: "
                    f"{submission_data.get('submission_id')}"
                )

                # Build grading request
                request = GradingRequest(
                    problem_description=question["problem"],
                    reference_solution=question["reference"],
                    rubric={
                        "criteria": question["rubric_criteria"],
                        "total_points": question["rubric_total"],
                    },
                    student_code=submission_data.get("code"),
                    grading_strategy="cot",  # Will override per strategy
                )

                # Get human grade (ground truth)
                human_grade = submission_data.get("human_grade")
                human_breakdown = submission_data.get("human_breakdown", {})

                # Test each strategy
                for strategy_name, grader in self.graders.items():
                    try:
                        logger.debug(f"Grading with {strategy_name}...")

                        # Measure time and grade
                        start_time = time.time()
                        result = grader.grade(request)
                        elapsed_time = time.time() - start_time

                        # Extract predicted scores
                        predicted_grade = result.final_score
                        predicted_breakdown = {
                            c.criterion_name: c.points_awarded
                            for c in result.breakdown
                        }

                        # Store results
                        results[strategy_name]["grades"].append(
                            (predicted_grade, human_grade)
                        )
                        results[strategy_name]["times"].append(elapsed_time)

                        logger.debug(
                            f"  {strategy_name}: {predicted_grade:.1f} "
                            f"(human: {human_grade:.1f}) "
                            f"in {elapsed_time:.2f}s"
                        )

                    except Exception as e:
                        logger.error(
                            f"Error with {strategy_name} on "
                            f"{submission_data.get('submission_id')}: {str(e)}"
                        )

        # Aggregate results for each strategy
        logger.info("\n" + "=" * 80)
        logger.info("AGGREGATING RESULTS")
        logger.info("=" * 80)

        for strategy_name in self.graders.keys():
            predicted = [g[0] for g in results[strategy_name]["grades"]]
            true_grades = [g[1] for g in results[strategy_name]["grades"]]
            times = results[strategy_name]["times"]

            if predicted:
                avg_time = sum(times) / len(times)
                comparison.add_strategy_results(
                    strategy_name,
                    predicted_grades=predicted,
                    predicted_breakdowns=[],  # Simplified for benchmark
                    true_grades=true_grades,
                    true_breakdowns=[],
                    execution_time=sum(times),
                    api_cost=0.0,  # Would be calculated from API usage
                )

                logger.info(
                    f"{strategy_name}: MAE={
                        GradingMetrics.mean_absolute_error(predicted, true_grades):.3f}, "
                    f"Correlation={
                        GradingMetrics.pearson_correlation(predicted, true_grades):.3f}"
                )

        # Save results
        results_file = output_path / "benchmark_results.json"
        summary = comparison.get_summary()

        with open(results_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"\nResults saved to {results_file}")

        # Print summary
        print("\n" + comparison.print_summary())

        return str(results_file)


def run_benchmark_from_dataset(
    api_key: str, dataset_path: str = "benchmark/dataset.json"
) -> str:
    """
    Convenience function to run benchmark.

    Args:
        api_key: OpenAI API key
        dataset_path: Path to benchmark dataset

    Returns:
        Path to results file
    """
    logger.info("Initializing benchmark runner...")

    client = OpenAIClient(api_key=api_key, model="gpt-4o")
    runner = BenchmarkRunner(client)

    return runner.run_benchmark(dataset_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.evaluation.benchmark_runner <openai_api_key>")
        sys.exit(1)

    api_key = sys.argv[1]
    run_benchmark_from_dataset(api_key)
