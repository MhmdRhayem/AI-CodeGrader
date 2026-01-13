"""
All prompt templates and examples for LLM-based code grading.
"""

# ============================================================================
# CHAIN-OF-THOUGHT (CoT) PROMPTS
# ============================================================================

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
  "breakdown": [
    {{
      "criterion_name": "Correctness",
      "points_awarded": 4.5,
      "max_points": 5.0,
      "feedback": "Specific feedback..."
    }},
    // ... one object for each criterion
  ],
  "total_score": 9.0,
  "total_possible": 10.0,
  "percentage": 90.0,
  "overall_feedback": "A summary of the student's performance, highlighting strengths and areas for improvement..."
}}

IMPORTANT:
- Each criterion in the breakdown MUST correspond to a criterion in the provided rubric
- The total_score MUST equal the sum of all individual criterion scores
- Points awarded MUST be between 0 and the criterion's max_points
- Feedback must be specific and constructive
- Be fair and objective in your evaluation
"""

# ============================================================================
# FEW-SHOT CHAIN-OF-THOUGHT PROMPTS
# ============================================================================

FEW_SHOT_EXAMPLES = [
    {
        "problem": "Write a function that returns the maximum of two integers.",
        "reference": "int findMax(int a, int b) {{\n    return a > b ? a : b;\n}}",
        "rubric": {
            "total_points": 10,
            "criteria": [
                {"name": "Correctness", "max_points": 5},
                {"name": "Code Quality", "max_points": 3},
                {"name": "Efficiency", "max_points": 2}
            ]
        },
        "student_code": "int findMax(int a, int b) {{\n    return a > b ? a : b;\n}}",
        "reasoning": "## Problem Understanding\nThe task is to write a function that compares two integers and returns the larger one. The reference solution uses the ternary operator which is idiomatic and efficient.\n\n## Reference Solution Analysis\nThe reference uses: `a > b ? a : b` - a clean ternary operator approach that directly returns the maximum in O(1) time with O(1) space.\n\n## Student Code Analysis\nThe student's code is identical to the reference solution. It correctly uses the ternary operator and will work for all integer pairs.\n\n## Criterion-by-Criterion Evaluation\n\n### Correctness (5/5)\nThe implementation is perfectly correct. It handles all cases (positive, negative, equal values) correctly. No edge cases are missed.\n\n### Code Quality (3/3)\nThe code is clean, readable, and uses standard C++ idioms (ternary operator). Variable names are clear and the formatting is consistent.\n\n### Efficiency (2/2)\nOptimal time complexity O(1) and space complexity O(1). No unnecessary operations.\n\n## Overall Assessment\nExcellent solution demonstrating mastery of the problem.",
        "grade": {
            "breakdown": [
                {"criterion_name": "Correctness", "points_awarded": 5.0, "max_points": 5.0, "feedback": "Perfect solution."},
                {"criterion_name": "Code Quality", "points_awarded": 3.0, "max_points": 3.0, "feedback": "Clean code."},
                {"criterion_name": "Efficiency", "points_awarded": 2.0, "max_points": 2.0, "feedback": "Optimal."}
            ],
            "total_score": 10.0,
            "total_possible": 10.0,
            "percentage": 100.0,
            "overall_feedback": "Perfect solution. Your understanding of C++ idioms and ability to write clean, efficient code is excellent."
        }
    },
    {
        "problem": "Implement a function to reverse an array in-place.",
        "reference": "void reverseArray(int arr[], int size) {{\n    int left = 0, right = size - 1;\n    while (left < right) {{\n        int temp = arr[left];\n        arr[left] = arr[right];\n        arr[right] = temp;\n        left++;\n        right--;\n    }}\n}}",
        "rubric": {
            "total_points": 10,
            "criteria": [
                {"name": "Correctness", "max_points": 5},
                {"name": "Code Quality", "max_points": 3},
                {"name": "Efficiency", "max_points": 2}
            ]
        },
        "student_code": "void reverseArray(int arr[], int size) {{\n    int temp[100];\n    for (int i = 0; i < size; i++) {{\n        temp[i] = arr[size - 1 - i];\n    }}\n    for (int i = 0; i < size; i++) {{\n        arr[i] = temp[i];\n    }}\n}}",
        "reasoning": "## Problem Understanding\nThe requirement is to reverse an array IN-PLACE, meaning we should modify the original array without using extra space.\n\n## Reference Solution Analysis\nThe reference uses a two-pointer swap technique:\n- Start with left at 0, right at size-1\n- Swap elements and move pointers toward center\n- This achieves true in-place reversal: O(1) extra space, O(n) time\n\n## Student Code Analysis\nThe student's solution creates a temporary array `temp[100]`, copies reversed elements into it, then copies back to original array. While this works functionally, it:\n1. Uses O(n) extra space (violates in-place requirement)\n2. Uses hardcoded array size (not flexible)\n3. Has more complex logic than needed\n\n## Criterion-by-Criterion Evaluation\n\n### Correctness (3/5)\nThe code works correctly for arrays up to size 100, but:\n- Violates the in-place requirement stated in the problem\n- Hardcoded size 100 means it fails for larger arrays\n- Score: 3/5 (functional but doesn't meet requirements)\n\n### Code Quality (2/3)\nThe logic is understandable but more complex than needed:\n- Extra variable declarations\n- Two separate loops\n- Hardcoded magic number (100)\n- Could be clearer with comments explaining the reversal\n- Score: 2/3 (readable but overcomplicated)\n\n### Efficiency (0/2)\nSpace complexity is O(n) instead of O(1) as required for in-place operations:\n- Temp array allocation uses extra memory\n- Time complexity is O(n) which is acceptable\n- Score: 0/2 (does not meet in-place requirement)\n\n## Overall Assessment\nPartial solution that works functionally but fails to meet the key requirement of reversing in-place. Demonstrates understanding of array manipulation but not optimal algorithm design.",
        "grade": {
            "breakdown": [
                {"criterion_name": "Correctness", "points_awarded": 3.0, "max_points": 5.0, "feedback": "Violates in-place requirement."},
                {"criterion_name": "Code Quality", "points_awarded": 2.0, "max_points": 3.0, "feedback": "Overcomplicated logic."},
                {"criterion_name": "Efficiency", "points_awarded": 0.0, "max_points": 2.0, "feedback": "O(n) space used."}
            ],
            "total_score": 5.0,
            "total_possible": 10.0,
            "percentage": 50.0,
            "overall_feedback": "Your solution works for reversing arrays, but it doesn't meet the in-place requirement. The use of a temporary array violates the constraint. Study two-pointer techniques for in-place array manipulation. Also, avoid hardcoding array sizes."
        }
    },
    {
        "problem": "Implement a Stack class with push, pop, and peek operations.",
        "reference": "class Stack {{\nprivate:\n    int arr[100];\n    int top;\npublic:\n    Stack() : top(-1) {{}}\n    void push(int x) {{ if (top < 99) arr[++top] = x; }}\n    int pop() {{ return top >= 0 ? arr[top--] : -1; }}\n    int peek() {{ return top >= 0 ? arr[top] : -1; }}\n    bool isEmpty() {{ return top == -1; }}\n}};",
        "rubric": {
            "total_points": 10,
            "criteria": [
                {"name": "Correctness", "max_points": 4},
                {"name": "Design", "max_points": 3},
                {"name": "Error Handling", "max_points": 3}
            ]
        },
        "student_code": "class Stack {{}}; // Empty implementation",
        "reasoning": "## Problem Understanding\nNeed to implement a Stack with basic operations: push (add), pop (remove), peek (view top), isEmpty check.\n\n## Reference Solution Analysis\nThe reference provides a working stack using:\n- Private array for storage\n- Top pointer tracking the stack position\n- Basic operations returning -1 for errors\n\n## Student Code Analysis\nThe student provided only an empty class declaration with no implementation.\n\n## Criterion-by-Criterion Evaluation\n\n### Correctness (0/4)\nNo implementation present. Code does not compile or function. Cannot push, pop, or peek.\n\n### Design (0/3)\nNo class members or methods implemented. No consideration for data structure design.\n\n### Error Handling (0/3)\nNo error handling whatsoever. Empty class cannot handle any operations.\n\n## Overall Assessment\nIncomplete submission with no implementation. Requires full rewrite to meet requirements.",
        "grade": {
            "breakdown": [
                {"criterion_name": "Correctness", "points_awarded": 0.0, "max_points": 4.0, "feedback": "No implementation."},
                {"criterion_name": "Design", "points_awarded": 0.0, "max_points": 3.0, "feedback": "Empty class."},
                {"criterion_name": "Error Handling", "points_awarded": 0.0, "max_points": 3.0, "feedback": "None."}
            ],
            "total_score": 0.0,
            "total_possible": 10.0,
            "percentage": 0.0,
            "overall_feedback": "No implementation provided. Please implement all required methods: constructor, push, pop, peek, and isEmpty. Study the reference solution and understand how to manage the stack's internal state."
        }
    }
]

FEW_SHOT_SYSTEM_PROMPT = """You are an expert C++ programming instructor and grader.

