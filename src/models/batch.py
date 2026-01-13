from pydantic import BaseModel, Field
from typing import List, Optional

from .grading_output import GradingResult
from .grading_input import GradingRubric


class BatchSubmission(BaseModel):
    filename: str = Field(..., min_length=1)
    student_code: str = Field(..., min_length=1)


class BatchGradingRequest(BaseModel):
    problem_description: str = Field(..., min_length=1)
    reference_solution: str = Field(..., min_length=1)
    rubric: GradingRubric
    grading_strategy: str = Field(default="cot")
    submissions: List[BatchSubmission] = Field(..., min_items=1)

    def validate_rubric(self) -> bool:
        # Same logic style as GradingRequest
        criteria_sum = sum(c.max_points for c in self.rubric.criteria)
        return abs(criteria_sum - self.rubric.total_points) < 0.01


class BatchItemResult(BaseModel):
    filename: str
    result: Optional[GradingResult] = None
    error: Optional[str] = None


class BatchGradingResult(BaseModel):
    count: int
    ok: int
    results: List[BatchItemResult]
