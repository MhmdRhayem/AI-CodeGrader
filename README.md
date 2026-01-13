# AI-CodeGrader

Automated C++ code grading system using Large Language Models with multiple evaluation strategies.

## Overview

An intelligent grading system that evaluates C++ student submissions against reference solutions using advanced LLM reasoning techniques. Supports 4 grading strategies:

- **Chain-of-Thought (CoT)**: Step-by-step reasoning
- **Few-Shot CoT**: Learning from examples
- **Voting**: Consensus from multiple parallel graders
- **Evaluator-Optimizer**: Two-agent iterative refinement

## Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key

### Installation

```bash
# Clone and setup
git clone https://github.com/MhmdRhayem/AI-CodeGrader.git
cd AI-CodeGrader

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

### Web Interface
```bash
python ui/app.py
```
Open `http://localhost:7860` in your browser.

### API Backend
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Programmatic Usage
```python
from src.llm import OpenAIClient
from src.graders import ChainOfThoughtGrader
from src.models import GradingRequest, GradingRubric, RubricCriterion

# Initialize
client = OpenAIClient(api_key="sk-...")
grader = ChainOfThoughtGrader(client)

# Create rubric
rubric = GradingRubric(
    criteria=[
        RubricCriterion(name="Correctness", max_points=5.0),
        RubricCriterion(name="Code Quality", max_points=3.0),
    ],
    total_points=8.0
)

# Grade submission
request = GradingRequest(
    problem_description="Write a function to find maximum...",
    reference_solution="int max(int a, int b) { return a > b ? a : b; }",
    rubric=rubric,
    student_code="int max(int a, int b) { if(a>b) return a; return b; }",
    grading_strategy="cot"
)

result = grader.grade(request)
print(f"Score: {result.final_score}/{result.total_points} ({result.percentage:.1f}%)")
```

## Project Structure

```
├── config/              # Application settings
├── src/
│   ├── models/         # Pydantic data models
│   ├── llm/            # OpenAI client
│   ├── graders/        # Grading strategies
│   ├── agentic/        # Voting & iterative agents
│   └── evaluation/     # Metrics and benchmarking
├── api/                # FastAPI backend
├── ui/                 # Gradio web interface
├── prompts/            # LLM prompts
└── benchmark/          # Dataset and evaluation
```

## Configuration

Edit `.env` file:

```env
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=gpt-4o
TEMPERATURE=0.3
MAX_TOKENS=2000

API_HOST=0.0.0.0
API_PORT=8000

GRADIO_HOST=0.0.0.0
GRADIO_PORT=7860

VOTING_NUM_VOTERS=5
EVALUATOR_OPTIMIZER_MAX_ITERATIONS=3
```

## API Endpoints

### Single Grading
```
POST /api/v1/grade
```

### Batch Grading
```
POST /api/v1/grade_batch
```

### Available Strategies
```
GET /api/v1/grade/strategies
```

## Grading Strategies

| Strategy | Speed | Accuracy | Cost |
|----------|-------|----------|------|
| CoT | Fast | Good | Low |
| Few-Shot CoT | Fast | Better | Medium |
| Voting | Slower | Best | High |
| Evaluator-Optimizer | Slower | Best | High |

## Evaluation Metrics

- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- Pearson Correlation
- Accuracy within ±5 points

## Requirements

See `requirements.txt` for complete dependencies.

Key packages:
- `openai` - LLM API
- `fastapi` - REST API
- `gradio` - Web UI
- `pydantic` - Data validation