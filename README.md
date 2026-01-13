# LLM-Based C++ Grading Agent

A proof-of-concept automated grading system for C++ programming exercises using Large Language Models (GPT-4/GPT-4o) with multiple prompting strategies.

## Project Overview

This system evaluates C++ student code submissions against teacher reference solutions using advanced LLM reasoning techniques. It supports multiple grading strategies to compare their effectiveness:

- **Chain-of-Thought (CoT)**: Step-by-step LLM reasoning
- **Few-Shot CoT**: Learning from examples in the prompt
- **Voting/Parallelization**: Multiple LLM graders with consensus
- **Evaluator-Optimizer**: Two-agent iterative refinement

## Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key (for GPT-4/GPT-4o access)

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd "C:\Mhmd\M2 AI and Data Engineering\NLP\Project"
```

2. Create a Python virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the template:
```bash
cp .env.example .env
```

5. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

## Project Structure

```
cpp-grading-agent/
├── config/                    # Configuration and prompts
│   ├── settings.py           # Application settings
│   └── prompts/              # Grading strategy prompts
│
├── src/                       # Source code
│   ├── models/               # Pydantic data models
│   ├── llm/                  # LLM client and utilities
│   ├── graders/              # Grading strategy implementations
│   ├── agentic/              # Agentic workflows
│   ├── evaluation/           # Benchmarking and metrics
│   └── utils/                # Utilities
│
├── api/                       # FastAPI backend
│   ├── main.py              # FastAPI app
│   └── routes/              # API endpoints
│
├── ui/                        # Gradio web interface
│   └── app.py               # Gradio UI
│
├── benchmark/                 # Benchmark dataset
│   └── questions/           # C++ questions with solutions
│
├── tests/                     # Unit and integration tests
│
└── experiments/               # Results and notebooks
```

## Current Status

✅ **Completed (Week 1-Foundation)**
- Project structure and Git setup
- Core Pydantic data models (GradingRequest, GradingResult, Benchmark)
- OpenAI API client with async support
- Prompt builder and response parser utilities
- BaseGrader abstract class
- Chain-of-Thought (CoT) grader implementation

⏳ **In Progress / Next Steps**
- Few-Shot CoT grader implementation
- Voting system (Parallelization) grader
- Evaluator-Optimizer agentic workflow
- Benchmark dataset creation (5 C++ questions)
- FastAPI backend with grading endpoints
- Gradio web interface
- Evaluation metrics and benchmarking

## Data Models

### GradingRequest
Input to the grading system:
- `problem_description`: C++ problem statement
- `reference_solution`: Teacher's reference solution
- `rubric`: Grading criteria with max points
- `student_code`: Student's C++ submission
- `grading_strategy`: Which technique to use

### GradingResult
Output from the grading system:
- `final_score`: Total points awarded
- `percentage`: Grade as percentage
- `breakdown`: Scores for each rubric criterion
- `overall_feedback`: Feedback summary
- `reasoning_trace`: Step-by-step reasoning (optional)
- `grading_strategy`: Which technique was used

### Benchmark Dataset
For evaluation:
- 5 C++ questions (Very Easy → Very Hard)
- Reference solutions
- Grading rubrics
- Sample student submissions (correct/partial/incorrect)
- Human-graded ground truth

## Grading Strategies

### 1. Chain-of-Thought (CoT) - ✅ Implemented
Instructs the LLM to reason step-by-step before grading:
1. Analyze problem requirements
2. Review reference solution
3. Examine student code
4. Evaluate each rubric criterion
5. Calculate final score

### 2. Few-Shot CoT - ⏳ In Development
Provides 2-3 grading examples in the prompt to teach the LLM grading patterns.

### 3. Voting/Parallelization - ⏳ In Development
Generates 5 independent grades in parallel with different temperatures, then:
- Computes median score per criterion
- Aggregates feedback from consensus voters
- Produces final consensus grade

### 4. Evaluator-Optimizer - ⏳ In Development
Two-agent iterative system (max 3 iterations):
1. **Evaluator**: Generates initial grade
2. **Optimizer**: Critiques the grade for fairness and accuracy
3. **Refine**: Evaluator improves based on critique
4. Repeat until convergence or max iterations

## API Endpoints (Future)

```
POST /api/v1/grade
  Input: GradingRequest (JSON)
  Output: GradingResult (JSON)
  Query params: strategy=cot|few_shot_cot|voting|evaluator_optimizer

