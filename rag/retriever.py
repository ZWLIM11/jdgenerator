"""
retriever.py
RAG retrieval layer — queries ChromaDB to get role-relevant context.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from knowledge_base.kb_builder import get_collection, build_knowledge_base


def _safe_query(collection_name: str, query: str, n: int = 3) -> list[str]:
    try:
        col = get_collection(collection_name)
        results = col.query(query_texts=[query], n_results=n)
        return results["documents"][0] if results["documents"] else []
    except Exception as e:
        print(f"[RAG] Warning: could not query {collection_name}: {e}")
        return []


def retrieve_role_context(job_title: str, department: str = "", n: int = 2) -> list[str]:
    """Retrieve similar role profiles."""
    query = f"{job_title} {department}".strip()
    return _safe_query("role_profiles", query, n)


def retrieve_competencies(skills: list[str], n: int = 4) -> list[str]:
    """Retrieve relevant competency definitions for given skills."""
    query = ", ".join(skills) if skills else "general professional competencies"
    return _safe_query("competencies", query, n)


def retrieve_skills(job_title: str, skills: list[str], n: int = 5) -> list[str]:
    """Retrieve skill taxonomy entries relevant to the role."""
    query = f"{job_title} {' '.join(skills)}"
    return _safe_query("skills", query, n)


def retrieve_full_context(
    job_title: str,
    department: str = "",
    skills: list[str] = None,
) -> dict:
    """
    Main retrieval function — returns all context needed for generation.
    Ensures KB is built before querying.
    """
    build_knowledge_base()  # no-op if already built

    skills = skills or []

    role_docs  = retrieve_role_context(job_title, department, n=2)
    comp_docs  = retrieve_competencies(skills, n=4)
    skill_docs = retrieve_skills(job_title, skills, n=5)

    return {
        "role_profiles":  role_docs,
        "competencies":   comp_docs,
        "skill_taxonomy": skill_docs,
    }
