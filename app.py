"""
app.py – Recruitment Blueprint Generator (v5)
Fixes: input text contrast, dropdown/selectbox invisible text,
       mixed HTML div bugs, empty boxes fully removed,
       all labels clearly visible, consistent warm palette.
"""

import json
import streamlit as st
from blueprint_generator import build_form, generate_job_description, generate_requirements
from question_generator import generate_questions, generate_expected_answers
from nlu.nlu_agent import load_blueprint_to_nlu

st.set_page_config(
    page_title="Recruitment Blueprint Generator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── App background ── */
.stApp { background: #F9F4F1; }
.block-container {
    padding-top: 1.8rem !important;
    padding-bottom: 4rem !important;
    max-width: 1180px !important;
}

/* ── Fix ALL input / textarea / selectbox text contrast ── */
/* Text inside inputs must be dark on light background */
input[type="text"],
input[type="number"],
textarea {
    color: #2C1A24 !important;
    background-color: #FFFFFF !important;
    border: 1.5px solid #D4A8B0 !important;
    border-radius: 8px !important;
}
input[type="text"]:focus,
input[type="number"]:focus,
textarea:focus {
    border-color: #9A7787 !important;
    box-shadow: 0 0 0 2px rgba(154,119,135,0.15) !important;
}

/* Selectbox — fix invisible text in dropdown */
[data-baseweb="select"] > div,
[data-baseweb="select"] input,
[data-baseweb="select"] [class*="ValueContainer"],
[data-baseweb="select"] [class*="singleValue"],
[data-baseweb="select"] [class*="placeholder"] {
    color: #2C1A24 !important;
    background-color: #FFFFFF !important;
}
[data-baseweb="select"] > div {
    border: 1.5px solid #D4A8B0 !important;
    border-radius: 8px !important;
    background-color: #FFFFFF !important;
}
/* Dropdown menu options */
[data-baseweb="popover"] li,
[data-baseweb="menu"] li,
[role="option"] {
    color: #2C1A24 !important;
    background-color: #FFFFFF !important;
}
[role="option"]:hover,
[aria-selected="true"][role="option"] {
    background-color: #F5EFF2 !important;
    color: #4A3040 !important;
}

/* Number input buttons */
[data-testid="stNumberInput"] button { color: #9A7787 !important; }

/* Labels — always dark and readable */
label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span {
    color: #4A3040 !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
}

/* Caption text */
[data-testid="stCaptionContainer"] p { color: #7A5568 !important; font-size: 0.8rem !important; }

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #3D1F2D 0%, #9A7787 60%, #E4AFB0 100%);
    border-radius: 16px;
    padding: 36px 44px 32px;
    margin-bottom: 24px;
    color: white;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "";
    position: absolute; top: -50px; right: -50px;
    width: 200px; height: 200px;
    background: rgba(254,215,191,0.12); border-radius: 50%;
}
.hero h1 { font-size: 1.9rem; font-weight: 700; margin: 0 0 6px; letter-spacing: -0.4px; }
.hero p  { font-size: 0.9rem; opacity: 0.85; margin: 0; line-height: 1.5; }
.badge {
    display: inline-block;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 3px 14px;
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: 1px; margin-bottom: 10px;
}

/* ── Section headers (pure text, no broken div wrappers) ── */
.sec-header {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 1.4px; text-transform: uppercase;
    color: #9A7787; margin-bottom: 14px;
    display: flex; align-items: center; gap: 10px;
    padding-bottom: 8px;
    border-bottom: 1.5px solid #EDD5D0;
}

/* ── Sidebar cards ── */
.side-card {
    background: white;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
    border: 1px solid #EDD5D0;
    box-shadow: 0 2px 6px rgba(154,119,135,0.08);
}
.side-title {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 1.2px; text-transform: uppercase;
    color: #9A7787; margin-bottom: 12px;
}
.check-item { font-size: 0.82rem; margin-bottom: 7px; }
.step-row { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; }
.step-num {
    width: 26px; height: 26px; border-radius: 50%;
    background: #E4AFB0; color: white;
    font-size: 0.72rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.step-label { font-size: 0.82rem; color: #5A3A4A; font-weight: 500; }

/* ── Form section dividers ── */
.form-section {
    background: white;
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 18px;
    border: 1px solid #EDD5D0;
    box-shadow: 0 2px 8px rgba(154,119,135,0.06);
}

/* ── Competency bars ── */
.comp-row { margin-bottom: 10px; }
.comp-label { font-size: 0.82rem; font-weight: 600; color: #4A3040; margin-bottom: 4px; }
.comp-track { background: #EDD5D0; border-radius: 6px; height: 10px; overflow: hidden; }
.comp-fill { height: 100%; border-radius: 6px;
             background: linear-gradient(90deg, #9A7787, #E4AFB0); }

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3D1F2D, #9A7787) !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 1rem !important;
    padding: 13px 28px !important; color: white !important;
    letter-spacing: 0.3px !important;
}
.stButton > button[kind="primary"]:hover { opacity: 0.88 !important; }
.stButton > button:not([kind="primary"]) {
    border: 1.5px solid #D4A8B0 !important;
    color: #6B4A5A !important;
    border-radius: 8px !important;
    background: white !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: #F5EFF2 !important;
}

/* ── Slider thumb and track ── */
[data-testid="stSlider"] [role="slider"] { background: #9A7787 !important; }
[data-testid="stSliderTrackFill"] { background: #9A7787 !important; }
/* Slider value label */
[data-testid="stSlider"] p { color: #4A3040 !important; font-weight: 600 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #F0E8EC; border-radius: 10px; padding: 4px; gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; font-weight: 500;
    font-size: 0.875rem; color: #6B4A5A !important;
}
.stTabs [aria-selected="true"] {
    background: white !important; color: #3D1F2D !important;
    box-shadow: 0 1px 4px rgba(154,119,135,0.18) !important;
}

/* ── Chips ── */
.chip { display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 0.78rem; font-weight: 600; margin: 3px; }
.chip-plum  { background: #F0E6EC; color: #4A2A3A; }
.chip-peach { background: #FFF0E6; color: #6B4020; }
.chip-red   { background: #FFE8E8; color: #7A2020; }

/* ── Question cards ── */
.q-card {
    background: #FDF8F6; border-left: 4px solid #9A7787;
    border-radius: 0 10px 10px 0; padding: 16px 18px; margin-bottom: 12px;
}
.q-card.behavioural { border-color: #C4849A; }
.q-card.situational  { border-color: #D4A060; }
.q-card.core         { border-color: #8A90C4; }
.q-meta { font-size: 0.73rem; color: #9A7787; margin-bottom: 6px; font-weight: 500; }
.q-text { font-size: 0.92rem; color: #2C1A24; font-weight: 500; line-height: 1.6; }

/* Difficulty badges */
.score-badge { display: inline-block; padding: 2px 9px; border-radius: 12px;
               font-size: 0.7rem; font-weight: 700; }
.badge-easy   { background: #E8F5E9; color: #1B5E20; }
.badge-medium { background: #FFF3E0; color: #7B4A00; }
.badge-hard   { background: #FFEBEE; color: #7A1A1A; }

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #EDD5D0 !important;
    border-radius: 10px !important;
    background: white !important;
}
[data-testid="stExpander"] summary p {
    color: #4A3040 !important; font-weight: 500 !important;
}

/* ── Download strip ── */
.dl-strip {
    background: linear-gradient(135deg, #3D1F2D, #9A7787);
    border-radius: 14px; padding: 22px 26px; margin-top: 24px;
}
.dl-title {
    color: #FED7BF; font-size: 0.9rem;
    font-weight: 600; margin-bottom: 14px;
}

/* ── Info / success / warning boxes text ── */
[data-testid="stAlert"] p { color: inherit !important; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="badge">AI-POWERED · RAG · HARNESS ENGINEERING</div>
  <h1>🎯 Recruitment Blueprint Generator</h1>
  <p>Fill in the role details below. The system uses RAG retrieval, context engineering,
  and harness validation to generate a complete, bias-free, role-accurate hiring blueprint.</p>
</div>
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────
form_col, side_col = st.columns([3, 1], gap="large")

# ── SIDEBAR ───────────────────────────────────────────────────
with side_col:
    st.markdown("""
    <div class="side-card">
      <div class="side-title">📋 Form Checklist</div>
    """, unsafe_allow_html=True)
    checklist_slot = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="side-card">
      <div class="side-title">⚡ Generation Steps</div>
      <div class="step-row"><div class="step-num">1</div><div class="step-label">Job Description (RAG)</div></div>
      <div class="step-row"><div class="step-num">2</div><div class="step-label">Requirements (Harness)</div></div>
      <div class="step-row"><div class="step-num">3</div><div class="step-label">Interview Questions</div></div>
      <div class="step-row"><div class="step-num">4</div><div class="step-label">Expected Answers (EAM)</div></div>
      <div class="step-row"><div class="step-num">5</div><div class="step-label">NLU Agent Load</div></div>
    </div>
    <div class="side-card">
      <div class="side-title">🛡️ Harness Scoring</div>
      <div style="font-size:0.78rem;color:#5A3A4A;line-height:1.8;">
        JSON Validity &nbsp;&nbsp;&nbsp; 20%<br>
        Schema Check &nbsp;&nbsp;&nbsp; 20%<br>
        Completeness &nbsp;&nbsp;&nbsp;&nbsp; 20%<br>
        Relevance &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 15%<br>
        Consistency &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 15%<br>
        Bias Detection &nbsp;&nbsp; 10%<br>
        <hr style="border-color:#EDD5D0;margin:6px 0;">
        <b>Pass threshold: 70%</b><br>
        Max retries: 3
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── FORM ──────────────────────────────────────────────────────
with form_col:

    # BASIC INFO
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="sec-header">🏢 Basic Information</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        job_title  = c1.text_input("Job Title *", placeholder="e.g. Junior Data Scientist")
        department = c2.text_input("Department",  placeholder="e.g. Data Analytics")
        c3, c4 = st.columns(2)
        location   = c3.text_input("Location", placeholder="e.g. Kuala Lumpur / Remote")
        c4a, c4b = c4.columns(2)
        salary_min = c4a.text_input("Min Salary (RM)", placeholder="4000")
        salary_max = c4b.text_input("Max Salary (RM)", placeholder="6000")
        c5, c6 = st.columns(2)
        employment_type = c5.selectbox("Employment Type",
            ["Full Time", "Part Time", "Contract", "Internship", "Freelance"])
        urgency = c6.selectbox("Hiring Urgency",
            ["Normal", "Urgent (< 2 weeks)", "Planned (> 1 month)"])
        salary = f"RM {salary_min} – RM {salary_max}" if (salary_min or salary_max) else "Not specified"
        st.markdown('</div>', unsafe_allow_html=True)

    # EDUCATION
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="sec-header">🎓 Education</div>', unsafe_allow_html=True)
        e1, e2 = st.columns(2)
        degree = e1.selectbox("Minimum Degree Required",
            ["High School / SPM", "Diploma", "Bachelor Degree", "Master Degree", "PhD"], index=2)
        field_of_study = e1.text_input("Field of Study", placeholder="e.g. Computer Science, Statistics")
        relevant_courses_input = e2.text_area(
            "Relevant Courses (one per line)",
            placeholder="e.g.\nMachine Learning\nDatabase Systems\nStatistics",
            height=112)
        relevant_courses = [c.strip() for c in relevant_courses_input.splitlines() if c.strip()]
        st.markdown('</div>', unsafe_allow_html=True)

    # EXPERIENCE
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="sec-header">💼 Experience</div>', unsafe_allow_html=True)
        x1, x2, x3 = st.columns(3)
        min_years       = x1.number_input("Minimum Years",   min_value=0, max_value=20, value=1)
        preferred_years = x2.number_input("Preferred Years", min_value=0, max_value=20, value=3)
        industry_exp    = x3.text_input("Industry Background", placeholder="e.g. Fintech")
        st.markdown('</div>', unsafe_allow_html=True)

    # CORE SKILLS
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="sec-header">⚙️ Core Skills</div>', unsafe_allow_html=True)
        if "core_skills" not in st.session_state:
            st.session_state.core_skills = [""]
        to_remove_sk = None
        for i, skill in enumerate(st.session_state.core_skills):
            sa, sb, sc = st.columns([5, 2, 1])
            st.session_state.core_skills[i] = sa.text_input(
                f"Skill {i+1}", value=skill, key=f"sk_{i}", placeholder="e.g. Python")
            sb.selectbox("Level", ["Required", "Nice to Have"],
                key=f"skl_{i}", label_visibility="collapsed")
            if sc.button("✕", key=f"rsk_{i}") and len(st.session_state.core_skills) > 1:
                to_remove_sk = i
        if to_remove_sk is not None:
            st.session_state.core_skills.pop(to_remove_sk); st.rerun()
        if st.button("＋ Add Skill", key="btn_add_skill"):
            st.session_state.core_skills.append(""); st.rerun()
        core_skills = [s.strip() for s in st.session_state.core_skills if s.strip()]
        st.markdown('</div>', unsafe_allow_html=True)

    # ADDITIONAL REQUIREMENTS
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="sec-header">📌 Additional Requirements</div>', unsafe_allow_html=True)
        if "extra_reqs" not in st.session_state:
            st.session_state.extra_reqs = [""]
        to_remove_rq = None
        for i, req in enumerate(st.session_state.extra_reqs):
            ra, rb = st.columns([6, 1])
            st.session_state.extra_reqs[i] = ra.text_input(
                f"Requirement {i+1}", value=req, key=f"rq_{i}",
                placeholder="e.g. Willing to travel occasionally")
            if rb.button("✕", key=f"rrq_{i}") and len(st.session_state.extra_reqs) > 1:
                to_remove_rq = i
        if to_remove_rq is not None:
            st.session_state.extra_reqs.pop(to_remove_rq); st.rerun()
        if st.button("＋ Add Requirement", key="btn_add_req"):
            st.session_state.extra_reqs.append(""); st.rerun()
        additional_requirements = [r.strip() for r in st.session_state.extra_reqs if r.strip()]
        st.markdown('</div>', unsafe_allow_html=True)

    # AUTO FAIL CONDITIONS
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="sec-header">🚫 Auto-Fail Conditions</div>', unsafe_allow_html=True)
        st.caption("Candidates matching any condition below are automatically rejected.")
        if "fail_conditions" not in st.session_state:
            st.session_state.fail_conditions = [
                "Unable to demonstrate required technical skills during interview",
                "Academic qualification below minimum requirement",
            ]
        to_remove_fc = None
        for i, cond in enumerate(st.session_state.fail_conditions):
            fa, fb = st.columns([6, 1])
            st.session_state.fail_conditions[i] = fa.text_input(
                f"Condition {i+1}", value=cond, key=f"fc_{i}")
            if fb.button("✕", key=f"rfc_{i}") and len(st.session_state.fail_conditions) > 1:
                to_remove_fc = i
        if to_remove_fc is not None:
            st.session_state.fail_conditions.pop(to_remove_fc); st.rerun()
        if st.button("＋ Add Condition", key="btn_add_fail"):
            st.session_state.fail_conditions.append(""); st.rerun()
        auto_fail_conditions = [c.strip() for c in st.session_state.fail_conditions if c.strip()]
        st.markdown('</div>', unsafe_allow_html=True)

    # COMPETENCY PRIORITIES
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="sec-header">📊 Competency Priorities</div>', unsafe_allow_html=True)
        st.caption("Rate how critical each competency is (1 = low · 10 = essential).")
        p1, p2 = st.columns(2)
        technical_priority       = p1.slider("Technical Skills",  1, 10, 7)
        communication_priority   = p1.slider("Communication",     1, 10, 5)
        leadership_priority      = p1.slider("Leadership",        1, 10, 3)
        problem_solving_priority = p2.slider("Problem Solving",   1, 10, 6)
        teamwork_priority        = p2.slider("Teamwork",          1, 10, 5)
        adaptability_priority    = p2.slider("Adaptability",      1, 10, 4)

        comp_data = {
            "Technical": technical_priority, "Communication": communication_priority,
            "Leadership": leadership_priority, "Problem Solving": problem_solving_priority,
            "Teamwork": teamwork_priority, "Adaptability": adaptability_priority,
        }
        bars_html = "".join(f"""
        <div class="comp-row">
            <div class="comp-label">{n} — {v}/10</div>
            <div class="comp-track"><div class="comp-fill" style="width:{v*10}%"></div></div>
        </div>""" for n, v in comp_data.items())
        st.markdown(bars_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # COMPANY CONTEXT
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="sec-header">🏗️ Company Context</div>', unsafe_allow_html=True)
        st.caption("Culture, team size, tech stack — anything that shapes what a great hire looks like.")
        company_context = st.text_area(
            "Company Context", label_visibility="collapsed",
            placeholder="e.g. Series B fintech startup in KL, 80 staff. Data team of 6 using Python + AWS. "
                        "We value self-starters who communicate insights to non-technical stakeholders...",
            height=130)
        st.markdown('</div>', unsafe_allow_html=True)

    # GENERATE BUTTON
    st.markdown("")
    generate = st.button(
        "🚀  Generate Full Blueprint",
        type="primary",
        use_container_width=True,
        disabled=not job_title.strip(),
    )
    if not job_title.strip():
        st.caption("👆 Enter a Job Title above to enable generation.")

# ── Live checklist update ─────────────────────────────────────
checks = {
    "Job Title":       bool(job_title.strip()),
    "Department":      bool(department.strip()),
    "Location":        bool(location.strip()),
    "Salary":          bool(salary_min or salary_max),
    "Core Skills":     len(core_skills) > 0,
    "Company Context": bool(company_context.strip()),
}
checklist_slot.markdown("".join(
    f'<div class="check-item" style="color:{"#3D1F2D" if ok else "#B09090"};">'
    f'{"✅" if ok else "⬜"} {lbl}</div>'
    for lbl, ok in checks.items()
), unsafe_allow_html=True)

# ── Generation pipeline ───────────────────────────────────────
if generate:
    if not job_title.strip():
        st.error("Please enter a Job Title before generating.")
        st.stop()

    form = build_form(
        job_title=job_title, department=department,
        location=location, salary=salary, degree=degree,
        relevant_courses=relevant_courses,
        min_years=int(min_years), preferred_years=int(preferred_years),
        core_skills=core_skills,
        additional_requirements=additional_requirements,
        auto_fail_conditions=auto_fail_conditions,
        technical_priority=technical_priority,
        communication_priority=communication_priority,
        leadership_priority=leadership_priority,
        company_context=company_context,
    )
    for k, v in [("employment_type", employment_type), ("urgency", urgency),
                 ("field_of_study", field_of_study), ("industry_exp", industry_exp),
                 ("location", location), ("salary", salary)]:
        st.session_state[k] = v

    prog = st.progress(0, "Initialising…")

    with st.spinner("Step 1/5 — Writing Job Description (RAG + Harness)…"):
        st.session_state["jd"] = generate_job_description(form)
    prog.progress(20, "✅ Job Description done")

    with st.spinner("Step 2/5 — Classifying Requirements (RAG + Harness)…"):
        st.session_state["requirements"] = generate_requirements(form, st.session_state["jd"])
    prog.progress(40, "✅ Requirements done")

    with st.spinner("Step 3/5 — Generating Interview Questions (Harness)…"):
        st.session_state["questions"] = generate_questions(
            st.session_state["requirements"], job_title=job_title)
    prog.progress(60, "✅ Questions done")

    with st.spinner("Step 4/5 — Building Expected Answer Models (EAM + Harness)…"):
        st.session_state["expected_answers"] = generate_expected_answers(
            st.session_state["questions"], job_title=job_title)
    prog.progress(80, "✅ EAM done")

    with st.spinner("Step 5/5 — Loading blueprint into NLU Agent…"):
        blueprint_for_nlu = {
            "job_title": job_title, "employment_type": employment_type,
            "urgency": urgency, "location": location, "salary": salary,
            "job_description":  st.session_state["jd"],
            "requirements":     st.session_state["requirements"],
            "questions":        st.session_state["questions"],
            "expected_answers": st.session_state["expected_answers"],
        }
        n_chunks = load_blueprint_to_nlu(blueprint_for_nlu)
        st.session_state["nlu_loaded"] = True
        st.session_state["nlu_chunks"] = n_chunks
    prog.progress(100, "✅ All done!")

    st.success(f"✅ Blueprint generated! NLU Agent loaded with **{n_chunks} knowledge chunks**. "
               f"See **Candidate NLU** and **Harness Report** pages in the sidebar.")

# ── Results display ───────────────────────────────────────────
if "jd" in st.session_state:
    jd    = st.session_state["jd"]
    reqs  = st.session_state.get("requirements", {})
    qs    = st.session_state.get("questions", [])
    ea    = st.session_state.get("expected_answers", [])
    etype = st.session_state.get("employment_type", "")
    urg   = st.session_state.get("urgency", "")

    st.markdown("---")

    # Title row
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
        <span style="font-size:1.5rem;font-weight:700;color:#2C1A24;">
            {jd.get('job_title','')}
        </span>
        <span class="chip chip-plum">{etype}</span>
        <span class="chip chip-peach">{urg}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("nlu_loaded"):
        st.info(f"💬 **NLU Agent ready** — {st.session_state.get('nlu_chunks',0)} chunks loaded. "
                f"Use the **Candidate NLU** page in the sidebar to answer candidate questions.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Job Description", "✅ Requirements",
        "❓ Interview Questions", "💡 Scoring Guide"])

    # ── Tab 1: JD ────────────────────────────────────────────
    with tab1:
        st.markdown(
            f'<div style="background:#FDF4F0;border-radius:10px;padding:18px 22px;'
            f'font-size:0.95rem;color:#2C1A24;line-height:1.8;margin-bottom:20px;">'
            f'{jd.get("job_summary","")}</div>', unsafe_allow_html=True)
        t1a, t1b = st.columns(2)
        with t1a:
            st.markdown("**Key Responsibilities**")
            for r in jd.get("responsibilities", []):
                st.markdown(f"- {r}")
        with t1b:
            st.markdown("**Mandatory Qualifications**")
            for q in jd.get("qualifications", []):
                st.markdown(f"- {q}")
        st.markdown("**Preferred Qualifications**")
        pq_cols = st.columns(2)
        for idx, p in enumerate(jd.get("preferred_qualifications", [])):
            pq_cols[idx % 2].markdown(f"- {p}")

    # ── Tab 2: Requirements ──────────────────────────────────
    with tab2:
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(
                '<div style="background:#EEF0FF;border-radius:10px;padding:16px 18px;">'
                '<div style="font-size:0.68rem;font-weight:700;letter-spacing:1px;'
                'color:#2A3080;margin-bottom:10px;">✅ MUST HAVE</div>'
                + "".join(
                    f'<div style="background:#DDE2FF;color:#1A2060;border-radius:6px;'
                    f'padding:6px 10px;margin:5px 0;font-size:0.82rem;font-weight:500;">• {item}</div>'
                    for item in reqs.get("must", []))
                + '</div>', unsafe_allow_html=True)
        with r2:
            st.markdown(
                '<div style="background:#FFF5E6;border-radius:10px;padding:16px 18px;">'
                '<div style="font-size:0.68rem;font-weight:700;letter-spacing:1px;'
                'color:#7B4A00;margin-bottom:10px;">⭐ NICE TO HAVE</div>'
                + "".join(
                    f'<div style="background:#FFE8C0;color:#5A3000;border-radius:6px;'
                    f'padding:6px 10px;margin:5px 0;font-size:0.82rem;font-weight:500;">• {item}</div>'
                    for item in reqs.get("addition", []))
                + '</div>', unsafe_allow_html=True)
        with r3:
            st.markdown(
                '<div style="background:#FFECEC;border-radius:10px;padding:16px 18px;">'
                '<div style="font-size:0.68rem;font-weight:700;letter-spacing:1px;'
                'color:#7A1A1A;margin-bottom:10px;">🚫 AUTO REJECT</div>'
                + "".join(
                    f'<div style="background:#FFD0D0;color:#5A0A0A;border-radius:6px;'
                    f'padding:6px 10px;margin:5px 0;font-size:0.82rem;font-weight:500;">• {item}</div>'
                    for item in reqs.get("fail", []))
                + '</div>', unsafe_allow_html=True)

    # ── Tab 3: Questions ─────────────────────────────────────
    with tab3:
        tag_colors = {
            "technical":   ("#9A7787", "Technical"),
            "behavioural": ("#C4849A", "Behavioural"),
            "situational": ("#D4A060", "Situational"),
            "core":        ("#8A90C4", "Core"),
        }
        diff_badge = {
            "easy":   "badge-easy",
            "medium": "badge-medium",
            "hard":   "badge-hard",
        }
        if not qs:
            st.info("No questions generated yet.")
        for i, q in enumerate(qs, 1):
            tag  = q.get("question_tag", "").lower()
            diff = q.get("difficulty", "").lower()
            color, tag_label = tag_colors.get(tag, ("#9A7787", tag.capitalize()))
            badge = diff_badge.get(diff, "badge-easy")
            comps = ", ".join(q.get("target_competency", []))
            st.markdown(f"""
            <div class="q-card {tag}">
              <div class="q-meta">
                Q{i} &nbsp;·&nbsp;
                <span style="color:{color};font-weight:700;">{tag_label.upper()}</span>
                &nbsp;·&nbsp;
                <span class="score-badge {badge}">{diff.capitalize()}</span>
                &nbsp;·&nbsp; {comps}
              </div>
              <div class="q-text">{q.get('question','')}</div>
            </div>""", unsafe_allow_html=True)
            triggers = q.get("follow_up_trigger", [])
            if triggers:
                with st.expander(f"↳ Follow-up triggers for Q{i}"):
                    for t in triggers:
                        st.markdown(f"- {t}")

    # ── Tab 4: Scoring Guide ─────────────────────────────────
    with tab4:
        st.caption("Score breakdown per answer: Keywords 30% · Scope Coverage 30% · Relevance 20% · Communication 20%")
        if not ea:
            st.info("No scoring guide generated yet.")
        for i, item in enumerate(ea, 1):
            q_preview = item.get("question", "")[:80]
            weight    = item.get("weight", 0)
            with st.expander(f"Q{i} · {q_preview}{'…' if len(item.get('question','')) > 80 else ''} · {weight} pts"):
                st.markdown(f"**💬 Ideal Answer**")
                st.markdown(f"> {item.get('ideal_answer', '')}")

                keywords = item.get("keywords", [])
                if keywords:
                    kw_html = " ".join(
                        f'<span style="background:#F0E6EC;color:#4A2A3A;border-radius:12px;'
                        f'padding:3px 10px;font-size:0.78rem;font-weight:600;margin:2px;'
                        f'display:inline-block;">{k}</span>'
                        for k in keywords)
                    st.markdown(f"**🔑 Keywords**<br>{kw_html}", unsafe_allow_html=True)

                criteria = item.get("scoring_criteria", {})
                sc1, sc2, sc3 = st.columns(3)
                sc1.error(f"**🔴 Poor**\n\n{criteria.get('poor', 'N/A')}")
                sc2.warning(f"**🟡 Average**\n\n{criteria.get('average', 'N/A')}")
                sc3.success(f"**🟢 Excellent**\n\n{criteria.get('excellent', 'N/A')}")

    # ── Downloads ────────────────────────────────────────────
    st.markdown('<div class="dl-strip"><div class="dl-title">⬇️ Download Blueprint Files</div></div>',
        unsafe_allow_html=True)
    d1, d2, d3, d4 = st.columns(4)
    d1.download_button("📄 Job Description",
        json.dumps(jd,   indent=4, ensure_ascii=False), "job_description.json",
        "application/json", use_container_width=True)
    d2.download_button("✅ Requirements",
        json.dumps(reqs, indent=4, ensure_ascii=False), "requirements.json",
        "application/json", use_container_width=True)
    d3.download_button("❓ Questions",
        json.dumps(qs,   indent=4, ensure_ascii=False), "questions.json",
        "application/json", use_container_width=True)
    d4.download_button("💡 Scoring Guide",
        json.dumps(ea,   indent=4, ensure_ascii=False), "expected_answers.json",
        "application/json", use_container_width=True)
    st.download_button(
        "📦 Full Blueprint (all-in-one JSON)",
        json.dumps({
            "job_title": jd.get("job_title"), "employment_type": etype, "urgency": urg,
            "job_description": jd, "requirements": reqs,
            "questions": qs, "expected_answers": ea,
        }, indent=4, ensure_ascii=False),
        "full_blueprint.json", "application/json", use_container_width=True)
