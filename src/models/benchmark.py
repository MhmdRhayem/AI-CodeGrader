"""
Data models for benchmark dataset.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime
from .grading_input import GradingRubric


class DifficultyLevel(str, Enum):
    """Difficulty levels for benchmark questions."""

    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class SubmissionType(str, Enum):
    """Classification of student submissions."""

    CORRECT = "correct"
    PARTIAL = "partial"
    INCORRECT = "incorrect"


class StudentSubmission(BaseModel):
    """A single student submission for a question."""

    submission_id: str = Field(
        ..., description="Unique identifier for this submission"
    )
    code: str = Field(
        ..., min_length=1, description="Student's C++ code"
    )
    submission_type: SubmissionType = Field(
        ..., description="Classification: correct, partial, or incorrect"
    )
    human_grade: float = Field(
        ..., ge=0, description="Ground truth score assigned by instructor"
    )
    human_breakdown: Dict[str, float] = Field(
        ..., description="Ground truth score per criterion"
    )
    human_feedback: str = Field(
        ..., description="Instructor's feedback on this submission"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "submission_id": "q1_correct_1",
                "code": "int findMax(int a, int b) { return a > b ? a : b; }",
                "submission_type": "correct",
                "human_grade": 9.5,
                "human_breakdown": {
                    "Correctness": 5.0,
                    "Code Quality": 3.0,
                    "Efficiency": 1.5
                },
                "human_feedback": "Excellent solution with clear logic."
            }
        }


class BenchmarkQuestion(BaseModel):
    """A benchmark question with reference solution and student submissions."""

    question_id: str = Field(
        ..., description="Unique identifier (e.g., 'q1_very_easy')"
    )
    difficulty: DifficultyLevel = Field(
        ..., description="Difficulty level of the question"
    )
    problem_description: str = Field(
        ..., min_length=10, description="Full problem statement"
    )
    reference_solution: str = Field(
        ..., min_length=10, description="Teacher's reference solution"
    )
    rubric: GradingRubric = Field(
        ..., description="Grading rubric for this question"
    )
    student_submissions: List[StudentSubmission] = Field(
        ..., description="Sample student submissions with ground truth grades", min_items=1
    )

    # Metadata
    topic: str = Field(
        ..., description="Topic area (e.g., 'loops', 'recursion')"
    )
    concepts_tested: List[str] = Field(
        ..., description="Key C++ concepts tested"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q1_very_easy",
                "difficulty": "very_easy",
                "problem_description": "Write a function to find the maximum of two integers.",
                "reference_solution": "int max(int a, int b) { return a > b ? a : b; }",
                "rubric": {
                    "criteria": [
                        {"name": "Correctness", "description": "...", "max_points": 5.0},
                        {"name": "Code Quality", "description": "...", "max_points": 3.0},
                        {"name": "Efficiency", "description": "...", "max_points": 2.0}
                    ],
                    "total_points": 10.0
                },
                "student_submissions": [],
                "topic": "conditional_logic",
                "concepts_tested": ["if-else", "ternary operator", "return statements"]
            }
        }


class BenchmarkDataset(BaseModel):
    """Complete benchmark dataset for evaluation."""

    questions: List[BenchmarkQuestion] = Field(
        ..., description="List of benchmark questions", min_items=1
    )
    version: str = Field(
        default="1.0", description="Version of the dataset"
    )
    created_date: datetime = Field(
        default_factory=datetime.utcnow, description="When dataset was created"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "questions": [],
                "version": "1.0",
                "created_date": "2026-01-11T00:00:00"
            }
        }
