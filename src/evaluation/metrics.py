"""
Evaluation metrics for comparing grading strategies.
"""

import logging
from typing import List, Dict, Tuple
from collections import defaultdict

import numpy as np

logger = logging.getLogger(__name__)


class GradingMetrics:
    """Calculate accuracy metrics for grading systems."""

    @staticmethod
    def mean_absolute_error(
        predicted_grades: List[float], true_grades: List[float]
    ) -> float:
        """
        Calculate Mean Absolute Error (MAE).

        Args:
            predicted_grades: Predicted scores
            true_grades: Ground truth scores

        Returns:
            MAE value
        """
        if len(predicted_grades) != len(true_grades):
            raise ValueError("Length mismatch between predicted and true grades")

        if len(predicted_grades) == 0:
            return 0.0

        errors = [abs(p - t) for p, t in zip(predicted_grades, true_grades)]
        return float(np.mean(errors))

    @staticmethod
    def root_mean_squared_error(
        predicted_grades: List[float], true_grades: List[float]
    ) -> float:
        """
        Calculate Root Mean Squared Error (RMSE).

        Penalizes larger errors more heavily than MAE.

        Args:
            predicted_grades: Predicted scores
            true_grades: Ground truth scores

        Returns:
            RMSE value
        """
        if len(predicted_grades) != len(true_grades):
            raise ValueError("Length mismatch between predicted and true grades")

        if len(predicted_grades) == 0:
            return 0.0

        squared_errors = [(p - t) ** 2 for p, t in zip(predicted_grades, true_grades)]
        return float(np.sqrt(np.mean(squared_errors)))

    @staticmethod
    def pearson_correlation(
        predicted_grades: List[float], true_grades: List[float]
    ) -> float:
        """
        Calculate Pearson correlation coefficient.

        Measures how well predicted grades correlate with true grades.

        Args:
            predicted_grades: Predicted scores
            true_grades: Ground truth scores

        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(predicted_grades) != len(true_grades):
            raise ValueError("Length mismatch between predicted and true grades")

        if len(predicted_grades) < 2:
            return 0.0

        try:
            correlation_matrix = np.corrcoef(predicted_grades, true_grades)
            # Get correlation between first and second variable
            return float(correlation_matrix[0, 1])
        except Exception as e:
            logger.warning(f"Could not compute correlation: {str(e)}")
            return 0.0

    @staticmethod
    def accuracy_within_threshold(
        predicted_grades: List[float],
        true_grades: List[float],
        threshold: float = 5.0,
    ) -> float:
        """
        Calculate percentage of predictions within threshold of true grade.

        Args:
            predicted_grades: Predicted scores
            true_grades: Ground truth scores
            threshold: Allowable error margin

        Returns:
            Percentage of accurate predictions (0-100)
        """
        if len(predicted_grades) != len(true_grades):
            raise ValueError("Length mismatch between predicted and true grades")

        if len(predicted_grades) == 0:
            return 0.0

        within_threshold = sum(
            1
            for p, t in zip(predicted_grades, true_grades)
            if abs(p - t) <= threshold
        )
        return (within_threshold / len(predicted_grades)) * 100.0

    @staticmethod
    def criterion_level_accuracy(
        predicted_breakdowns: List[Dict[str, float]],
        true_breakdowns: List[Dict[str, float]],
    ) -> Dict[str, float]:
        """
        Calculate MAE per rubric criterion across all submissions.

        Args:
            predicted_breakdowns: List of dicts mapping criterion names to scores
            true_breakdowns: List of dicts mapping criterion names to true scores

        Returns:
            Dict mapping criterion names to MAE values
        """
        if len(predicted_breakdowns) != len(true_breakdowns):
            raise ValueError(
                "Length mismatch between predicted and true breakdowns"
            )

        criterion_errors = defaultdict(list)

        for pred_breakdown, true_breakdown in zip(
            predicted_breakdowns, true_breakdowns
        ):
            for criterion_name in pred_breakdown:
                if criterion_name in true_breakdown:
                    pred_score = pred_breakdown[criterion_name]
                    true_score = true_breakdown[criterion_name]
                    error = abs(pred_score - true_score)
                    criterion_errors[criterion_name].append(error)

        return {
            criterion: float(np.mean(errors))
            for criterion, errors in criterion_errors.items()
        }

    @staticmethod
    def score_distribution_stats(
        grades: List[float],
    ) -> Dict[str, float]:
        """
        Calculate basic statistics about grade distribution.

        Args:
            grades: List of grades

        Returns:
            Dict with mean, median, std, min, max
        """
        if len(grades) == 0:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

        return {
            "mean": float(np.mean(grades)),
            "median": float(np.median(grades)),
            "std": float(np.std(grades)),
            "min": float(np.min(grades)),
            "max": float(np.max(grades)),
        }


class BenchmarkComparison:
    """Compare multiple grading strategies on a benchmark dataset."""

    def __init__(self):
        """Initialize comparison tracker."""
        self.results = {}

    def add_strategy_results(
        self,
        strategy_name: str,
        predicted_grades: List[float],
        predicted_breakdowns: List[Dict[str, float]],
        true_grades: List[float],
        true_breakdowns: List[Dict[str, float]],
        execution_time: float = 0.0,
        api_cost: float = 0.0,
    ) -> None:
        """
        Add results for a strategy.

        Args:
            strategy_name: Name of grading strategy
            predicted_grades: List of predicted grades
            predicted_breakdowns: List of predicted criterion breakdowns
            true_grades: Ground truth grades
            true_breakdowns: Ground truth breakdowns
            execution_time: Time taken to grade all submissions (seconds)
            api_cost: Cost of API calls (USD)
        """
        metrics = GradingMetrics()

        mae = metrics.mean_absolute_error(predicted_grades, true_grades)
        rmse = metrics.root_mean_squared_error(predicted_grades, true_grades)
        correlation = metrics.pearson_correlation(predicted_grades, true_grades)
        accuracy_5 = metrics.accuracy_within_threshold(
            predicted_grades, true_grades, threshold=5.0
        )
        criterion_mae = metrics.criterion_level_accuracy(
            predicted_breakdowns, true_breakdowns
        )
        pred_stats = metrics.score_distribution_stats(predicted_grades)
        true_stats = metrics.score_distribution_stats(true_grades)

        self.results[strategy_name] = {
            "mae": mae,
            "rmse": rmse,
            "correlation": correlation,
            "accuracy_within_5pts": accuracy_5,
            "criterion_mae": criterion_mae,
            "predicted_distribution": pred_stats,
            "true_distribution": true_stats,
            "execution_time_seconds": execution_time,
            "api_cost_usd": api_cost,
            "num_submissions": len(predicted_grades),
        }

    def get_best_strategy(
        self, metric: str = "mae"
    ) -> Tuple[str, Dict[str, float]]:
        """
        Get the best strategy according to a metric.

        Args:
            metric: Metric to use ('mae', 'rmse', 'correlation', 'accuracy_within_5pts')

        Returns:
            Tuple of (strategy_name, results_dict)
        """
        if not self.results:
            raise ValueError("No results to compare")

        if metric not in [
            "mae",
            "rmse",
            "accuracy_within_5pts",
            "correlation",
        ]:
            raise ValueError(f"Unknown metric: {metric}")

        if metric == "correlation":
            # Higher is better for correlation
            best_strategy = max(
                self.results.items(), key=lambda x: x[1].get(metric, 0)
            )
        else:
            # Lower is better for mae/rmse, higher is better for accuracy
            if metric == "accuracy_within_5pts":
                best_strategy = max(
                    self.results.items(), key=lambda x: x[1].get(metric, 0)
                )
            else:
                best_strategy = min(
                    self.results.items(), key=lambda x: x[1].get(metric, float("inf"))
                )

        return best_strategy[0], best_strategy[1]

    def get_summary(self) -> Dict:
        """
        Get a summary of all results for comparison.

        Returns:
            Dict with summary statistics
        """
        if not self.results:
            return {}

        summary = {
            "techniques_compared": list(self.results.keys()),
            "num_techniques": len(self.results),
            "results": self.results,
        }

        # Find best strategies
        try:
            best_mae = self.get_best_strategy("mae")
            best_correlation = self.get_best_strategy("correlation")
            best_accuracy = self.get_best_strategy("accuracy_within_5pts")

            summary["best_by_mae"] = best_mae[0]
            summary["best_by_correlation"] = best_correlation[0]
            summary["best_by_accuracy"] = best_accuracy[0]

        except ValueError:
            pass

        return summary

    def print_summary(self) -> str:
        """
        Generate a formatted summary of results.

        Returns:
            Formatted summary string
        """
        summary = self.get_summary()
        if not summary:
            return "No results to display"

        lines = []
        lines.append("=" * 80)
        lines.append("GRADING STRATEGY COMPARISON RESULTS")
        lines.append("=" * 80)
        lines.append(
            f"\nCompared {summary['num_techniques']} techniques on "
            f"{next(iter(self.results.values()))['num_submissions']} submissions\n"
        )

        # Detailed results table
        lines.append(f"{'Strategy':<25} {'MAE':<10} {'RMSE':<10} {'Corr':<10} {'Acc@5':<10}")
        lines.append("-" * 65)

        for strategy_name in summary["techniques_compared"]:
            results = self.results[strategy_name]
            lines.append(
                f"{strategy_name:<25} "
                f"{results['mae']:<10.3f} "
                f"{results['rmse']:<10.3f} "
                f"{results['correlation']:<10.3f} "
                f"{results['accuracy_within_5pts']:<10.1f}"
            )

        # Best strategies
        lines.append("\n" + "=" * 80)
        lines.append("BEST STRATEGIES BY METRIC")
        lines.append("=" * 80)
        if "best_by_mae" in summary:
            lines.append(f"Best MAE:        {summary['best_by_mae']}")
        if "best_by_correlation" in summary:
            lines.append(f"Best Correlation: {summary['best_by_correlation']}")
        if "best_by_accuracy" in summary:
            lines.append(f"Best Accuracy:   {summary['best_by_accuracy']}")

        return "\n".join(lines)
