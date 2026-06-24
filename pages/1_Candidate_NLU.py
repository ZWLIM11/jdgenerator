"""
pages/1_Candidate_NLU.py
Recruitment NLU Agent — grounded candidate Q&A page.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nlu.nlu_agent import answer_candidate_question, is_blueprint_loaded

st.set_page_config(
    page_title="Candidate NLU Agent",
    page_icon="💬",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #FDF6F0; }
.block-container { max-width: 800px !important; padding-top: 1.8rem !important; }

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

.msg-user {
    background: #F5EFF2; border-radius: 12px 12px 4px 12px;
    padding: 14px 18px; margin: 10px 0; margin-left: 20%;
    font-size: .9rem; color: #4A3040;
    border: 1px solid #E4AFB0;
}
.msg-bot {
    background: white; border-radius: 12px 12px 12px 4px;
    padding: 14px 18px; margin: 10px 0; margin-right: 20%;
    font-size: .9rem; color: #3A3A3A;
    border: 1px solid #F0E6E0;
    box-shadow: 0 1px 4px rgba(154,119,135,.07);
}
.msg-label {
    font-size: .68rem; font-weight: 700; letter-spacing: .8px;
    text-transform: uppercase; margin-bottom: 6px;
}
.user-label { color: #9A7787; }
.bot-label  { color: #6B4A5A; }

.suggestion-btn > button {
    background: #F5EFF2 !important; border: 1px solid #E4AFB0 !important;
    border-radius: 20px !important; color: #6B4A5A !important;
    font-size: .8rem !important; padding: 6px 14px !important;
    margin: 3px !important;
}

.status-ok  { background: #E6F7EF; border-radius: 8px; padding: 10px 14px;
              color: #1A6B40; font-size: .85rem; font-weight: 500; }
.status-err { background: #FFF0F0; border-radius: 8px; padding: 10px 14px;
              color: #8B3A3A; font-size: .85rem; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="badge">RECRUITMENT NLU AGENT</div>
  <h1>💬 Candidate Q&A</h1>
  <p>Ask any question about the job role. Answers are grounded in the generated recruitment blueprint — not guessed.</p>
</div>
""", unsafe_allow_html=True)

# ── Status ────────────────────────────────────────────────────
loaded = is_blueprint_loaded()

if not loaded:
    st.markdown("""
    <div class="status-err">
        ⚠️ No blueprint loaded yet. Please go to the
        <strong>Blueprint Generator</strong> page, fill in the form,
        and click <strong>Generate Full Blueprint</strong> first.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

n_chunks = st.session_state.get("nlu_chunks", "?")
st.markdown(f"""
<div class="status-ok">
    ✅ Blueprint loaded — <strong>{n_chunks} knowledge chunks</strong> ready.
    All answers are grounded in the recruitment blueprint.
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ── Suggested Questions ───────────────────────────────────────
SUGGESTIONS = [
    "Is Python required for this role?",
    "What are the minimum qualifications?",
    "What does this role involve day to day?",
    "What is the salary range?",
    "What are the auto-fail conditions?",
    "Is this a remote position?",
    "What competencies are being assessed?",
    "How many interview questions are there?",
]

st.markdown("**💡 Suggested Questions**")
cols = st.columns(4)
for i, suggestion in enumerate(SUGGESTIONS):
    if cols[i % 4].button(suggestion, key=f"sug_{i}", use_container_width=True):
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        st.session_state.pending_question = suggestion

st.markdown("---")

# ── Chat History ──────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for entry in st.session_state.chat_history:
    st.markdown(f"""
    <div class="msg-user">
        <div class="msg-label user-label">You</div>
        {entry['question']}
    </div>
    <div class="msg-bot">
        <div class="msg-label bot-label">🤖 NLU Agent</div>
        {entry['answer']}
    </div>
    """, unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────────
with st.form("nlu_form", clear_on_submit=True):
    user_q = st.text_input(
        "Your question",
        value=st.session_state.pop("pending_question", ""),
        placeholder="e.g. Is Python required for this role?",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Send →", use_container_width=True)

if submitted and user_q.strip():
    with st.spinner("Searching blueprint and generating answer…"):
        answer = answer_candidate_question(user_q.strip())

    st.session_state.chat_history.append({
        "question": user_q.strip(),
        "answer":   answer,
    })
    st.rerun()

# ── Clear ─────────────────────────────────────────────────────
if st.session_state.chat_history:
    if st.button("🗑️ Clear conversation", use_container_width=False):
        st.session_state.chat_history = []
        st.rerun()
