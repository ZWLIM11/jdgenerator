"""
content_validators.py
Harness Modules 3-6:
  - Completeness Validator
  - Requirement Relevance Validator
  - Consistency Validator
  - Bias Detection Module
"""

import re


# ── MODULE 3: Completeness ────────────────────────────────────

JD_REQUIRED_FIELDS = ["job_title", "job_summary", "responsibilities", "qualifications", "preferred_qualifications"]
JD_MIN_LENGTHS     = {"responsibilities": 4, "qualifications": 3, "preferred_qualifications": 2}

REQ_REQUIRED_FIELDS = ["must", "addition", "fail"]
REQ_MIN_LENGTHS     = {"must": 3, "addition": 2, "fail": 2}

Q_REQUIRED_FIELDS   = ["question", "question_tag", "difficulty", "target_competency", "expected_scope"]
EA_REQUIRED_FIELDS  = ["question", "ideal_answer", "keywords", "expected_scope", "scoring_criteria"]


def validate_completeness(artifact_type: str, data) -> dict:
    errors = []
    checks_passed = 0
    checks_total  = 0

    def check(condition, msg):
        nonlocal checks_passed, checks_total
        checks_total += 1
        if condition:
            checks_passed += 1
        else:
            errors.append(msg)

    if artifact_type == "jd":
        for field in JD_REQUIRED_FIELDS:
            check(field in data and data[field], f"Missing field: {field}")
        for field, min_len in JD_MIN_LENGTHS.items():
            if field in data and isinstance(data[field], list):
                check(len(data[field]) >= min_len, f"{field} has fewer than {min_len} items")
        if "job_summary" in data:
            words = len(str(data["job_summary"]).split())
            check(words >= 40, f"job_summary too short ({words} words, need 40+)")

    elif artifact_type == "requirements":
        for field in REQ_REQUIRED_FIELDS:
            check(field in data and data[field], f"Missing field: {field}")
        for field, min_len in REQ_MIN_LENGTHS.items():
            if field in data and isinstance(data[field], list):
                check(len(data[field]) >= min_len, f"{field} has fewer than {min_len} items")

    elif artifact_type == "questions":
        items = data if isinstance(data, list) else [data]
        check(len(items) >= 4, f"Only {len(items)} questions generated, need at least 4")
        tags = [q.get("question_tag", "").lower() for q in items]
        check("technical" in tags, "No technical question found")
        check("behavioural" in tags, "No behavioural question found")
        for i, q in enumerate(items):
            for field in Q_REQUIRED_FIELDS:
                check(field in q and q[field], f"Q{i+1} missing: {field}")

    elif artifact_type == "expected_answers":
        items = data if isinstance(data, list) else [data]
        for i, ea in enumerate(items):
            for field in EA_REQUIRED_FIELDS:
                check(field in ea and ea[field], f"EA{i+1} missing: {field}")
            if "scoring_criteria" in ea and isinstance(ea["scoring_criteria"], dict):
                for level in ["poor", "average", "excellent"]:
                    check(level in ea["scoring_criteria"] and ea["scoring_criteria"][level],
                          f"EA{i+1} scoring_criteria missing: {level}")

    score = checks_passed / checks_total if checks_total > 0 else 0.0
    return {
        "valid": score >= 0.75,
        "score": round(score, 2),
        "errors": errors,
        "checks_passed": checks_passed,
        "checks_total": checks_total,
    }


# ── MODULE 4: Requirement Relevance ──────────────────────────

# Skills that do NOT belong in certain role types
ROLE_EXCLUSIONS = {
    "data": ["React", "Angular", "Vue", "HTML", "CSS", "Figma", "WordPress", "iOS", "Android"],
    "frontend": ["TensorFlow", "PyTorch", "scikit-learn", "Spark", "Hadoop", "Kafka", "Airflow"],
    "backend": ["Figma", "Adobe XD", "Sketch", "UI Design", "TensorFlow", "PyTorch"],
    "hr": ["Python", "TensorFlow", "React", "Docker", "Kubernetes", "Kubernetes"],
    "product": ["TensorFlow", "Docker", "Kubernetes", "Deep Learning", "Spark"],
}


def _detect_role_type(job_title: str) -> str:
    title_lower = job_title.lower()
    if any(k in title_lower for k in ["data scientist", "data analyst", "ml engineer", "ai engineer"]):
        return "data"
    if any(k in title_lower for k in ["front-end", "frontend", "ui engineer"]):
        return "frontend"
    if any(k in title_lower for k in ["backend", "back-end", "api engineer"]):
        return "backend"
    if any(k in title_lower for k in ["hr", "human resource", "recruitment"]):
        return "hr"
    if any(k in title_lower for k in ["product manager", "product owner"]):
        return "product"
    return "general"


