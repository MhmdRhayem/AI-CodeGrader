"""
Data models for grading input.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class RubricCriterion(BaseModel):
    """A single criterion in a grading rubric."""

    name: str = Field(
        ..., description="Criterion name (e.g., 'Correctness')"
    )
    description: str = Field(
        ..., description="What this criterion evaluates"
    )
    max_points: float = Field(
        ..., gt=0, description="Maximum points for this criterion"
    )
    evaluation_guidelines: Optional[str] = Field(
        None, description="Guidelines for evaluating this criterion"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Correctness",
                "description": "Does the code work correctly for all test cases?",
                "max_points": 8.0,
                "evaluation_guidelines": "Test with edge cases, empty inputs, large inputs"
            }
        }


class GradingRubric(BaseModel):
    """Grading rubric with multiple criteria."""

    criteria: List[RubricCriterion] = Field(
        ..., description="List of grading criteria", min_items=1
    )
    total_points: float = Field(
        ..., gt=0, description="Total possible points"
    )

    def validate_total(self) -> bool:
        """Verify that sum of criteria equals total_points."""
        criteria_sum = sum(c.max_points for c in self.criteria)
        return abs(criteria_sum - self.total_points) < 0.01

    class Config:
        json_schema_extra = {
            "example": {
                "criteria": [
                    {
                        "name": "Correctness",
                        "description": "Does the code work correctly?",
                        "max_points": 8.0
                    },
                    {
                        "name": "Code Quality",
                        "description": "Is the code clean and readable?",
                        "max_points": 2.0
                    }
                ],
                "total_points": 10.0
            }
        }


class GradingRequest(BaseModel):
    """Request for grading a student submission."""

    problem_description: str = Field(
        ..., min_length=10, description="The C++ problem statement"
    )
    reference_solution: str = Field(
        ..., min_length=10, description="Teacher's reference C++ solution"
    )
    rubric: GradingRubric = Field(
        ..., description="Grading rubric with criteria and points"
    )
    student_code: str = Field(
        ..., min_length=1, description="Student's C++ code submission"
    )
    grading_strategy: Literal["cot", "few_shot_cot", "voting", "evaluator_optimizer"] = Field(
        default="cot",
        description="Which grading strategy to use"
    )

    def validate_rubric(self) -> bool:
        """Validate that rubric totals are consistent."""
        return self.rubric.validate_total()

    class Config:
        json_schema_extra = {
            "example": {
                "problem_description": "Write a function to find the maximum of two integers.",
                "reference_solution": "int max(int a, int b) { return a > b ? a : b; }",
                "rubric": {
                    "criteria": [
                        {
                            "name": "Correctness",
                            "description": "Does it return the correct maximum?",
                            "max_points": 5.0
                        },
                        {
                            "name": "Code Quality",
                            "description": "Is the code clean?",
                            "max_points": 3.0
                        },
                        {
                            "name": "Efficiency",
                            "description": "Is the solution optimal?",
                            "max_points": 2.0
                        }
                    ],
                    "total_points": 10.0
                },
                "student_code": "int max(int a, int b) { if (a > b) return a; else return b; }",
                "grading_strategy": "cot"
            }
        }
