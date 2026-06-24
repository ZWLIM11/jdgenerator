"""
kb_builder.py
Builds and manages the ChromaDB recruitment knowledge base.
Loads: skill_taxonomy, role_profiles, competency_definitions
"""

import json
import os
import chromadb
from chromadb.utils import embedding_functions

DATA_DIR  = os.path.join(os.path.dirname(__file__), "data")
DB_PATH   = os.path.join(os.path.dirname(__file__), "chroma_db")

# Use the built-in sentence-transformers embedding (all-MiniLM-L6-v2)
EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def get_client():
    return chromadb.PersistentClient(path=DB_PATH)


def _load_json(filename):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


def build_knowledge_base(force_rebuild=False):
    """
    Build the ChromaDB knowledge base from JSON files.
    Skips if already built unless force_rebuild=True.
    """
    client = get_client()
    existing = [c.name for c in client.list_collections()]

    if not force_rebuild and all(
        name in existing for name in ["role_profiles", "competencies", "skills"]
    ):
        print("Knowledge base already exists. Skipping rebuild.")
        return

    print("Building recruitment knowledge base...")

    # ── Role Profiles ─────────────────────────────────────────
    role_col = client.get_or_create_collection("role_profiles", embedding_function=EMBED_FN)
    role_col.delete(where={"source": "role_profiles"}) if force_rebuild else None

    roles = _load_json("role_profiles.json")
    docs, ids, metas = [], [], []
    for role in roles:
        # Create a rich text chunk for each role
        text = f"""
Role: {role['role']}
Department: {role['department']}
Industries: {', '.join(role['industry'])}
Core Skills: {', '.join(role['core_skills'])}
Preferred Skills: {', '.join(role['preferred_skills'])}
NOT relevant skills: {', '.join(role['NOT_skills'])}
Responsibilities: {' | '.join(role['responsibilities'])}
Qualifications: {' | '.join(role['qualifications'])}
Competencies: {', '.join(role['competencies'])}
        """.strip()
        docs.append(text)
        ids.append(f"role_{role['role'].replace(' ', '_').lower()}")
        metas.append({"role": role["role"], "department": role["department"], "source": "role_profiles"})

    role_col.upsert(documents=docs, ids=ids, metadatas=metas)
    print(f"  ✓ Loaded {len(docs)} role profiles")

    # ── Competency Definitions ────────────────────────────────
    comp_col = client.get_or_create_collection("competencies", embedding_function=EMBED_FN)

    comps = _load_json("competency_definitions.json")
    docs, ids, metas = [], [], []
    for comp in comps:
        text = f"""
Competency: {comp['name']}
Category: {comp['category']}
Definition: {comp['definition']}
Behavioural Indicators: {' | '.join(comp['behavioural_indicators'])}
Interview Angles: {' | '.join(comp['interview_angles'])}
Poor Signals: {' | '.join(comp['poor_signals'])}
Good Signals: {' | '.join(comp['good_signals'])}
Excellent Signals: {' | '.join(comp['excellent_signals'])}
        """.strip()
        docs.append(text)
        ids.append(f"comp_{comp['name'].replace(' ', '_').lower()}")
        metas.append({"name": comp["name"], "category": comp["category"], "source": "competencies"})

    comp_col.upsert(documents=docs, ids=ids, metadatas=metas)
    print(f"  ✓ Loaded {len(docs)} competency definitions")

    # ── Skill Taxonomy ────────────────────────────────────────
    skill_col = client.get_or_create_collection("skills", embedding_function=EMBED_FN)

    taxonomy = _load_json("skill_taxonomy.json")
    docs, ids, metas = [], [], []
    for category, skills in taxonomy.items():
        for skill_key, aliases in skills.items():
            text = f"Skill: {skill_key} | Category: {category} | Also known as: {', '.join(aliases)}"
            docs.append(text)
            ids.append(f"skill_{category}_{skill_key}")
            metas.append({"skill": skill_key, "category": category, "source": "skills"})

    skill_col.upsert(documents=docs, ids=ids, metadatas=metas)
    print(f"  ✓ Loaded {len(docs)} skill entries")

    print("Knowledge base build complete.")


def get_collection(name: str):
    client = get_client()
    return client.get_collection(name, embedding_function=EMBED_FN)


if __name__ == "__main__":
    build_knowledge_base(force_rebuild=True)