You will grade student C++ code submissions using provided examples that show how to evaluate submissions step-by-step.

Study the examples carefully to understand:
1. How to analyze problem requirements vs. submitted code
2. How to compare with reference solutions
3. How to evaluate each rubric criterion with detailed reasoning
4. How to assign fair scores with clear justification

Then apply the same rigorous evaluation approach to the new submission.
"""

FEW_SHOT_USER_PROMPT_TEMPLATE = """# EXAMPLES OF GRADING PROCESS

Below are examples showing how to grade similar submissions. Study these carefully.

{examples}

---

# NOW GRADE THIS NEW SUBMISSION

## Problem Statement
{problem_description}

## Teacher's Reference Solution
{reference_solution}

## Grading Rubric
{rubric_json}

## Student's Submission
{student_code}

---

# GRADING INSTRUCTIONS

Grade this student submission using the same approach shown in the examples above.

## Step 1: Understanding
What does the problem ask for? What are the key requirements?

## Step 2: Reference Analysis
How does the reference solution approach this problem?

## Step 3: Student Code Analysis
What does the student's code do? How does it compare to the reference?

## Step 4: Rubric Evaluation
For EACH criterion, provide detailed analysis explaining:
- How well does the code meet this criterion?
- What are specific strengths or weaknesses?
- What score should be awarded and why?

