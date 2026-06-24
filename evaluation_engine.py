"""
evaluation_engine.py
Step 3 – Score candidate answers against expected answers.

Scoring dimensions:
  - keyword_score      (30% weight)
  - scope_score        (30% weight)
  - relevance_score    (20% weight, LLM-based)
  - communication_score(20% weight, heuristic)
"""

from llm_utils import chat


# ─────────────────────────────────────────────
# Individual Scoring Functions
# ─────────────────────────────────────────────

def keyword_score(candidate_answer: str, keywords: list[str]) -> float:
    """Return percentage of expected keywords present in the candidate's answer."""
    if not keywords:
        return 0.0
    text = candidate_answer.lower()
    matched = sum(1 for kw in keywords if kw.lower() in text)
    return round((matched / len(keywords)) * 100, 2)


def scope_score(candidate_answer: str, expected_scope: list[str]) -> float:
    """Return percentage of expected scope items touched by the candidate."""
    if not expected_scope:
        return 0.0
    text = candidate_answer.lower()
    matched = 0
    for item in expected_scope:
        words = item.lower().split()
        if any(word in text for word in words):
            matched += 1
    return round((matched / len(expected_scope)) * 100, 2)


def communication_score(candidate_answer: str) -> float:
    """Simple heuristic: score by answer length (word count)."""
    word_count = len(candidate_answer.split())
    if word_count < 20:
        return 40.0
    elif word_count < 50:
        return 70.0
    else:
        return 90.0


def relevance_score(question: str, candidate_answer: str) -> float:
    """LLM-based relevance score from 0 to 100."""
    prompt = f"""
Question:
{question}

Candidate Answer:
{candidate_answer}

Score how relevant the candidate's answer is to the question, from 0 to 100.
Return ONLY a number. No explanation.
"""
    raw = chat(prompt).strip()
    # Extract the first number found
    import re
    match = re.search(r"\d+(\.\d+)?", raw)
    return float(match.group()) if match else 0.0


# ─────────────────────────────────────────────
# Main Evaluation Function
# ─────────────────────────────────────────────

def evaluate_answers(
    expected_answers: list[dict],
    candidate_answers: list[dict],
) -> list[dict]:
    """
    Pair expected answers with candidate answers and compute all scores.

    Args:
        expected_answers: output of generate_expected_answers()
        candidate_answers: list of {"question": ..., "candidate_answer": ...}

    Returns:
        List of result dicts with per-question scores and final_score.
    """
    results = []

    for expected, candidate in zip(expected_answers, candidate_answers):
        ans = candidate["candidate_answer"]
        breakdown = expected["score_breakdown"]

        kw   = keyword_score(ans, expected["keywords"])
        sc   = scope_score(ans, expected["expected_scope"])
        comm = communication_score(ans)
        rel  = relevance_score(expected["question"], ans)

        final = (
            kw   * breakdown["keywords"]       / 100 +
            sc   * breakdown["scope_coverage"] / 100 +
            rel  * breakdown["relevance"]       / 100 +
            comm * breakdown["communication"]   / 100
        )

        results.append({
            "question":            expected["question"],
            "question_tag":        expected.get("question_tag", ""),
            "difficulty":          expected.get("difficulty", ""),
            "keyword_score":       kw,
            "scope_score":         sc,
            "relevance_score":     rel,
            "communication_score": comm,
            "final_score":         round(final, 2),
        })

    return results


# ─────────────────────────────────────────────
# Overall Report Builder
# ─────────────────────────────────────────────

def build_report(candidate_id: str, results: list[dict]) -> dict:
    """Compute overall score and hiring recommendation."""
    if not results:
        return {}

    overall = round(sum(r["final_score"] for r in results) / len(results), 2)

    if overall >= 85:
        recommendation = "Strong Hire"
    elif overall >= 70:
        recommendation = "Shortlist"
    elif overall >= 50:
        recommendation = "Consider"
    else:
        recommendation = "Reject"

    return {
        "candidate_id":    candidate_id,
        "overall_score":   overall,
        "recommendation":  recommendation,
        "question_scores": results,
    }
