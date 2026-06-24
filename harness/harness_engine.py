"""
harness_engine.py
Harness Engineering Validation Framework — orchestrates all validators,
computes quality score, and triggers auto-regeneration if score < 0.70.
"""

from harness.json_validator    import validate_json
from harness.schema_validator  import validate_schema
from harness.content_validators import (
    validate_completeness,
    validate_relevance,
    validate_consistency,
    detect_bias,
)

# Scoring weights (must sum to 1.0)
WEIGHTS = {
    "json":         0.20,
    "schema":       0.20,
    "completeness": 0.20,
    "relevance":    0.15,
    "consistency":  0.15,
    "bias":         0.10,
}

QUALITY_THRESHOLD = 0.70
MAX_RETRIES = 3


def compute_quality_score(component_scores: dict) -> float:
    return round(sum(WEIGHTS[k] * component_scores.get(k, 0.0) for k in WEIGHTS), 4)


def run_validation(
    artifact_type: str,
    raw_text: str,
    job_title: str = "",
    requirements: dict = None,
    questions: list = None,
    expected_answers: list = None,
    jd: dict = None,
) -> dict:
    """
    Run full validation pipeline on a single generated artifact.

    Returns a report dict with:
      - passed: bool
      - quality_score: float
      - component_scores: dict
      - errors: dict of lists
      - data: parsed and validated artifact
    """
    requirements   = requirements   or {}
    questions      = questions      or []
    expected_answers = expected_answers or []
    jd             = jd             or {}
    errors         = {}

    # Step 1 — JSON Validation
    json_result = validate_json(raw_text)
    if not json_result["valid"]:
        return {
            "passed": False,
            "quality_score": 0.0,
            "component_scores": {"json": 0.0},
            "errors": {"json": json_result["errors"]},
            "data": None,
            "fail_reason": "JSON_INVALID",
        }

    data = json_result["data"]
    component_scores = {"json": json_result["score"]}
    errors["json"] = json_result["errors"]

    # Step 2 — Schema Validation
    schema_result = validate_schema(artifact_type, data)
    component_scores["schema"] = schema_result["score"]
    errors["schema"] = schema_result["errors"]

    # Step 3 — Completeness
    completeness_result = validate_completeness(artifact_type, data)
    component_scores["completeness"] = completeness_result["score"]
    errors["completeness"] = completeness_result["errors"]

    # Step 4 — Relevance (only for jd + requirements)
    if artifact_type in ("jd", "requirements"):
        _jd   = data if artifact_type == "jd" else jd
        _reqs = data if artifact_type == "requirements" else requirements
        rel_result = validate_relevance(job_title, _reqs, _jd)
        component_scores["relevance"] = rel_result["score"]
        errors["relevance"] = rel_result["errors"]
    else:
        component_scores["relevance"] = 1.0
        errors["relevance"] = []

    # Step 5 — Consistency (only for questions + expected_answers)
    if artifact_type == "questions" and expected_answers:
        cons_result = validate_consistency(requirements, data, expected_answers)
        component_scores["consistency"] = cons_result["score"]
        errors["consistency"] = cons_result["errors"]
    elif artifact_type == "expected_answers" and questions:
        cons_result = validate_consistency(requirements, questions, data)
        component_scores["consistency"] = cons_result["score"]
        errors["consistency"] = cons_result["errors"]
    else:
        component_scores["consistency"] = 1.0
        errors["consistency"] = []

    # Step 6 — Bias Detection (only for jd + requirements)
    if artifact_type in ("jd", "requirements"):
        _jd   = data if artifact_type == "jd" else jd
        _reqs = data if artifact_type == "requirements" else requirements
        bias_result = detect_bias(_jd, _reqs)
        component_scores["bias"] = bias_result["score"]
        errors["bias"] = bias_result["errors"]
    else:
        component_scores["bias"] = 1.0
        errors["bias"] = []

    quality_score = compute_quality_score(component_scores)
    passed = quality_score >= QUALITY_THRESHOLD

    return {
        "passed": passed,
        "quality_score": quality_score,
        "component_scores": component_scores,
        "errors": errors,
        "data": data,
        "fail_reason": None if passed else "QUALITY_BELOW_THRESHOLD",
    }


def build_regeneration_feedback(validation_report: dict) -> str:
    """Convert validation errors into a feedback string for prompt refinement."""
    lines = ["The previous output had the following issues that must be fixed:"]
    for module, errs in validation_report["errors"].items():
        if errs:
            lines.append(f"\n[{module.upper()} ERRORS]")
            for e in errs[:5]:  # cap to 5 per module
                lines.append(f"  - {e}")
    lines.append("\nPlease regenerate the output fixing all issues above.")
    lines.append("Return ONLY valid JSON. No markdown. No explanation.")
    return "\n".join(lines)


def harness_generate(
    generate_fn,
    validate_kwargs: dict,
    artifact_type: str,
    label: str = "",
    max_retries: int = MAX_RETRIES,
) -> dict:
    """
    Orchestrator: call generate_fn, validate, auto-regenerate if needed.

    generate_fn: callable(feedback: str | None) -> str (raw LLM output)
    validate_kwargs: extra kwargs passed to run_validation
    Returns: {"data": ..., "report": ..., "attempts": int}
    """
    feedback = None

    for attempt in range(1, max_retries + 1):
        raw = generate_fn(feedback)
        report = run_validation(artifact_type, raw, **validate_kwargs)

        print(f"[Harness] {label} attempt {attempt}/{max_retries} — "
              f"quality={report['quality_score']:.2f} — "
              f"{'PASS ✓' if report['passed'] else 'FAIL ✗'}")

        if report["passed"]:
            return {"data": report["data"], "report": report, "attempts": attempt}

        # Build feedback for next attempt
        feedback = build_regeneration_feedback(report)
        print(f"[Harness] Regenerating... Feedback:\n{feedback[:200]}")

    # Return best effort after max retries
    print(f"[Harness] {label} — max retries reached. Using last output (score={report['quality_score']:.2f})")
    return {"data": report["data"], "report": report, "attempts": max_retries}