def validate_relevance(job_title: str, requirements: dict, jd: dict) -> dict:
    errors = []
    role_type = _detect_role_type(job_title)
    exclusions = ROLE_EXCLUSIONS.get(role_type, [])

    all_items = (
        requirements.get("must", []) +
        requirements.get("addition", []) +
        jd.get("qualifications", []) +
        jd.get("responsibilities", [])
    )

    flagged = []
    for item in all_items:
        for excl in exclusions:
            if excl.lower() in item.lower():
                flagged.append(f"'{excl}' in: {item[:60]}")

    if flagged:
        errors.extend(flagged)

    score = max(0.0, 1.0 - (len(flagged) * 0.15))
    return {
        "valid": len(flagged) == 0,
        "score": round(score, 2),
        "errors": errors,
        "flagged_items": flagged,
        "role_type_detected": role_type,
    }


# ── MODULE 5: Consistency ─────────────────────────────────────

def validate_consistency(requirements: dict, questions: list, expected_answers: list) -> dict:
    errors = []
    checks_passed = 0
    checks_total  = 0

    must_skills = " ".join(requirements.get("must", [])).lower()

    def check(condition, msg):
        nonlocal checks_passed, checks_total
        checks_total += 1
        if condition:
            checks_passed += 1
        else:
            errors.append(msg)

    # Q ↔ EA alignment
    check(len(questions) == len(expected_answers),
          f"Question count ({len(questions)}) ≠ Expected answer count ({len(expected_answers)})")

    for i, (q, ea) in enumerate(zip(questions, expected_answers)):
        q_text  = q.get("question", "").lower()
        ea_q    = ea.get("question", "").lower()

        # Check questions match between q and ea
        q_words = set(q_text.split()[:5])
        ea_words = set(ea_q.split()[:5])
        overlap = len(q_words & ea_words)
        check(overlap >= 2, f"Q{i+1}: question mismatch between questions and expected_answers")

        # EA has scoring criteria
        check(
            "scoring_criteria" in ea and isinstance(ea["scoring_criteria"], dict),
            f"Q{i+1}: missing scoring_criteria in expected_answer"
        )

        # Q has competency
        check(
            q.get("target_competency") and len(q["target_competency"]) > 0,
            f"Q{i+1}: missing target_competency"
        )

    # At least one technical question exists if must has technical skills
    tech_keywords = ["python", "sql", "javascript", "java", "react", "docker", "aws"]
    has_tech_req = any(k in must_skills for k in tech_keywords)
    if has_tech_req:
        q_tags = [q.get("question_tag", "").lower() for q in questions]
        check("technical" in q_tags, "Technical requirements exist but no technical question generated")

    score = checks_passed / checks_total if checks_total > 0 else 0.0
    return {
        "valid": score >= 0.75,
        "score": round(score, 2),
        "errors": errors,
        "checks_passed": checks_passed,
        "checks_total": checks_total,
    }


# ── MODULE 6: Bias Detection ──────────────────────────────────

BIAS_PATTERNS = {
    "age": [
        r"\byoung\b", r"\bfresh graduate only\b", r"\bage \d+", r"\bunder \d+ years old\b",
        r"\brecent graduate only\b", r"\bnative speaker only\b", r"\bmother tongue\b",
    ],
    "gender": [
        r"\bmale\b", r"\bfemale\b", r"\bhe\/she\b", r"\bhe or she\b",
        r"\bgentleman\b", r"\blady\b",
    ],
    "race_religion": [
        r"\bbumi\b", r"\bbumiputera only\b", r"\bchinese only\b",
        r"\bmalay only\b", r"\bindian only\b", r"\bmuslim only\b",
        r"\bnon-muslim\b",
    ],
    "physical": [
        r"\bphysically fit\b", r"\bable-bodied\b", r"\bgood looking\b",
        r"\battractiv\b", r"\bpresentable\b",
    ],
}

BIAS_REPLACEMENTS = {
    "young": "motivated",
    "male candidate": "candidate",
    "female candidate": "candidate",
    "native speaker only": "strong communication skills required",
    "physically fit": "able to meet physical job requirements",
}


def detect_bias(jd: dict, requirements: dict) -> dict:
    errors = []
    flagged = []

    all_text_parts = (
        [jd.get("job_summary", ""), jd.get("job_title", "")] +
        jd.get("responsibilities", []) +
        jd.get("qualifications", []) +
        jd.get("preferred_qualifications", []) +
        requirements.get("must", []) +
        requirements.get("addition", []) +
        requirements.get("fail", [])
    )
    full_text = " ".join(all_text_parts).lower()

    for bias_type, patterns in BIAS_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                flagged.append(f"[{bias_type.upper()}] Found: '{matches[0]}' — potential discriminatory language")

    errors.extend(flagged)
    score = max(0.0, 1.0 - (len(flagged) * 0.2))

    return {
        "valid": len(flagged) == 0,
        "score": round(score, 2),
        "errors": errors,
        "flagged_items": flagged,
        "bias_free": len(flagged) == 0,
    }
