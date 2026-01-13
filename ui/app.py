"""
Gradio web interface for C++ Grading Agent.
"""

import gradio as gr
import requests
import json
import logging
from typing import Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration
API_URL = "http://localhost:8000/api/v1/grade"
STRATEGIES_URL = "http://localhost:8000/api/v1/grade/strategies"

# Sample data for demonstration
SAMPLE_PROBLEM = """Write a C++ function that finds and returns the maximum value in an integer array.

Function signature: int findMax(int arr[], int size);

Requirements:
- The function should find the largest element in the array
- Array size is guaranteed to be at least 1
- Handle both positive and negative numbers correctly
"""

SAMPLE_REFERENCE = """int findMax(int arr[], int size) {
    int max = arr[0];
    for (int i = 1; i < size; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}"""

SAMPLE_RUBRIC = """{
  "total_points": 10,
  "criteria": [
    {
      "name": "Correctness",
      "description": "Does the function correctly find and return the maximum value?",
      "max_points": 5.0,
      "evaluation_guidelines": "Test with positive numbers, negative numbers, and mixed values."
    },
    {
      "name": "Code Quality",
      "description": "Is the code clean, readable, and well-structured?",
      "max_points": 3.0,
      "evaluation_guidelines": "Check for clear variable names, consistent formatting, and readable logic."
    },
    {
      "name": "Efficiency",
      "description": "Is the solution optimal in terms of time and space complexity?",
      "max_points": 2.0,
      "evaluation_guidelines": "Time should be O(n), space should be O(1)."
    }
  ]
}"""

SAMPLE_STUDENT = """int findMax(int arr[], int size) {
    if (size <= 0) return -1;

    int max = arr[0];
    for (int i = 1; i < size; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}"""


