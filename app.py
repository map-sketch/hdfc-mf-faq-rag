import streamlit as st
import os
import pathlib

# ── Streamlit Cloud: bridge st.secrets -> os.environ ─────────────────────────
try:
    _secrets = st.secrets
    for _key in [
        "GROQ_API_KEY", "HF_TOKEN", "CHROMA_PERSIST_DIR",
        "COLLECTION_NAME", "BGE_MODEL_NAME", "GROQ_MODEL_NAME",
        "RETRIEVAL_TOP_K", "RETRIEVAL_SCORE_THRESHOLD",
    ]:
        if _key in _secrets:
            os.environ[_key] = str(_secrets[_key])
except Exception:
    pass

st.set_page_config(
    page_title="HDFC Mutual Fund FAQ Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load CSS from file + hide sidebar completely ─────────────────────────────
CSS_PATH = pathlib.Path(__file__).parent / "static" / "style.css"
css_text = CSS_PATH.read_text() if CSS_PATH.exists() else ""
css_text += """
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}
.main .block-container {
    padding-top: 0 !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}
"""
st.html(f"<style>{css_text}</style>")


# ── Pipeline loader ──────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_pipeline():
    from src.embeddings import get_vectorstore
    from src.ingest import process_and_ingest
    from src.rag_chain import RAGPipeline

    vs = get_vectorstore()
    try:
        count = vs._collection.count()
    except Exception:
        count = 0
    if count == 0:
        process_and_ingest()
    return RAGPipeline()


# ── Session state ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None


# ── Top header bar ───────────────────────────────────────────────────────────
st.markdown(
    '<div style="background:#0d0e0f; border-bottom:1px solid rgba(92,64,60,0.3);'
    '            padding:12px 32px; display:flex; align-items:center; justify-content:space-between;">'
    '  <div style="display:flex;align-items:center;gap:12px;">'
    '    <span style="font-family:Lexend,sans-serif;font-size:22px;font-weight:700;color:#dc2626;">ProMutual</span>'
    '    <span style="font-family:Inter,sans-serif;font-size:10px;font-weight:700;'
    '          letter-spacing:0.1em;text-transform:uppercase;color:#ac8884;'
    '          background:#1a1c1c;border-radius:9999px;padding:4px 12px;">HDFC TERMINAL</span>'
    '  </div>'
    '  <div style="display:flex;align-items:center;gap:8px;">'
    '    <span class="dot-pulse" style="width:8px;height:8px;border-radius:50%;'
    '          background:#dc2626;display:inline-block;"></span>'
    '    <span style="font-family:Inter,sans-serif;font-size:11px;font-weight:600;'
    '          letter-spacing:0.05em;color:#ac8884;">SYSTEM ACTIVE</span>'
    '  </div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Disclaimer banner ────────────────────────────────────────────────────────
st.markdown(
    '<div style="background:#121414; border-bottom:1px solid rgba(92,64,60,0.2);'
    '            padding:8px 32px; display:flex; align-items:center; gap:10px;'
    '            font-size:12px; color:#ac8884; line-height:1.5;">'
    '  <span style="color:#dc2626;">&#9432;</span>'
    '  <span><strong style="color:#e6bdb8;">Disclaimer:</strong> Facts-only. No investment advice.'
    '  All data sourced from Groww.in, refreshed daily at 10:30 AM IST.</span>'
    '</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# SUGGESTED QUERIES
# ─────────────────────────────────────────────────────────────────────────────
SUGGESTED = [
    "What is the expense ratio of HDFC Mid Cap Fund Direct Growth?",
    "What is the exit load for HDFC Defence Fund?",
    "What is the minimum SIP for HDFC Gold ETF FoF?",
    "What is the NAV of all the funds in your database?",
    "What is the benchmark index of HDFC Equity Fund?",
    "What is the risk rating for HDFC Silver ETF FoF?",
]


# ─────────────────────────────────────────────────────────────────────────────
# LANDING (no messages yet)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(
        '<div class="fade-in" style="max-width:860px;margin:0 auto;padding:60px 24px 20px;text-align:center;">'
        '  <div style="font-family:Lexend,sans-serif;font-size:42px;font-weight:700;'
        '              letter-spacing:-0.02em;color:#e3e2e2;margin-bottom:12px;">'
        '    Good morning, <span style="color:#dc2626;">Analyst</span></div>'
        '  <div style="font-family:Inter,sans-serif;font-size:17px;color:#ac8884;'
        '              max-width:520px;margin:0 auto 40px;line-height:1.6;">'
        '    Access institutional-grade insights about HDFC Mutual Fund schemes.'
        '    Facts-only. No advice. Always cited.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="max-width:860px;margin:0 auto;padding:0 24px;">'
        '  <div style="font-family:Inter,sans-serif;font-size:11px;font-weight:700;'
        '              letter-spacing:0.05em;text-transform:uppercase;color:#ac8884;'
        '              margin-bottom:16px;">Suggested Analysis</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    row1 = st.columns(3)
    row2 = st.columns(3)
    for idx, query in enumerate(SUGGESTED[:3]):
        with row1[idx]:
            if st.button(query, key=f"s_{idx}", use_container_width=True):
                st.session_state.pending_query = query
                st.rerun()
    for idx, query in enumerate(SUGGESTED[3:]):
        with row2[idx]:
            if st.button(query, key=f"s_{idx+3}", use_container_width=True):
                st.session_state.pending_query = query
                st.rerun()

    # Style suggestion buttons
    st.html("""<style>
    .main [data-testid="stButton"] button {
        background: #1e2020 !important;
        border: 1px solid rgba(92,64,60,0.4) !important;
        border-radius: 14px !important;
        color: #e3e2e2 !important;
        font-family: Inter, sans-serif !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        padding: 20px 16px !important;
        text-align: left !important;
        height: auto !important;
        min-height: 80px !important;
        line-height: 1.5 !important;
        white-space: normal !important;
        transition: all 0.25s !important;
    }
    .main [data-testid="stButton"] button:hover {
        background: #292a2a !important;
        border-color: rgba(220,38,38,0.5) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(220,38,38,0.08) !important;
    }
    </style>""")

else:
    # ─────────────────────────────────────────────────────────────────────
    # ACTIVE CHAT
    # ─────────────────────────────────────────────────────────────────────
    st.markdown('<div style="max-width:860px;margin:0 auto;padding:24px 24px 120px;">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="fade-in" style="display:flex;justify-content:flex-end;margin-bottom:20px;">'
                f'  <div style="background:#1e2020;border:1px solid rgba(92,64,60,0.4);'
                f'              border-radius:20px 20px 4px 20px;padding:14px 20px;'
                f'              max-width:75%;color:#e3e2e2;line-height:1.6;font-size:15px;">'
                f'    {msg["content"]}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="fade-in" style="display:flex;align-items:flex-start;gap:14px;margin-bottom:20px;">'
                f'  <div style="width:40px;height:40px;flex-shrink:0;border-radius:12px;'
                f'              background:#dc2626;display:flex;align-items:center;justify-content:center;'
                f'              box-shadow:0 0 15px rgba(220,38,38,0.15);font-size:18px;">&#127974;</div>'
                f'  <div style="background:#1a1c1c;border:1px solid rgba(92,64,60,0.4);'
                f'              border-radius:4px 20px 20px 20px;padding:16px 22px;flex:1;'
                f'              color:#e3e2e2;line-height:1.7;font-size:15px;">'
                f'    {msg["content"]}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)


# ── Chat input ───────────────────────────────────────────────────────────────
prompt = st.chat_input("Ask about expense ratios, exit loads, NAV, minimum SIP...")

if st.session_state.pending_query:
    prompt = st.session_state.pending_query
    st.session_state.pending_query = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display the user's message immediately before blocking
    st.markdown(
        f'<div class="fade-in" style="display:flex;justify-content:flex-end;margin-bottom:20px;">'
        f'  <div style="background:#1e2020;border:1px solid rgba(92,64,60,0.4);'
        f'              border-radius:20px 20px 4px 20px;padding:14px 20px;'
        f'              max-width:75%;color:#e3e2e2;line-height:1.6;font-size:15px;">'
        f'    {prompt}</div></div>',
        unsafe_allow_html=True,
    )
    
    with st.spinner("Analyzing query..."):
        try:
            pipeline = get_pipeline()
            response = pipeline.process_query(prompt)
        except Exception as e:
            response = f"Error: {str(e)}"
            
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
