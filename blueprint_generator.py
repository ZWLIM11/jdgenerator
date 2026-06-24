"""
blueprint_generator.py
Step 1 & 2 — JD + Requirements with RAG + Context Engineering + Harness Validation.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from llm_utils import chat
from rag.retriever import retrieve_full_context
from context_engineering.context_builder import build_jd_context, build_requirements_context
from harness.harness_engine import harness_generate


def build_form(
    job_title, department, location, salary, degree,
    relevant_courses, min_years, preferred_years,
    core_skills, additional_requirements, auto_fail_conditions,
    technical_priority, communication_priority, leadership_priority,
    company_context,
) -> dict:
    return {
        "job_title": job_title, "department": department,
        "location": location, "salary": salary,
        "education": {"degree": degree, "relevant_courses": relevant_courses},
        "experience": {"minimum_years": min_years, "preferred_years": preferred_years},
        "core_skills": core_skills,
        "additional_requirements": additional_requirements,
        "auto_fail_conditions": auto_fail_conditions,
        "competency_priorities": {
            "technical": technical_priority,
            "communication": communication_priority,
            "leadership": leadership_priority,
        },
        "company_context": company_context,
    }


def generate_job_description(form: dict) -> dict:
    rag_context = retrieve_full_context(
        job_title=form["job_title"],
        department=form.get("department", ""),
        skills=form.get("core_skills", []),
    )

    def _generate(feedback=None):
        base = build_jd_context(form, rag_context)
        return chat(f"{base}\n\n{feedback}" if feedback else base)

    result = harness_generate(
        generate_fn=_generate,
        validate_kwargs={"job_title": form["job_title"], "jd": {}},
        artifact_type="jd",
        label="Job Description",
    )
    return result["data"] or {}


def generate_requirements(form: dict, jd: dict) -> dict:
    rag_context = retrieve_full_context(
        job_title=form["job_title"],
        department=form.get("department", ""),
        skills=form.get("core_skills", []),
    )

    def _generate(feedback=None):
        base = build_requirements_context(form, jd, rag_context)
        return chat(f"{base}\n\n{feedback}" if feedback else base)

    result = harness_generate(
        generate_fn=_generate,
        validate_kwargs={"job_title": form["job_title"], "jd": jd},
        artifact_type="requirements",
        label="Requirements",
    )
    return result["data"] or {}
