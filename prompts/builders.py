"""
Prompt building utilities for constructing and parsing LLM prompts.
"""

import json
import re
from typing import Dict, Any
from src.models import GradingRequest, GradingRubric


class PromptBuilder:
    """Build prompts for different grading strategies."""

    @staticmethod
    def format_rubric(rubric: GradingRubric) -> str:
        lines = ["# Grading Rubric\n"]
        lines.append(f"Total Points: {rubric.total_points}\n")
        lines.append("## Criteria:\n")

        for criterion in rubric.criteria:
            lines.append(f"\n### {criterion.name} ({criterion.max_points} points)")
            lines.append(f"Description: {criterion.description}")
            if criterion.evaluation_guidelines:
                lines.append(f"Guidelines: {criterion.evaluation_guidelines}")

        return "\n".join(lines)

    @staticmethod
    def format_rubric_json(rubric: GradingRubric) -> str:
        return json.dumps(
            {
                "total_points": rubric.total_points,
                "criteria": [
                    {
                        "name": c.name,
                        "description": c.description,
                        "max_points": c.max_points,
                        "guidelines": c.evaluation_guidelines,
                    }
                    for c in rubric.criteria
                ],
            },
            indent=2,
        )

    @staticmethod
    def format_code_block(code: str, language: str = "cpp") -> str:
        return f"```{language}\n{code}\n```"

    @staticmethod
    def build_grading_prompt(request: GradingRequest, prompt_template: str) -> str:
        return prompt_template.format(
            problem_description=request.problem_description,
            reference_solution=PromptBuilder.format_code_block(
                request.reference_solution
            ),
            rubric_json=PromptBuilder.format_rubric_json(request.rubric),
            student_code=PromptBuilder.format_code_block(request.student_code),
        )


class ResponseParser:
    """Parse and validate LLM responses."""

    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        # Try direct JSON parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in the text
        brace_count = 0
        start_idx = -1

        for i, char in enumerate(text):
            if char == "{":
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    try:
                        return json.loads(text[start_idx : i + 1])
                    except json.JSONDecodeError:
                        start_idx = -1

        raise ValueError("Could not extract valid JSON from LLM response")

    @staticmethod
    def validate_grading_response(response: Dict[str, Any]) -> bool:
        required_keys = ["breakdown", "overall_feedback", "total_score"]

        if not all(key in response for key in required_keys):
            return False

        if not isinstance(response.get("breakdown"), list):
            return False

        if len(response.get("breakdown", [])) == 0:
            return False

        for criterion in response.get("breakdown", []):
            if not all(
                key in criterion
                for key in ["criterion_name", "points_awarded", "max_points", "feedback"]
            ):
                return False

        return True
