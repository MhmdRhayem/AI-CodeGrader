"""
Prompts module for LLM-based C++ grading system.

All prompt templates, examples, and building utilities are defined here.
"""

from prompts.prompts import (
    # Chain-of-Thought Prompts
    COT_SYSTEM_PROMPT,
    COT_USER_PROMPT_TEMPLATE,
    # Few-Shot CoT Prompts
    FEW_SHOT_EXAMPLES,
    FEW_SHOT_SYSTEM_PROMPT,
    FEW_SHOT_USER_PROMPT_TEMPLATE,
    format_few_shot_examples,
    # Evaluator-Optimizer Prompts
    EVALUATOR_SYSTEM_PROMPT,
    EVALUATOR_GRADE_PROMPT_TEMPLATE,
    EVALUATOR_REFINE_PROMPT_TEMPLATE,
    OPTIMIZER_SYSTEM_PROMPT,
    OPTIMIZER_CRITIQUE_PROMPT_TEMPLATE,
)

from prompts.builders import PromptBuilder, ResponseParser

__all__ = [
    # Prompt constants
    "COT_SYSTEM_PROMPT",
    "COT_USER_PROMPT_TEMPLATE",
    "FEW_SHOT_EXAMPLES",
    "FEW_SHOT_SYSTEM_PROMPT",
    "FEW_SHOT_USER_PROMPT_TEMPLATE",
    "format_few_shot_examples",
    "EVALUATOR_SYSTEM_PROMPT",
    "EVALUATOR_GRADE_PROMPT_TEMPLATE",
    "EVALUATOR_REFINE_PROMPT_TEMPLATE",
    "OPTIMIZER_SYSTEM_PROMPT",
    "OPTIMIZER_CRITIQUE_PROMPT_TEMPLATE",
    # Builders
    "PromptBuilder",
    "ResponseParser",
]
