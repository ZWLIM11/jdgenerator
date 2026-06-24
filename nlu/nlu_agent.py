"""
nlu_agent.py
Recruitment NLU Agent — chunks the generated blueprint into ChromaDB,
then answers candidate questions with grounded retrieval.
"""

import json
import uuid
import chromadb
from chromadb.utils import embedding_functions
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from llm_utils import chat

NLU_DB_PATH = os.path.join(os.path.dirname(__file__), "nlu_chroma_db")
EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
COLLECTION_NAME = "blueprint_chunks"


def _get_collection():
    client = chromadb.PersistentClient(path=NLU_DB_PATH)
    return client.get_or_create_collection(COLLECTION_NAME, embedding_function=EMBED_FN)


def chunk_blueprint(blueprint: dict) -> list[dict]:
    """
    Break the blueprint into searchable text chunks.
    Each chunk has: text, chunk_type, metadata
    """
    chunks = []
    jd   = blueprint.get("job_description", {})
    reqs = blueprint.get("requirements", {})
    qs   = blueprint.get("questions", [])
    ea   = blueprint.get("expected_answers", [])
    job_title = blueprint.get("job_title", "this role")

    # Role Overview
    chunks.append({
        "text": f"Role Overview for {job_title}:\n{jd.get('job_summary', '')}",
        "type": "role_overview",
    })

    # Responsibilities
    if jd.get("responsibilities"):
        chunks.append({
            "text": f"Responsibilities for {job_title}:\n" + "\n".join(f"- {r}" for r in jd["responsibilities"]),
            "type": "responsibilities",
        })

    # Qualifications
    if jd.get("qualifications"):
        chunks.append({
            "text": f"Mandatory Qualifications for {job_title}:\n" + "\n".join(f"- {q}" for q in jd["qualifications"]),
            "type": "qualifications",
        })

    if jd.get("preferred_qualifications"):
        chunks.append({
            "text": f"Preferred Qualifications for {job_title}:\n" + "\n".join(f"- {q}" for q in jd["preferred_qualifications"]),
            "type": "preferred_qualifications",
        })

    # Requirements
    if reqs.get("must"):
        chunks.append({
            "text": f"Must-Have Requirements for {job_title}:\n" + "\n".join(f"- {r}" for r in reqs["must"]),
            "type": "must_requirements",
        })

    if reqs.get("addition"):
        chunks.append({
            "text": f"Nice-to-Have Requirements for {job_title}:\n" + "\n".join(f"- {r}" for r in reqs["addition"]),
            "type": "additional_requirements",
        })

    if reqs.get("fail"):
        chunks.append({
            "text": f"Auto-Fail Conditions for {job_title} (automatic rejection):\n" + "\n".join(f"- {r}" for r in reqs["fail"]),
            "type": "fail_conditions",
        })

    # Interview process
    if qs:
        q_summary = f"The interview for {job_title} consists of {len(qs)} questions covering: "
        tags = list({q.get("question_tag", "") for q in qs})
        q_summary += ", ".join(t for t in tags if t) + " topics."
        chunks.append({"text": q_summary, "type": "interview_process"})

    # Scoring info
    if ea:
        weights = [item.get("weight", 0) for item in ea]
        total_w = sum(weights)
        chunks.append({
            "text": f"Interview scoring for {job_title}: Total weight = {total_w} points across {len(ea)} questions. "
                    f"Score breakdown per question: Keywords 30%, Scope Coverage 30%, Relevance 20%, Communication 20%.",
            "type": "scoring_info",
        })

    # Employment info
    etype   = blueprint.get("employment_type", "")
    urgency = blueprint.get("urgency", "")
    location = blueprint.get("location", "")
    salary  = blueprint.get("salary", "")

    info_parts = [f"Position: {job_title}"]
    if etype:   info_parts.append(f"Employment Type: {etype}")
    if location: info_parts.append(f"Location: {location}")
    if salary:  info_parts.append(f"Salary Range: {salary}")
    if urgency: info_parts.append(f"Hiring Urgency: {urgency}")

    chunks.append({"text": " | ".join(info_parts), "type": "employment_info"})

    return chunks


def load_blueprint_to_nlu(blueprint: dict) -> int:
    """
    Chunk the blueprint and upsert into ChromaDB NLU collection.
    Returns number of chunks loaded.
    """
    col = _get_collection()

    # Clear old chunks for a fresh blueprint
    try:
        existing = col.get()
        if existing["ids"]:
            col.delete(ids=existing["ids"])
    except Exception:
        pass

    chunks = chunk_blueprint(blueprint)
    docs, ids, metas = [], [], []

    for i, chunk in enumerate(chunks):
        docs.append(chunk["text"])
        ids.append(f"chunk_{i}_{uuid.uuid4().hex[:6]}")
        metas.append({"chunk_type": chunk["type"]})

    if docs:
        col.upsert(documents=docs, ids=ids, metadatas=metas)

    return len(docs)


def answer_candidate_question(question: str, n_results: int = 3) -> str:
    """
    Retrieve relevant blueprint chunks and generate a grounded answer.
    """
    col = _get_collection()

    try:
        results = col.query(query_texts=[question], n_results=n_results)
        chunks  = results["documents"][0] if results["documents"] else []
    except Exception as e:
        return f"Unable to retrieve information: {e}"

    if not chunks:
        return "I don't have enough information about this role to answer that question."

    context = "\n\n".join(chunks)

    prompt = f"""You are a professional HR assistant answering a candidate's question about a job opening.

Use ONLY the recruitment information provided below to answer. Do not make up information.
If the answer is not in the provided information, say "I don't have that specific information — please contact the HR team directly."

=== RECRUITMENT INFORMATION ===
{context}

=== CANDIDATE QUESTION ===
{question}

=== YOUR ANSWER ===
Provide a clear, helpful, and professional answer based strictly on the recruitment information above.
"""
    return chat(prompt)


def is_blueprint_loaded() -> bool:
    """Check if a blueprint has been loaded into the NLU collection."""
    try:
        col = _get_collection()
        result = col.get()
        return len(result["ids"]) > 0
    except Exception:
        return False
