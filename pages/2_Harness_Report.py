"""
pages/2_Harness_Report.py
Harness Engineering Validation Report page.
Shows quality scores, component breakdowns, and validation details.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(
    page_title="Harness Validation Report",
    page_icon="🛡️",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #FDF6F0; }
.block-container { max-width: 1100px !important; padding-top: 1.8rem !important; }

.hero {
    background: linear-gradient(135deg, #4A3040 0%, #9A7787 65%, #E4AFB0 100%);
    border-radius: 16px; padding: 32px 40px 28px;
    margin-bottom: 24px; color: white;
}
.hero h1 { font-size: 1.7rem; font-weight: 700; margin: 0 0 5px; }
.hero p  { font-size: .9rem; opacity: .8; margin: 0; }
.hero .badge {
    display:inline-block; background:rgba(255,255,255,.18);
    border:1px solid rgba(255,255,255,.3); border-radius:20px;
    padding:3px 13px; font-size:.7rem; font-weight:600;
    letter-spacing:.8px; margin-bottom:10px;
}

.score-card {
    background: white; border-radius: 14px; padding: 20px 22px;
    border: 1px solid #F0E6E0; text-align: center;
    box-shadow: 0 2px 8px rgba(154,119,135,.07);
}
.score-big { font-size: 2.2rem; font-weight: 700; }
.score-label { font-size: .75rem; color: #9A7787; font-weight: 600;
               letter-spacing: .8px; text-transform: uppercase; margin-top: 4px; }

.bar-track { background: #F0E6E0; border-radius: 6px; height: 12px; overflow: hidden; margin: 6px 0; }
.bar-fill  { height: 100%; border-radius: 6px; background: linear-gradient(90deg, #9A7787, #E4AFB0); }
.bar-fill-warn { background: linear-gradient(90deg, #E67E22, #F39C12); }
.bar-fill-fail { background: linear-gradient(90deg, #C0392B, #E74C3C); }

.err-item { background: #FFF0F0; border-left: 3px solid #E4AFB0; border-radius: 0 6px 6px 0;
            padding: 8px 12px; margin: 4px 0; font-size: .82rem; color: #6B3A3A; }
.ok-item  { background: #F0F7F0; border-left: 3px solid #27AE60; border-radius: 0 6px 6px 0;
            padding: 8px 12px; margin: 4px 0; font-size: .82rem; color: #1A6B40; }

.weight-badge {
    display: inline-block; background: #F5EFF2; color: #6B4A5A;
    border-radius: 12px; padding: 2px 10px; font-size: .72rem; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="badge">HARNESS ENGINEERING</div>
  <h1>🛡️ Validation Report</h1>
  <p>Quality scores and validation details for the generated recruitment blueprint.</p>
</div>
""", unsafe_allow_html=True)

# ── Check if blueprint exists ─────────────────────────────────
if "jd" not in st.session_state:
    st.warning("⚠️ No blueprint generated yet. Go to the **Blueprint Generator** page first.")
    st.stop()

# ── Re-run validation on demand ───────────────────────────────
from harness.harness_engine import run_validation
from harness.content_validators import detect_bias, validate_relevance

jd    = st.session_state.get("jd", {})
reqs  = st.session_state.get("requirements", {})
qs    = st.session_state.get("questions", [])
ea    = st.session_state.get("expected_answers", [])
job_title = jd.get("job_title", "")

import json

@st.cache_data(show_spinner=False)
def run_all_validations(_jd, _reqs, _qs, _ea, _job_title):
    results = {}
    results["jd"]   = run_validation("jd",   json.dumps(_jd),   job_title=_job_title, jd=_jd)
    results["reqs"] = run_validation("requirements", json.dumps(_reqs), job_title=_job_title, jd=_jd)
    results["qs"]   = run_validation("questions", json.dumps(_qs), job_title=_job_title,
                                     requirements=_reqs, expected_answers=_ea)
    results["ea"]   = run_validation("expected_answers", json.dumps(_ea), job_title=_job_title,
                                     requirements=_reqs, questions=_qs)
    return results

with st.spinner("Running full harness validation…"):
    reports = run_all_validations(
        tuple(jd.items()), tuple(sorted(reqs.items())),
        tuple(json.dumps(q) for q in qs),
        tuple(json.dumps(e) for e in ea),
        job_title,
    )

WEIGHTS = {"json": 0.20, "schema": 0.20, "completeness": 0.20,
           "relevance": 0.15, "consistency": 0.15, "bias": 0.10}
LABELS  = {"json": "JSON Validity", "schema": "Schema Compliance",
           "completeness": "Completeness", "relevance": "Req. Relevance",
           "consistency": "Consistency", "bias": "Bias Detection"}

def avg_score(reports: dict, component: str) -> float:
    scores = [r["component_scores"].get(component, 1.0) for r in reports.values()]
    return sum(scores) / len(scores) if scores else 0.0

# ── Overall Score Cards ───────────────────────────────────────
st.markdown("### Overall Quality Scores")
cols = st.columns(4)
artifacts = [("jd", "Job Description"), ("reqs", "Requirements"),
             ("qs", "Questions"), ("ea", "Expected Answers")]