def grade_submission(
    problem_desc: str,
    reference_sol: str,
    rubric_json: str,
    student_code: str,
    strategy: str,
) -> Tuple[str, str, str]:
    """
    Call the grading API and format results.

    Args:
        problem_desc: Problem description
        reference_sol: Reference solution code
        rubric_json: Rubric as JSON string
        student_code: Student's code
        strategy: Grading strategy to use

    Returns:
        Tuple of (score_display, breakdown_display, feedback_display)
    """
    try:
        # Validate inputs
        if not problem_desc.strip():
            return "❌ Error: Problem description cannot be empty", "", ""
        if not reference_sol.strip():
            return "❌ Error: Reference solution cannot be empty", "", ""
        if not student_code.strip():
            return "❌ Error: Student code cannot be empty", "", ""
        if not rubric_json.strip():
            return "❌ Error: Rubric cannot be empty", "", ""

        # Validate rubric JSON
        try:
            rubric = json.loads(rubric_json)
        except json.JSONDecodeError as e:
            return f"❌ Error: Invalid rubric JSON - {str(e)}\n\nMake sure the rubric is valid JSON with the structure:\n{{'criteria': [...], 'total_points': X}}", "", ""

        # Validate rubric structure
        if not isinstance(rubric, dict):
            return "❌ Error: Rubric must be a JSON object", "", ""
        if "criteria" not in rubric:
            return "❌ Error: Rubric must have a 'criteria' field", "", ""
        if "total_points" not in rubric:
            return "❌ Error: Rubric must have a 'total_points' field", "", ""

        # Validate criteria
        criteria_sum = sum(c.get("max_points", 0) for c in rubric.get("criteria", []))
        if abs(criteria_sum - rubric.get("total_points", 0)) > 0.01:
            return (
                f"❌ Error: Rubric mismatch\n\n"
                f"Sum of criteria points: {criteria_sum:.1f}\n"
                f"Total points: {rubric.get('total_points', 0):.1f}\n\n"
                f"These must be equal. Please fix your rubric.",
                "",
                ""
            )

        # Build request
        payload = {
            "problem_description": problem_desc,
            "reference_solution": reference_sol,
            "rubric": rubric,
            "student_code": student_code,
            "grading_strategy": strategy,
        }

        logger.info(f"Sending grading request with strategy: {strategy}")

        # Call API
        response = requests.post(API_URL, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()

        # Format score display
        final_score = result.get("final_score", 0)
        total_points = result.get("total_points", 0)
        percentage = result.get("percentage", 0)

        score_text = (
            f"### 🎯 Final Score\n\n"
            f"**{final_score:.1f} / {total_points:.1f}** ({percentage:.1f}%)\n\n"
        )

        # Determine score level
        if percentage >= 90:
            score_text += "⭐ Excellent work!"
        elif percentage >= 80:
            score_text += "✅ Good job!"
        elif percentage >= 70:
            score_text += "📚 Satisfactory"
        elif percentage >= 60:
            score_text += "⚠️ Needs improvement"
        else:
            score_text += "❌ Major revisions needed"

        # Format breakdown
        breakdown_text = "### 📊 Score Breakdown\n\n"
        breakdown = result.get("breakdown", [])

        for criterion in breakdown:
            name = criterion.get("criterion_name", "Unknown")
            awarded = criterion.get("points_awarded", 0)
            max_pts = criterion.get("max_points", 0)
            feedback = criterion.get("feedback", "")

            # Calculate percentage for this criterion
            if max_pts > 0:
                criterion_pct = (awarded / max_pts) * 100
            else:
                criterion_pct = 0

            breakdown_text += f"**{name}**\n"
            breakdown_text += f"- Score: {awarded:.1f}/{max_pts:.1f} ({criterion_pct:.0f}%)\n"
            breakdown_text += f"- Feedback: {feedback}\n\n"

        # Format overall feedback
        feedback_text = "### 📝 Overall Feedback\n\n"
        overall_feedback = result.get("overall_feedback", "")
        feedback_text += overall_feedback

        # Add reasoning trace if available
        reasoning_trace = result.get("reasoning_trace")
        if reasoning_trace:
            feedback_text += "\n\n---\n\n### 🤔 Reasoning Trace\n\n"
            feedback_text += f"<details><summary>Click to expand reasoning</summary>\n\n{reasoning_trace}\n\n</details>"

        # Add metadata
        feedback_text += f"\n\n---\n\n*Graded using: **{result.get('grading_strategy', 'unknown')}** strategy*"

        logger.info(
            f"Grading successful. Score: {final_score}/{total_points} ({percentage:.1f}%)"
        )

        return score_text, breakdown_text, feedback_text

    except json.JSONDecodeError as e:
        return f"❌ Error: Invalid rubric JSON - {str(e)}", "", ""
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return (
            "❌ Connection Error\n\n"
            "Cannot connect to grading API at http://localhost:8000\n\n"
            "**Please ensure:**\n"
            "1. FastAPI backend is running: `python -m uvicorn api.main:app --reload`\n"
            "2. Backend is on http://localhost:8000\n"
            "3. OpenAI API key is set in .env file",
            "",
            "",
        )
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        try:
            error_json = e.response.json()
            error_msg = error_json.get("detail", str(e.response.text))
        except:
            error_msg = e.response.text
        return f"❌ API Error\n\n{error_msg}", "", ""
    except requests.exceptions.Timeout:
        logger.warning("Request timeout during grading")
        return (
            "❌ Request Timeout\n\n"
            "Grading took too long (>120 seconds).\n\n"
            "**This can happen with:**\n"
            "- **Voting strategy** (parallel calls are slower)\n"
            "- **Evaluator-Optimizer** (multiple iterations)\n"
            "- **Network latency** (slow OpenAI API response)\n\n"
            "Try using **Chain-of-Thought** or **Few-Shot CoT** for faster results.",
            "",
            "",
        )
    except Exception as e:
        logger.error(f"Error in grading: {str(e)}", exc_info=True)
        return f"❌ Unexpected error: {str(e)}", "", ""


def grade_submission_with_status(
    problem_desc: str,
    reference_sol: str,
    rubric_json: str,
    student_code: str,
    strategy: str,
) -> Tuple[str, str, str, str]:
    """
    Wrapper that shows loading status while grading.

    Returns:
        Tuple of (status, score, breakdown, feedback)
    """
    # Show loading status
    strategy_name = {
        "cot": "Chain-of-Thought",
        "few_shot_cot": "Few-Shot CoT",
        "voting": "Voting (5 parallel graders)",
        "evaluator_optimizer": "Evaluator-Optimizer",
    }.get(strategy, strategy)

    status_msg = f"⏳ **Processing with {strategy_name}...**\n\n_This may take 5-60 seconds depending on the strategy._"

    # Yield loading state immediately
    yield status_msg, "", "", ""

    # Perform grading
    score, breakdown, feedback = grade_submission(
        problem_desc, reference_sol, rubric_json, student_code, strategy
    )

    # Update status based on result
    if score.startswith("❌"):
        status_msg = f"❌ **Grading failed**"
    elif score.startswith("### 🎯"):
        status_msg = f"✅ **Grading complete!** Used {strategy_name}"
    else:
        status_msg = f"⚠️ **Unexpected result**"

    yield status_msg, score, breakdown, feedback


def get_strategy_info() -> str:
    """
    Fetch and display strategy information from the API.

    Returns:
        Formatted strategy information
    """
    try:
        response = requests.get(STRATEGIES_URL, timeout=5)
        response.raise_for_status()
        strategies = response.json()

        info = "## Available Grading Strategies\n\n"
        for key, strategy in strategies.items():
            info += f"### {strategy.get('name', key)}\n"
            info += f"- **Description:** {strategy.get('description', 'N/A')}\n"
            info += f"- **Speed:** {strategy.get('speed', 'N/A')}\n"
            info += f"- **Cost:** {strategy.get('cost', 'N/A')}\n"
            info += f"- **Accuracy:** {strategy.get('accuracy', 'N/A')}\n\n"

        return info

    except Exception as e:
        return f"Could not load strategy information: {str(e)}"


# Create Gradio interface
with gr.Blocks(
    title="C++ Grading Agent",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown(
        """
# 🎓 LLM-Based C++ Grading Agent

Automated grading of C++ programming submissions using state-of-the-art Large Language Models.

Select a grading strategy and submit your problem, reference solution, rubric, and student code.
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📝 Input")

            problem_input = gr.TextArea(
                label="📌 Problem Description",
                placeholder="Enter the C++ problem statement...",
                value=SAMPLE_PROBLEM,
                lines=6,
            )

            reference_input = gr.Code(
                label="✅ Reference Solution (C++)",
                language="cpp",
                value=SAMPLE_REFERENCE,
                lines=8,
            )

            rubric_input = gr.Code(
                label="📋 Grading Rubric (JSON)",
                language="json",
                value=SAMPLE_RUBRIC,
                lines=10,
            )

            student_input = gr.Code(
                label="👨‍💻 Student Submission (C++)",
                language="cpp",
                value=SAMPLE_STUDENT,
                lines=8,
            )

            strategy_input = gr.Radio(
                label="🔧 Grading Strategy",
                choices=[
                    ("Chain-of-Thought (Fast & Cost-Effective)", "cot"),
                    ("Few-Shot CoT (With Examples)", "few_shot_cot"),
                    ("Voting (Multiple Graders)", "voting"),
                    ("Evaluator-Optimizer (Iterative Refinement)", "evaluator_optimizer"),
                ],
                value="cot",
            )

            grade_btn = gr.Button("🚀 Grade Submission", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("### 📊 Results")

            status_output = gr.Markdown(
                label="Status",
                value="*Waiting for submission...*",
            )

            score_output = gr.Markdown(
                label="Final Score",
                value="",
            )

            breakdown_output = gr.Markdown(
                label="Score Breakdown",
            )

            feedback_output = gr.Markdown(
                label="Feedback & Reasoning",
            )

    # Add strategy information section
    with gr.Accordion("📖 Strategy Information", open=False):
        strategy_info = gr.Markdown(get_strategy_info())

    # Connect button to grading function
    grade_btn.click(
        fn=grade_submission_with_status,
        inputs=[problem_input, reference_input, rubric_input, student_input, strategy_input],
        outputs=[status_output, score_output, breakdown_output, feedback_output],
    )

    gr.Markdown(
        """
---

### ℹ️ How to Use

1. **Enter the problem description** - Copy the problem statement you want to grade
2. **Provide the reference solution** - Include the teacher's expected solution
3. **Define the rubric** - Create grading criteria in JSON format
4. **Input student code** - Paste the student's submission
5. **Choose a strategy** - Select a grading technique
6. **Click Grade** - The system will analyze and grade the submission

### 📚 Grading Strategies Explained

- **Chain-of-Thought:** Fast, cost-effective. Good for quick grading.
- **Few-Shot CoT:** Uses grading examples to improve consistency.
- **Voting:** Generates multiple grades and uses consensus. More expensive but more robust.
- **Evaluator-Optimizer:** Iteratively refines grades. Best for critical evaluations.
        """
    )


if __name__ == "__main__":
    logger.info("Starting Gradio UI on http://localhost:7860")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
