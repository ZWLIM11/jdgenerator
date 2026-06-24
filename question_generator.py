"""
question_generator.py
Step 3 & 4 — Questions + EAM with RAG + Harness.
EAM fix: generate ONE question at a time to avoid token cutoff.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from llm_utils import chat, _strip_think_tags
from rag.retriever import retrieve_full_context
from context_engineering.context_builder import build_question_context
from harness.harness_engine import harness_generate
from harness.json_validator import validate_json


# ── Interview Questions ───────────────────────────────────────

def generate_questions(requirements: dict, job_title: str = "") -> list:
    rag_context = retrieve_full_context(
        job_title=job_title,
        skills=requirements.get("must", [])[:5],
    )

    def _generate(feedback=None):
        base = build_question_context(requirements, rag_context)
        return chat(f"{base}\n\n{feedback}" if feedback else base)

    result = harness_generate(
        generate_fn=_generate,
        validate_kwargs={"job_title": job_title, "requirements": requirements},
        artifact_type="questions",
        label="Interview Questions",
    )
    return result["data"] or []


# ── EAM — one question per call ───────────────────────────────

def _build_single_eam_prompt(question: dict, comp_chunks: str) -> str:
    """Build a prompt for ONE question's expected answer model."""
    weight = {"easy": 5, "medium": 10, "hard": 15}.get(
        question.get("difficulty", "medium").lower(), 10)

    return f"""You are an expert AI Interview Assessment Designer.

Generate an Expected Answer Model (EAM) for this single interview question.

=== QUESTION ===
{json.dumps(question, indent=2, ensure_ascii=False)}

=== COMPETENCY REFERENCE ===
{comp_chunks or "Professional competency standards."}

CRITICAL RULES:
- Return ONLY a single JSON object (not an array)
- First character must be {{ and last must be }}
- No markdown, no explanation, no extra text
- ideal_answer must be 60-100 words
- keywords: exactly 5 terms
- expected_scope: exactly 3 points
- follow_up_trigger: exactly 2 triggers
- scoring_criteria poor/average/excellent: each 15-25 words

Return this EXACT structure:
{{
    "question": "{question.get('question','').replace('"', "'")}",
    "question_tag": "{question.get('question_tag','')}",
    "difficulty": "{question.get('difficulty','')}",
    "competency": {json.dumps(question.get('target_competency', []))},
    "weight": {weight},
    "score_breakdown": {{"keywords": 30, "scope_coverage": 30, "relevance": 20, "communication": 20}},
    "ideal_answer": "",
    "keywords": [],
    "expected_scope": [],
    "follow_up_trigger": [],
    "scoring_criteria": {{
        "poor": "",
        "average": "",
        "excellent": ""
    }}
}}"""


def _generate_single_eam(question: dict, comp_chunks: str, max_retries: int = 3) -> dict:
    """Generate and validate EAM for a single question with retries."""
    for attempt in range(1, max_retries + 1):
        prompt = _build_single_eam_prompt(question, comp_chunks)
        raw    = chat(prompt)
        result = validate_json(raw)

        if result["valid"] and isinstance(result["data"], dict):
            data = result["data"]
            # Ensure required fields exist
            data.setdefault("question",        question.get("question", ""))
            data.setdefault("question_tag",    question.get("question_tag", ""))
            data.setdefault("difficulty",      question.get("difficulty", "medium"))
            data.setdefault("competency",      question.get("target_competency", []))
            data.setdefault("weight",          {"easy":5,"medium":10,"hard":15}.get(
                                                question.get("difficulty","medium").lower(), 10))
            data.setdefault("score_breakdown", {"keywords":30,"scope_coverage":30,
                                                "relevance":20,"communication":20})
            data.setdefault("ideal_answer",    "")
            data.setdefault("keywords",        [])
            data.setdefault("expected_scope",  [])
            data.setdefault("follow_up_trigger", [])
            data.setdefault("scoring_criteria", {"poor":"","average":"","excellent":""})
            print(f"  [EAM] Q '{question.get('question','')[:40]}...' — attempt {attempt} PASS ✓")
            return data

        print(f"  [EAM] Q '{question.get('question','')[:40]}...' — attempt {attempt} FAIL: {result['errors']}")

    # Fallback: return minimal valid structure
    print(f"  [EAM] Using fallback for: {question.get('question','')[:50]}")
    return {
        "question":         question.get("question", ""),
        "question_tag":     question.get("question_tag", ""),
        "difficulty":       question.get("difficulty", "medium"),
        "competency":       question.get("target_competency", []),
        "weight":           {"easy":5,"medium":10,"hard":15}.get(
                            question.get("difficulty","medium").lower(), 10),
        "score_breakdown":  {"keywords":30,"scope_coverage":30,"relevance":20,"communication":20},
        "ideal_answer":     "A strong candidate should demonstrate clear understanding of the topic with concrete examples.",
        "keywords":         [],
        "expected_scope":   [],
        "follow_up_trigger": ["missing_example", "unable_to_explain"],
        "scoring_criteria": {
            "poor":      "Cannot demonstrate basic understanding of the topic.",
            "average":   "Shows basic understanding with some relevant examples.",
            "excellent": "Demonstrates deep understanding with specific, well-structured examples.",
        }
    }


def generate_expected_answers(questions: list, job_title: str = "") -> list:
    """
    Generate EAM for each question individually to avoid token cutoff.
    Much more reliable than asking the model for all 6 at once.
    """
    if not questions:
        return []

    rag_context  = retrieve_full_context(job_title=job_title)
    comp_chunks  = "\n\n".join(rag_context.get("competencies", []))
    results      = []

    print(f"[EAM] Generating expected answers for {len(questions)} questions individually...")

    for i, question in enumerate(questions, 1):
        print(f"[EAM] Processing question {i}/{len(questions)}: {question.get('question_tag','')}")
        eam = _generate_single_eam(question, comp_chunks)
        results.append(eam)

    print(f"[EAM] Complete — {len(results)} expected answer models generated.")
    return results