for col, (key, label) in zip(cols, artifacts):
    r = reports[key]
    score = r["quality_score"]
    color = "#27AE60" if score >= 0.85 else "#E67E22" if score >= 0.70 else "#C0392B"
    icon  = "✅" if score >= 0.70 else "❌"
    col.markdown(f"""
    <div class="score-card">
        <div class="score-big" style="color:{color};">{score:.0%}</div>
        <div class="score-label">{icon} {label}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")

# Overall average
all_scores = [r["quality_score"] for r in reports.values()]
overall = sum(all_scores) / len(all_scores)
overall_color = "#27AE60" if overall >= 0.85 else "#E67E22" if overall >= 0.70 else "#C0392B"
st.markdown(f"""
<div style="background:white;border-radius:14px;padding:20px 24px;border:1px solid #F0E6E0;
            display:flex;align-items:center;gap:20px;margin-bottom:20px;">
    <div style="font-size:2.8rem;font-weight:700;color:{overall_color};">{overall:.0%}</div>
    <div>
        <div style="font-size:1rem;font-weight:600;color:#4A3040;">Overall Blueprint Quality</div>
        <div style="font-size:.85rem;color:#9A7787;">Threshold: 70% to pass · Weights: JSON 20%, Schema 20%, Completeness 20%, Relevance 15%, Consistency 15%, Bias 10%</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Component Breakdown ───────────────────────────────────────
st.markdown("### Component Score Breakdown")

for component, label in LABELS.items():
    weight = WEIGHTS[component]
    avg = avg_score(reports, component)
    pct = int(avg * 100)
    bar_class = "bar-fill" if avg >= 0.75 else "bar-fill-warn" if avg >= 0.50 else "bar-fill-fail"
    color = "#27AE60" if avg >= 0.75 else "#E67E22" if avg >= 0.50 else "#C0392B"

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"""
        <div style="margin-bottom:14px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <span style="font-size:.85rem;font-weight:600;color:#4A3040;">{label}</span>
                <span class="weight-badge">Weight: {int(weight*100)}%</span>
            </div>
            <div class="bar-track">
                <div class="{bar_class}" style="width:{pct}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown(f"<div style='text-align:center;padding-top:4px;font-size:1.1rem;font-weight:700;color:{color};'>{pct}%</div>",
                    unsafe_allow_html=True)

# ── Per-Artifact Detail ───────────────────────────────────────
st.markdown("### Detailed Validation Logs")

for key, label in artifacts:
    r = reports[key]
    score = r["quality_score"]
    icon  = "✅" if r["passed"] else "❌"
    with st.expander(f"{icon} {label} — {score:.0%} quality"):
        # Component scores
        comp_cols = st.columns(3)
        for i, (comp, comp_label) in enumerate(LABELS.items()):
            s = r["component_scores"].get(comp, 1.0)
            c = "#27AE60" if s >= 0.75 else "#E67E22" if s >= 0.50 else "#C0392B"
            comp_cols[i % 3].markdown(
                f"<div style='text-align:center;'>"
                f"<div style='font-size:1.3rem;font-weight:700;color:{c};'>{s:.0%}</div>"
                f"<div style='font-size:.72rem;color:#9A7787;'>{comp_label}</div>"
                f"</div>", unsafe_allow_html=True)

        st.markdown("")

        # Errors
        all_errors = [(mod, err) for mod, errs in r["errors"].items() for err in errs if errs]
        if all_errors:
            st.markdown("**⚠️ Validation Issues Found:**")
            for mod, err in all_errors:
                st.markdown(f'<div class="err-item">[ {mod.upper()} ] {err}</div>',
                            unsafe_allow_html=True)
        else:
            st.markdown('<div class="ok-item">✅ No validation issues found.</div>',
                        unsafe_allow_html=True)

# ── Bias Report ───────────────────────────────────────────────
st.markdown("### 🔍 Bias Detection Report")
bias_result = detect_bias(jd, reqs)
if bias_result["bias_free"]:
    st.success("✅ No discriminatory language detected in the generated blueprint.")
else:
    st.error(f"⚠️ {len(bias_result['flagged_items'])} potential bias issue(s) found:")
    for item in bias_result["flagged_items"]:
        st.markdown(f'<div class="err-item">{item}</div>', unsafe_allow_html=True)

# ── Relevance Report ──────────────────────────────────────────
st.markdown("### 🎯 Requirement Relevance Report")
rel_result = validate_relevance(job_title, reqs, jd)
st.markdown(f"**Role type detected:** `{rel_result['role_type_detected']}`")
if rel_result["valid"]:
    st.success("✅ All requirements are relevant to the role type. No mismatched skills detected.")
else:
    st.warning(f"⚠️ {len(rel_result['flagged_items'])} potentially irrelevant item(s) detected:")
    for item in rel_result["flagged_items"]:
        st.markdown(f'<div class="err-item">{item}</div>', unsafe_allow_html=True)

if st.button("🔄 Re-run Validation", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