GET /api/v1/grade/strategies
  Output: Available grading strategies

POST /api/v1/benchmark/run
  Input: Optional filtering parameters
  Output: Benchmark results comparing all strategies
```

## Running the Application (Future)

### Start FastAPI Backend
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Start Gradio UI
```bash
python ui/app.py
```

The UI will be available at `http://localhost:7860`

## Evaluation Metrics

The system compares grading strategies using:
- **MAE** (Mean Absolute Error): Average deviation from human grades
- **RMSE** (Root Mean Squared Error): Penalizes larger errors
- **Pearson Correlation**: Correlation with human grades
- **Accuracy within threshold**: % correct within ±5 points
- **Per-criterion MAE**: Error for each rubric criterion

**Target Performance:**
- MAE < 3 points (on 20-point scale)
- Correlation > 0.85
- Accuracy within 5 points > 80%

## Example Usage (Future)

```python
from src.llm import OpenAIClient
from src.graders import ChainOfThoughtGrader
from src.models import GradingRequest, GradingRubric, RubricCriterion

# Initialize
client = OpenAIClient(api_key="sk-...")
grader = ChainOfThoughtGrader(client)

# Create grading request
rubric = GradingRubric(
    criteria=[
        RubricCriterion(
            name="Correctness",
            description="Does it work?",
            max_points=5.0
        ),
        RubricCriterion(
            name="Code Quality",
            description="Is it clean?",
            max_points=3.0
        )
    ],
    total_points=8.0
)

request = GradingRequest(
    problem_description="Write a function to find the maximum...",
    reference_solution="int max(int a, int b) { return a > b ? a : b; }",
    rubric=rubric,
    student_code="int max(int a, int b) { if(a>b) return a; return b; }",
    grading_strategy="cot"
)

# Grade
result = grader.grade(request)

# Print results
print(f"Score: {result.final_score}/{result.total_points} ({result.percentage:.1f}%)")
for criterion in result.breakdown:
    print(f"  {criterion.criterion_name}: {criterion.points_awarded}/{criterion.max_points}")
print(f"\nFeedback: {result.overall_feedback}")
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_graders.py -v

# Run with coverage
pytest --cov=src tests/
```

## Configuration

Edit `.env` to configure:

```env
# OpenAI
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o
TEMPERATURE=0.3
MAX_TOKENS=2000

# API
API_HOST=0.0.0.0
API_PORT=8000

# Gradio
GRADIO_HOST=0.0.0.0
GRADIO_PORT=7860

# Grading strategies
VOTING_NUM_VOTERS=5
EVALUATOR_OPTIMIZER_MAX_ITERATIONS=3
```

## Project Timeline

**Week 1 (Done):** Foundation & Infrastructure
- ✅ Project setup
- ✅ Core models and LLM client
- ✅ Base grader and CoT implementation

**Week 2:** Grading Strategies
- Few-Shot CoT implementation
- Voting system implementation
- Evaluator-Optimizer implementation

**Week 3:** Web Application
- FastAPI backend
- Gradio frontend
- Evaluation system

**Week 4:** Benchmarking & Presentation
- Run full benchmark
- Analyze results
- Create presentation

## Next Steps

1. **Set up virtual environment**: `python -m venv venv && source venv/Scripts/activate`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Create .env file**: Copy from .env.example and add OpenAI API key
4. **Implement Few-Shot CoT grader** (see plan file for details)
5. **Create benchmark dataset** with 5 C++ questions
6. **Build remaining grading strategies**

## References

- OpenAI API: https://platform.openai.com/docs/api-reference
- FastAPI: https://fastapi.tiangolo.com/
- Gradio: https://www.gradio.app/
- Pydantic: https://docs.pydantic.dev/

## Status & Deliverables

📊 **Deliverables Required:**
1. ✅ Working grading system (in progress)
2. ⏳ Benchmark dataset (5 questions)
3. ⏳ Evaluation results (technique comparison)
4. ⏳ Presentation with live demo
5. ⏳ Complete documentation

## Authors

Built as an M2 NLP project for AI and Data Engineering.

## License

Internal use only.