## Step 5: Final Grade
Sum the criterion scores to get the total.

---

# REQUIRED OUTPUT FORMAT

Provide your response in this JSON format:

{{
  "reasoning": {{
    "understanding": "Your analysis of what the problem asks for...",
    "reference_analysis": "Your analysis of the reference solution...",
    "code_analysis": "Your analysis of the student's code...",
    "criterion_evaluations": [
      {{
        "criterion_name": "First Criterion",
        "analysis": "Detailed analysis of how well the code meets this criterion...",
        "points_awarded": X.X,
        "max_points": Y.Y,
        "feedback": "Specific feedback for this criterion..."
      }},
      // ... one for each criterion in the rubric
    ]
  }},
  "breakdown": [
    {{
      "criterion_name": "First Criterion",
      "points_awarded": X.X,
      "max_points": Y.Y,
      "feedback": "..."
    }},
    // ... one for each criterion
  ],
  "total_score": Z.Z,
  "total_possible": W.W,
  "percentage": P.P,
  "overall_feedback": "Summary of the student's performance..."
}}

IMPORTANT REMINDERS:
- Be thorough and fair in your evaluation, like in the examples
- Provide specific, constructive feedback
- Scores must sum correctly
- Consider all rubric criteria equally
"""


def format_few_shot_examples() -> str:
    """
    Format few-shot examples for inclusion in prompts.

    Returns:
        Formatted examples string
    """
    parts = []

    for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
        parts.append(f"## EXAMPLE {i}\n")
        parts.append(f"**Problem:** {example['problem']}\n")
        parts.append(f"**Reference Solution:**\n```cpp\n{example['reference']}\n```\n")
        parts.append(f"**Student Code:**\n```cpp\n{example['student_code']}\n```\n")
        parts.append(f"**Grading Reasoning:**\n{example['reasoning']}\n")
        parts.append(f"**Assigned Grade:** {example['grade']['total_score']}/{example['grade']['total_possible']}")
        parts.append(f"({example['grade']['percentage']:.0f}%)\n")
        parts.append("---\n\n")

    return "\n".join(parts)


# ============================================================================
# EVALUATOR-OPTIMIZER PROMPTS
# ============================================================================

EVALUATOR_SYSTEM_PROMPT = """You are an expert C++ programming instructor tasked with grading student submissions.

Your role is to:
1. Carefully analyze the problem requirements
2. Compare the student's code with the reference solution
3. Evaluate against the provided rubric
4. Assign fair and accurate scores
5. Provide constructive feedback

