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

## API Endpoints

### Single Grading
```
POST /api/v1/grade
```

### Batch Grading
```
POST /api/v1/grade_batch
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