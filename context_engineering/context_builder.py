"""
context_builder.py
Context Engineering Layer — combines Role Brief + RAG chunks + examples
into a rich structured prompt context for each LLM generation task.
"""

import json


FEW_SHOT_JD = """
EXAMPLE Job Description Output:
{
  "job_title": "Data Scientist",
  "job_summary": "We are seeking a skilled Data Scientist to join our analytics team...",
  "responsibilities": ["Develop ML models", "Analyse datasets", "Present insights"],
  "qualifications": ["Bachelor in CS/Statistics", "Python proficiency", "SQL knowledge"],
  "preferred_qualifications": ["AWS experience", "Deep Learning knowledge"]
}
"""

FEW_SHOT_REQUIREMENTS = """
EXAMPLE Requirements Output:
{
  "must": ["Python proficiency", "SQL knowledge", "2+ years ML experience"],
  "addition": ["AWS certification", "Kaggle competition experience"],
  "fail": ["No work authorisation", "Cannot demonstrate Python skills"]
}
"""

FEW_SHOT_QUESTION = """
EXAMPLE Question Output:
[{
  "question": "Explain how you would handle class imbalance in a classification problem.",
  "question_tag": "technical",
  "difficulty": "medium",
  "target_competency": ["Technical Skills", "Problem Solving"],
  "expected_scope": ["SMOTE", "class weights", "evaluation metrics"],
  "follow_up_trigger": ["missing_example", "unable_to_explain_metrics"]
}]
"""

GENERATION_CONSTRAINTS = """
CONSTRAINTS:
- Do NOT include skills irrelevant to the role (e.g. no React for Data Scientists)
- Do NOT use discriminatory language (age, gender, race, religion)
- All requirements must be verifiable and measurable
- Output must be valid JSON only — no markdown, no explanation
- First character must be { or [ and last must be } or ]
"""


def build_jd_context(form: dict, rag_context: dict) -> str:
    role_chunks = "\n\n".join(rag_context.get("role_profiles", []))
    skill_chunks = "\n".join(rag_context.get("skill_taxonomy", []))

    return f"""
You are a professional Senior HR Recruitment Specialist with 15 years of experience.

=== ROLE BRIEF ===
{json.dumps(form, indent=2, ensure_ascii=False)}

=== RETRIEVED ROLE KNOWLEDGE ===
{role_chunks or "No similar roles found."}

=== RELEVANT SKILL CONTEXT ===
{skill_chunks or "No skill context found."}

{FEW_SHOT_JD}
{GENERATION_CONSTRAINTS}

Generate a professional Job Description strictly based on the role brief above.
Return JSON only using this structure:
{{
    "job_title": "",
    "job_summary": "",
    "responsibilities": [""],
    "qualifications": [""],
    "preferred_qualifications": [""]
}}

Rules:
- job_summary: 80-120 words, professional tone
- responsibilities: 5-8 items
- qualifications: 5-8 mandatory items
- preferred_qualifications: 3-5 items
- Only include skills that are RELEVANT to this specific role
"""


def build_requirements_context(form: dict, jd: dict, rag_context: dict) -> str:
    comp_chunks = "\n\n".join(rag_context.get("competencies", []))

    return f"""
You are an expert Senior HR Recruitment Specialist.

=== ROLE BRIEF ===
{json.dumps(form, indent=2, ensure_ascii=False)}

=== GENERATED JOB DESCRIPTION ===
{json.dumps(jd, indent=2, ensure_ascii=False)}

=== RETRIEVED COMPETENCY CONTEXT ===
{comp_chunks or "No competency context found."}

{FEW_SHOT_REQUIREMENTS}
{GENERATION_CONSTRAINTS}

Classify recruitment requirements into MUST, ADDITION, and FAIL categories.
Return JSON only:
{{
    "must": [""],
    "addition": [""],
    "fail": [""]
}}

Rules:
- must: 5-10 mandatory, measurable requirements
- addition: 3-6 preferred qualifications that improve ranking
- fail: 3-6 conditions that trigger automatic rejection
- No generic statements like "good communication skills"
- Each item must be specific and verifiable
"""


def build_question_context(requirements: dict, rag_context: dict) -> str:
    comp_chunks = "\n\n".join(rag_context.get("competencies", []))

    return f"""
You are an expert Interview Question Designer.

=== REQUIREMENTS ===
{json.dumps(requirements, indent=2, ensure_ascii=False)}

=== COMPETENCY REFERENCE ===
{comp_chunks or "No competency context found."}

{FEW_SHOT_QUESTION}
{GENERATION_CONSTRAINTS}

Generate EXACTLY 6 competency-based interview questions.
Distribution:
- 1 Core question (difficulty: easy)
- 2 Technical questions (difficulty: 1 easy, 1 medium)
- 2 Behavioural questions (difficulty: 1 medium, 1 hard)
- 1 Situational question (difficulty: hard)

Return JSON array only:
[{{
    "question": "",
    "question_tag": "core|technical|behavioural|situational",
    "difficulty": "easy|medium|hard",
    "target_competency": [],
    "expected_scope": [],
    "follow_up_trigger": []
}}]
"""


def build_eam_context(questions: list, rag_context: dict) -> str:
    comp_chunks = "\n\n".join(rag_context.get("competencies", []))

    return f"""
You are an expert AI Interview Assessment Designer.

=== INTERVIEW QUESTIONS ===
{json.dumps(questions, indent=2, ensure_ascii=False)}

=== COMPETENCY REFERENCE ===
{comp_chunks or "No competency context found."}

{GENERATION_CONSTRAINTS}

Generate Expected Answer Models (EAM) for EACH question.
Return JSON array only:
[{{
    "question": "",
    "question_tag": "",
    "difficulty": "",
    "competency": [],
    "weight": 0,
    "score_breakdown": {{
        "keywords": 30,
        "scope_coverage": 30,
        "relevance": 20,
        "communication": 20
    }},
    "ideal_answer": "",
    "keywords": [],
    "expected_scope": [],
    "follow_up_trigger": [],
    "scoring_criteria": {{
        "poor": "",
        "average": "",
        "excellent": ""
    }}
}}]

Rules:
- weight: easy=5, medium=10, hard=15
- ideal_answer: realistic 80-150 word answer
- keywords: 5-8 important terms
- expected_scope: 3-6 discussion points
- scoring_criteria: concrete descriptions of poor/average/excellent responses
"""