Grade thoroughly and fairly. Show your reasoning.
"""

EVALUATOR_GRADE_PROMPT_TEMPLATE = """# Problem Statement
{problem_description}

# Teacher's Reference Solution
{reference_solution}

# Grading Rubric
{rubric_json}

# Student's Submission
{student_code}

---

Please grade this submission thoroughly. For each rubric criterion:
1. Analyze how well the student's code meets that criterion
2. Assign a fair score with detailed justification
3. Provide specific, constructive feedback

Provide your response in this JSON format:

{{
  "reasoning": {{
    "understanding": "What does the problem ask for?",
    "reference_analysis": "How does the reference solution approach this?",
    "code_analysis": "What does the student's code do and how does it compare?",
    "criterion_evaluations": [
      {{
        "criterion_name": "Criterion Name",
        "analysis": "Detailed analysis...",
        "points_awarded": X.X,
        "max_points": Y.Y,
        "feedback": "Specific feedback..."
      }}
    ]
  }},
  "breakdown": [
    {{"criterion_name": "Name", "points_awarded": X.X, "max_points": Y.Y, "feedback": "..."}}
  ],
  "total_score": Z.Z,
  "total_possible": W.W,
  "percentage": P.P,
  "overall_feedback": "Summary..."
}}
"""

OPTIMIZER_SYSTEM_PROMPT = """You are a quality assurance agent reviewing grades for fairness, accuracy, and consistency.

Your role is to:
1. Review the evaluator's grade thoroughly
2. Check if scores match the rubric criteria
3. Verify feedback is specific and helpful
4. Identify any scoring errors or inconsistencies
5. Ensure the grade is fair (not too harsh, not too lenient)
6. Approve or suggest corrections

Be critical but fair. If the grade is accurate, approve it. If there are issues, provide specific corrections.
"""

OPTIMIZER_CRITIQUE_PROMPT_TEMPLATE = """# Problem Statement
{problem_description}

# Teacher's Reference Solution
{reference_solution}

# Grading Rubric
{rubric_json}

# Student's Submission
{student_code}

# Evaluator's Initial Grade
{current_grade}

---

Review this grade for accuracy and fairness. Check:

1. **Rubric Alignment:** Does each score match the rubric criteria?
2. **Accuracy:** Are the criterion analyses correct?
3. **Feedback Quality:** Is the feedback specific and helpful?
4. **Consistency:** Are similar issues weighted consistently?
5. **Fairness:** Is the overall grade fair (proportional to the work quality)?
6. **Edge Cases:** Were any important edge cases missed?

Provide your assessment in this JSON format:

{{
  "approved": true/false,
  "issues_found": [
    {{
      "criterion": "Criterion Name",
      "issue": "What's wrong with this score?",
      "suggested_score": X.X,
      "reasoning": "Why should it be adjusted?"
    }}
  ],
  "overall_assessment": "Is this grade accurate and fair? Why or why not?",
  "confidence": 0.95
}}

If the grade is accurate, set approved to true with empty issues_found.
If there are problems, provide specific corrections with reasoning.
"""

EVALUATOR_REFINE_PROMPT_TEMPLATE = """# Problem Statement
{problem_description}

# Teacher's Reference Solution
{reference_solution}

# Grading Rubric
{rubric_json}

# Student's Submission
{student_code}

# Your Previous Grade
{previous_grade}

# Quality Assurance Feedback
{critique}

---

The quality assurance review found issues with your initial grade. Please refine your evaluation:

1. Reconsider the criterion scores based on the feedback
2. Adjust scores that were flagged as incorrect
3. Ensure your analysis is thorough and fair
4. Provide updated feedback

Provide your refined grade in this JSON format:

{{
  "reasoning": {{
    "understanding": "...",
    "reference_analysis": "...",
    "code_analysis": "...",
    "criterion_evaluations": [
      {{
        "criterion_name": "...",
        "analysis": "Updated analysis addressing the feedback...",
        "points_awarded": X.X,
        "max_points": Y.Y,
        "feedback": "Updated feedback..."
      }}
    ]
  }},
  "breakdown": [
    {{"criterion_name": "...", "points_awarded": X.X, "max_points": Y.Y, "feedback": "..."}}
  ],
  "total_score": Z.Z,
  "total_possible": W.W,
  "percentage": P.P,
  "overall_feedback": "Refined feedback summary..."
}}

Address all issues raised in the quality assurance feedback.
"""
