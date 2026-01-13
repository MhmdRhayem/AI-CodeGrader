"""
Data models for grading output.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class CriterionScore(BaseModel):
    """Score awarded for a single rubric criterion."""

    criterion_name: str = Field(
        ..., description="Name of the criterion"
    )
    points_awarded: float = Field(
        ..., ge=0, description="Points awarded for this criterion"
    )
    max_points: float = Field(
        ..., gt=0, description="Maximum points possible for this criterion"
    )
    feedback: str = Field(
        ..., min_length=5, description="Specific feedback for this criterion"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "criterion_name": "Correctness",
                "points_awarded": 4.5,
                "max_points": 5.0,
                "feedback": "The code handles most cases correctly but has an edge case issue with negative numbers."
            }
        }


class GradingResult(BaseModel):
    """Complete grading result for a student submission."""

    final_score: float = Field(
        ..., ge=0, description="Total points awarded"
    )
    total_points: float = Field(
        ..., gt=0, description="Total possible points"
    )
    percentage: float = Field(
        ..., ge=0, le=100, description="Percentage score (0-100)"
    )

    breakdown: List[CriterionScore] = Field(
        ..., description="Scores for each rubric criterion", min_items=1
    )
    overall_feedback: str = Field(
        ..., min_length=10, description="Overall feedback about the submission"
    )

    # Metadata
    grading_strategy: Literal["cot", "few_shot_cot", "voting", "evaluator_optimizer"] = Field(
        ..., description="Which grading strategy was used"
    )
    model_used: str = Field(
        default="gpt-4o", description="Which LLM model was used"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the grade was computed"
    )
    reasoning_trace: Optional[str] = Field(
        None, description="Step-by-step reasoning (for CoT and Evaluator-Optimizer)"
    )

    def validate_score(self) -> bool:
        """Verify that breakdown scores sum to final score."""
        breakdown_sum = sum(c.points_awarded for c in self.breakdown)
        return abs(breakdown_sum - self.final_score) < 0.01

    def validate_percentage(self) -> bool:
        """Verify that percentage matches final score."""
        expected_percentage = (self.final_score / self.total_points) * 100
        return abs(expected_percentage - self.percentage) < 0.1

    class Config:
        json_schema_extra = {
            "example": {
                "final_score": 9.0,
                "total_points": 10.0,
                "percentage": 90.0,
                "breakdown": [
                    {
                        "criterion_name": "Correctness",
                        "points_awarded": 5.0,
                        "max_points": 5.0,
                        "feedback": "Correct implementation for all test cases."
                    },
                    {
                        "criterion_name": "Code Quality",
                        "points_awarded": 2.5,
                        "max_points": 3.0,
                        "feedback": "Good naming but could use more comments."
                    },
                    {
                        "criterion_name": "Efficiency",
                        "points_awarded": 1.5,
                        "max_points": 2.0,
                        "feedback": "Optimal time complexity but could optimize space usage."
                    }
                ],
                "overall_feedback": "Strong submission with good understanding of the problem. Consider adding more documentation for clarity.",
                "grading_strategy": "cot",
                "model_used": "gpt-4o",
                "timestamp": "2026-01-11T10:30:00"
            }
        }
