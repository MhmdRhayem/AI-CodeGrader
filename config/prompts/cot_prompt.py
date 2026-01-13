"""
Chain-of-Thought (CoT) prompting templates for grading.
"""

# System prompt for CoT grading
COT_SYSTEM_PROMPT = """You are an expert C++ programming instructor and grader with deep knowledge of software engineering best practices.

Your task is to grade student C++ code submissions carefully and fairly using the provided rubric.

You MUST think step-by-step and show your complete reasoning process:
1. First, carefully analyze and summarize the problem requirements
2. Review the reference solution to understand the expected approach and implementation details
3. Examine the student's code thoroughly for correctness, logic, style, and efficiency
4. For each rubric criterion, evaluate how well the student's code meets that criterion with detailed reasoning
5. Finally, calculate the total score by summing the individual criterion scores

Always provide your reasoning BEFORE the final grades. Be fair but rigorous in your evaluation.
"""

# User prompt template for CoT grading
COT_USER_PROMPT_TEMPLATE = """# Problem Statement
{problem_description}

# Teacher's Reference Solution
{reference_solution}

# Grading Rubric
{rubric_json}

# Student's Submission
{student_code}

---

# Grading Instructions

Please grade this student submission step-by-step:

## Step 1: Understanding Phase
Summarize what the problem is asking for. What are the key requirements and constraints?

## Step 2: Reference Solution Analysis
Explain the key aspects of the reference solution. What approach does it use? What are the important implementation details?

## Step 3: Student Code Analysis
Examine the student's code carefully. What does it do? How does it compare to the reference solution? Are there any obvious correctness issues, logic errors, or style problems?

## Step 4: Rubric-by-Rubric Evaluation
For EACH criterion in the rubric, provide detailed analysis:
- Does the student's code meet this criterion?
- What specific strengths or weaknesses does it demonstrate?
- Assign a score with clear justification based on the rubric guidelines

## Step 5: Final Grade Calculation
Sum up the individual criterion scores to get the final grade.

---

# Required Output Format

You MUST provide your response in the following JSON format:

{{
  "reasoning": {{
    "understanding": "Your analysis of what the problem asks for...",
    "reference_analysis": "Your analysis of the reference solution...",
    "code_analysis": "Your analysis of the student's code...",
    "criterion_evaluations": [
      {{
        "criterion_name": "Correctness",
        "analysis": "Detailed analysis of how well the code meets this criterion...",
        "points_awarded": 4.5,
        "max_points": 5.0,
        "feedback": "Specific feedback about this criterion for the student..."
      }},
      // ... one object for each criterion in the rubric
    ]
  }},
  "final_grade": {{
    "breakdown": [
      {{
        "criterion": "Correctness",
        "score": 4.5,
        "max_score": 5.0,
        "feedback": "Specific feedback..."
      }},
      // ... one object for each criterion
    ],
    "total_score": 9.0,
    "total_possible": 10.0,
    "percentage": 90.0,
    "overall_feedback": "A summary of the student's performance, highlighting strengths and areas for improvement..."
  }}
}}

IMPORTANT:
- Each criterion in the breakdown MUST correspond to a criterion in the provided rubric
- The total_score MUST equal the sum of all individual criterion scores
- Points awarded MUST be between 0 and the criterion's max_points
- Feedback must be specific and constructive
- Be fair and objective in your evaluation
"""
