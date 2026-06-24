"""
schema_validator.py
Harness Module 2 — validates parsed JSON against Pydantic schemas.
"""

from pydantic import BaseModel, ValidationError, field_validator
from typing import Optional
import re


# ── Pydantic Schemas ──────────────────────────────────────────

class JobDescriptionSchema(BaseModel):
    job_title: str
    job_summary: str
    responsibilities: list[str]
    qualifications: list[str]
    preferred_qualifications: list[str]

    @field_validator("responsibilities", "qualifications", "preferred_qualifications")
    @classmethod
    def non_empty_list(cls, v):
        if not v:
            raise ValueError("List must not be empty")
        return v


class RequirementsSchema(BaseModel):
    must: list[str]
    addition: list[str]
    fail: list[str]

    @field_validator("must", "addition", "fail")
    @classmethod
    def non_empty_list(cls, v):
        if not v:
            raise ValueError("List must not be empty")
        return v


class InterviewQuestionSchema(BaseModel):
    question: str
    question_tag: str
    difficulty: str
    target_competency: list[str]
    expected_scope: list[str]
    follow_up_trigger: list[str]

    @field_validator("question_tag")
    @classmethod
    def valid_tag(cls, v):
        allowed = {"core", "technical", "behavioural", "situational", "communication", "problem_solving"}
        if v.lower() not in allowed:
            raise ValueError(f"question_tag must be one of {allowed}")
        return v.lower()

    @field_validator("difficulty")
    @classmethod
    def valid_difficulty(cls, v):
        if v.lower() not in {"easy", "medium", "hard"}:
            raise ValueError("difficulty must be easy, medium, or hard")
        return v.lower()


class ScoreBreakdownSchema(BaseModel):
    keywords: int
    scope_coverage: int
    relevance: int
    communication: int


class ScoringCriteriaSchema(BaseModel):
    poor: str
    average: str
    excellent: str


class ExpectedAnswerSchema(BaseModel):
    question: str
    question_tag: str
    difficulty: str
    competency: list[str]
    weight: int
    score_breakdown: ScoreBreakdownSchema
    ideal_answer: str
    keywords: list[str]
    expected_scope: list[str]
    follow_up_trigger: list[str]
    scoring_criteria: ScoringCriteriaSchema


# ── Validator Functions ───────────────────────────────────────

def _validate_single(schema_class, data: dict) -> tuple[bool, list[str]]:
    try:
        schema_class(**data)
        return True, []
    except ValidationError as e:
        return False, [f"{err['loc']}: {err['msg']}" for err in e.errors()]


def validate_schema(artifact_type: str, data) -> dict:
    """
    Validate parsed JSON data against the appropriate Pydantic schema.
    artifact_type: 'jd' | 'requirements' | 'questions' | 'expected_answers'
    """
    errors = []
    valid_count = 0
    total = 1

    if artifact_type == "jd":
        ok, errs = _validate_single(JobDescriptionSchema, data)
        if ok:
            valid_count = 1
        errors.extend(errs)

    elif artifact_type == "requirements":
        ok, errs = _validate_single(RequirementsSchema, data)
        if ok:
            valid_count = 1
        errors.extend(errs)

    elif artifact_type == "questions":
        total = len(data) if isinstance(data, list) else 1
        for i, q in enumerate(data if isinstance(data, list) else [data]):
            ok, errs = _validate_single(InterviewQuestionSchema, q)
            if ok:
                valid_count += 1
            errors.extend([f"Q{i+1}: {e}" for e in errs])

    elif artifact_type == "expected_answers":
        total = len(data) if isinstance(data, list) else 1
        for i, ea in enumerate(data if isinstance(data, list) else [data]):
            ok, errs = _validate_single(ExpectedAnswerSchema, ea)
            if ok:
                valid_count += 1
            errors.extend([f"EA{i+1}: {e}" for e in errs])

    score = valid_count / total if total > 0 else 0.0
    return {
        "valid": score >= 0.8,
        "score": round(score, 2),
        "errors": errors,
        "valid_count": valid_count,
        "total": total,
    }
