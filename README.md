# Recruitment Blueprint Generator

A Streamlit app powered by a local Qwen3 model via Ollama.

## Project Structure

```
recruitment_app/
├── app.py                  ← Streamlit UI (run this)
├── blueprint_generator.py  ← Job Description + Requirements generation
├── question_generator.py   ← Interview Questions + Expected Answers generation
├── evaluation_engine.py    ← Candidate answer scoring engine
├── llm_utils.py            ← Shared Ollama wrapper and JSON extractor
└── requirements.txt
```

## Setup

1. **Install Ollama** – https://ollama.com  
   Pull the model:
   ```bash
   ollama pull qwen3:8b
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Flow

```
Streamlit Form (app.py)
        │
        ▼
build_form()           ← blueprint_generator.py
        │
        ▼
generate_job_description()
        │
        ▼
generate_requirements()
        │
        ▼
generate_questions()   ← question_generator.py
        │
        ▼
generate_expected_answers()
        │
        ▼
Display + Download JSON
```

## Evaluation (separate use)

To score a candidate's actual answers, use `evaluation_engine.py`:

```python
from evaluation_engine import evaluate_answers, build_report

results = evaluate_answers(expected_answers, candidate_answers)
report  = build_report("CAND001", results)
```

`candidate_answers` should be a list of `{"question": ..., "candidate_answer": ...}` dicts.
