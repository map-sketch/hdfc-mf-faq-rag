import streamlit as st
import os
import time

# ── Streamlit Cloud: bridge st.secrets → os.environ ─────────────────────────
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
    initial_sidebar_state="expanded"
)

# ── Crimson Terminal Design System ───────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Lexend:wght@400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<style>
/* ── Reset & Base ── */
html, body, [data-testid="stApp"] {
    background-color: #0a0a0a !important;
    color: #e3e2e2 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stHeader"] { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0d0e0f !important;
    border-right: 1px solid rgba(92,64,60,0.4) !important;
    min-width: 260px !important;
    max-width: 260px !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

/* ── Main content ── */
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    color: #e3e2e2 !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] {
    background-color: #1e2020 !important;
    border: 1px solid rgba(92,64,60,0.6) !important;
    border-radius: 16px !important;
    color: #e3e2e2 !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #dc2626 !important;
    box-shadow: 0 0 0 1px #dc2626 !important;
}
[data-testid="stChatInput"] textarea {
    color: #e3e2e2 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stChatInput"] button {
    background-color: #dc2626 !important;
    border-radius: 12px !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #dc2626 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background-color: #343535; border-radius: 20px; }

/* ── Links ── */
a { color: #90cdff !important; }
a:hover { color: #dc2626 !important; }

/* ── Dot pulse animation ── */
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
.dot-pulse { animation: pulse 2s ease-in-out infinite; }

/* ── fadeIn ── */
@keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.fade-in { animation: fadeIn 0.4s ease-out; }

/* ── Suggestion card hover ── */
.suggestion-card {
    background: #1e2020;
    border: 1px solid rgba(92,64,60,0.4);
    border-radius: 16px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
}
.suggestion-card:hover {
    background: #292a2a;
    border-color: rgba(220,38,38,0.5);
    transform: translateY(-2px);
}
.suggestion-icon {
    width: 32px; height: 32px;
    border-radius: 50%;
    background: rgba(220,38,38,0.15);
    border: 1px solid rgba(220,38,38,0.3);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 14px;
}

/* ── Top header bar ── */
.top-header {
    background: #1a1c1c;
    border-bottom: 1px solid rgba(92,64,60,0.3);
    padding: 10px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
}

/* ── Disclaimer banner ── */
.disclaimer-banner {
    background: #0d0e0f;
    border-bottom: 1px solid rgba(92,64,60,0.3);
    padding: 10px 24px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    font-size: 13px;
    color: #e6bdb8;
    line-height: 1.5;
}
.disclaimer-banner strong { color: #e3e2e2; }

/* ── Chat container ── */
.chat-container {
    max-width: 860px;
    margin: 0 auto;
    padding: 32px 24px 160px;
}

/* ── Message bubbles ── */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 24px;
}
.msg-user-bubble {
    background: #1e2020;
    border: 1px solid rgba(92,64,60,0.4);
    border-radius: 20px 20px 4px 20px;
    padding: 14px 20px;
    max-width: 80%;
    font-family: 'Inter', sans-serif;
    color: #e3e2e2;
    line-height: 1.6;
}
.msg-bot {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 24px;
}
.bot-avatar {
    width: 40px; height: 40px; flex-shrink: 0;
    border-radius: 12px;
    background: #dc2626;
    border: 1px solid rgba(220,38,38,0.5);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 0 15px rgba(220,38,38,0.15);
    font-size: 18px;
}
.msg-bot-bubble {
    background: #1a1c1c;
    border: 1px solid rgba(92,64,60,0.4);
    border-radius: 4px 20px 20px 20px;
    padding: 16px 22px;
    font-family: 'Inter', sans-serif;
    color: #e3e2e2;
    line-height: 1.7;
    flex: 1;
}

/* ── Input area docked bottom ── */
.input-dock {
    position: fixed;
    bottom: 0; left: 260px; right: 0;
    background: rgba(13,14,15,0.92);
    backdrop-filter: blur(12px);
    border-top: 1px solid rgba(92,64,60,0.3);
    padding: 16px 24px 20px;
    z-index: 50;
}
.input-inner { max-width: 860px; margin: 0 auto; }
.chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.chip {
    padding: 6px 14px;
    border-radius: 9999px;
    border: 1px solid rgba(92,64,60,0.4);
    background: #1a1c1c;
    color: #e6bdb8;
    font-size: 11px;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    letter-spacing: 0.04em;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex; align-items: center; gap: 5px;
}
.chip:hover { background: #292a2a; border-color: rgba(220,38,38,0.5); color: #dc2626; }

/* ── Hero / landing ── */
.hero {
    max-width: 860px;
    margin: 0 auto;
    padding: 60px 24px 200px;
    text-align: center;
}
.hero-title {
    font-family: 'Lexend', sans-serif;
    font-size: 48px;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.15;
    color: #e3e2e2;
    margin-bottom: 16px;
}
.hero-title span { color: #dc2626; }
.hero-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 18px;
    color: #e6bdb8;
    max-width: 540px;
    margin: 0 auto 48px;
    line-height: 1.6;
}
.main-input-box {
    background: #1e2020;
    border: 2px solid rgba(92,64,60,0.5);
    border-radius: 16px;
    padding: 20px 20px 16px;
    margin-bottom: 48px;
    transition: border-color 0.2s;
    position: relative;
}
.main-input-box::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 17px;
    background: linear-gradient(135deg, rgba(220,38,38,0.15), rgba(56,57,58,0.1));
    pointer-events: none;
    opacity: 0.5;
}
.section-label {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #ac8884;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.cards-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
}
@media(max-width:768px) { .cards-grid { grid-template-columns: 1fr; } }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:28px 20px 24px; border-bottom:1px solid rgba(92,64,60,0.3);">
        <div style="font-family:'Lexend',sans-serif; font-size:26px; font-weight:700;
                    color:#dc2626; margin-bottom:4px;">ProMutual</div>
        <div style="font-family:'Inter',sans-serif; font-size:10px; font-weight:700;
                    letter-spacing:0.1em; text-transform:uppercase; color:#ac8884;">
            HDFC Investment Terminal
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin-top:14px;">
            <span class="dot-pulse" style="width:8px;height:8px;border-radius:50%;
                  background:#dc2626;display:inline-block;"></span>
            <span style="font-family:'Inter',sans-serif;font-size:11px;font-weight:600;
                         letter-spacing:0.05em;color:#ac8884;">MARKET HOURS ACTIVE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Nav items
    page = st.radio(
        label="nav",
        options=["💬  Chat", "📊  Fund Overview", "🕐  History"],
        label_visibility="collapsed",
    )
    st.markdown("""
    <style>
    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 4px !important;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] { display:none; }
    [data-testid="stSidebar"] label {
        font-family: 'Inter', sans-serif !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.07em !important;
        text-transform: uppercase !important;
        color: #ac8884 !important;
        padding: 12px 16px !important;
        border-radius: 12px !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        transition: all 0.2s !important;
        cursor: pointer !important;
        border: 1px solid transparent !important;
    }
    [data-testid="stSidebar"] label:hover {
        background: #1e2020 !important;
        color: #e3e2e2 !important;
    }
    [data-testid="stSidebar"] label[data-checked="true"],
    [data-testid="stSidebar"] [aria-checked="true"] + label {
        background: rgba(220,38,38,0.15) !important;
        color: #dc2626 !important;
        border-color: rgba(220,38,38,0.25) !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] > div {
        padding: 0 8px !important;
        gap: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Bottom sidebar
    st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="position:absolute;bottom:0;left:0;right:0;padding:20px;
                border-top:1px solid rgba(92,64,60,0.3);">
        <div style="background:#1e2020;border:1px solid rgba(220,38,38,0.25);
                    border-radius:12px;padding:12px 16px;text-align:center;
                    font-family:'Inter',sans-serif;font-size:11px;font-weight:700;
                    letter-spacing:0.05em;color:#dc2626;cursor:pointer;
                    transition:all 0.2s;"
             onmouseover="this.style.background='rgba(220,38,38,0.1)'"
             onmouseout="this.style.background='#1e2020'">
            ⭐ UPGRADE TO PREMIUM
        </div>
        <div style="margin-top:8px;padding:10px 12px;border-radius:12px;
                    font-family:'Inter',sans-serif;font-size:11px;font-weight:700;
                    letter-spacing:0.05em;color:#ac8884;cursor:pointer;
                    display:flex;align-items:center;gap:8px;"
             onmouseover="this.style.background='#1e2020';this.style.color='#e3e2e2'"
             onmouseout="this.style.background='transparent';this.style.color='#ac8884'">
            ⚙️ SETTINGS
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline loader
# ─────────────────────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# Disclaimer banner
st.markdown("""
<div class="disclaimer-banner">
    <span style="color:#dc2626;font-size:18px;flex-shrink:0;">ℹ️</span>
    <p><strong>Important Disclosure:</strong> This assistant provides factual information only
    about HDFC Mutual Fund schemes. It does not constitute financial advice, investment
    recommendations, or an offer to buy/sell securities. Always verify independently.</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CHAT PAGE
# ─────────────────────────────────────────────────────────────────────────────
if "Chat" in page:

    SUGGESTED = [
        ("📈", "show_chart",  "What is the expense ratio of HDFC Mid Cap Fund Direct Growth?"),
        ("💰", "account_balance", "What is the exit load for HDFC Defence Fund?"),
        ("📘", "library_books", "What is the minimum SIP for HDFC Gold ETF FoF?"),
        ("🔢", "analytics", "What is the NAV of all the funds in your database?"),
        ("🏦", "account_balance_wallet", "What is the benchmark index of HDFC Equity Fund?"),
        ("📋", "description", "What is the risk rating for HDFC Silver ETF FoF?"),
    ]

    if not st.session_state.messages:
        # ── Landing / Hero ───────────────────────────────────────────────
        st.markdown("""
        <div class="hero fade-in">
            <div class="hero-title">Good morning, <span>Analyst</span></div>
            <div class="hero-subtitle">
                Access institutional-grade insights about HDFC Mutual Fund schemes.
                Facts-only. No advice. Always cited.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Suggested queries grid
        st.markdown("""
        <div style="max-width:860px;margin:0 auto;padding:0 24px 200px;">
            <div class="section-label">
                <span>🔍</span> SUGGESTED ANALYSIS
            </div>
            <div class="cards-grid">
        """, unsafe_allow_html=True)

        cols = st.columns(3)
        for idx, (emoji, icon, query) in enumerate(SUGGESTED):
            with cols[idx % 3]:
                if st.button(
                    f"{emoji}  {query}",
                    key=f"suggest_{idx}",
                    use_container_width=True,
                ):
                    st.session_state.pending_query = query
                    st.rerun()

        st.markdown("</div></div>", unsafe_allow_html=True)

        # Style the suggestion buttons
        st.markdown("""
        <style>
        [data-testid="stButton"] button {
            background: #1e2020 !important;
            border: 1px solid rgba(92,64,60,0.4) !important;
            border-radius: 14px !important;
            color: #e3e2e2 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 13px !important;
            font-weight: 400 !important;
            padding: 18px 16px !important;
            text-align: left !important;
            height: auto !important;
            min-height: 88px !important;
            line-height: 1.5 !important;
            white-space: normal !important;
            transition: all 0.25s !important;
        }
        [data-testid="stButton"] button:hover {
            background: #292a2a !important;
            border-color: rgba(220,38,38,0.5) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(220,38,38,0.08) !important;
        }
        </style>
        """, unsafe_allow_html=True)

    else:
        # ── Active chat view ─────────────────────────────────────────────
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-user fade-in">
                    <div class="msg-user-bubble">{msg["content"]}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-bot fade-in">
                    <div class="bot-avatar">🏦</div>
                    <div class="msg-bot-bubble">{msg["content"]}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Suggestion chips below last message
        st.markdown("""
        <div class="input-dock">
          <div class="input-inner">
            <div class="chip-row">
        """, unsafe_allow_html=True)

        CHIPS = [
            ("📈", "Expense Ratios",     "What are the expense ratios of all funds?"),
            ("💰", "Exit Loads",          "What are the exit loads of all funds?"),
            ("📊", "NAV Today",           "What is the NAV of all the funds in your database?"),
            ("🏷️", "Minimum SIP",        "What is the minimum SIP for all funds?"),
        ]
        chip_cols = st.columns(len(CHIPS))
        for i, (emoji, label, query) in enumerate(CHIPS):
            with chip_cols[i]:
                if st.button(f"{emoji} {label}", key=f"chip_{i}"):
                    st.session_state.pending_query = query
                    st.rerun()

        st.markdown("</div></div></div>", unsafe_allow_html=True)

        st.markdown("""
        <style>
        [data-testid="stButton"] button {
            background: #1a1c1c !important;
            border: 1px solid rgba(92,64,60,0.4) !important;
            border-radius: 9999px !important;
            color: #e6bdb8 !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            letter-spacing: 0.04em !important;
            padding: 7px 14px !important;
            height: auto !important;
            transition: all 0.2s !important;
        }
        [data-testid="stButton"] button:hover {
            background: #292a2a !important;
            border-color: rgba(220,38,38,0.5) !important;
            color: #dc2626 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # ── Chat input ───────────────────────────────────────────────────────
    prompt = st.chat_input("Ask about expense ratios, exit loads, NAV, minimum SIP...")

    # Handle suggestion click
    if st.session_state.pending_query:
        prompt = st.session_state.pending_query
        st.session_state.pending_query = None

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner(""):
            st.markdown("""
            <div style="display:flex;align-items:center;gap:10px;padding:12px 24px;
                        color:#ac8884;font-size:13px;font-family:'Inter',sans-serif;">
                <span class="dot-pulse" style="width:8px;height:8px;border-radius:50%;
                      background:#dc2626;display:inline-block;"></span>
                Analyzing query...
            </div>
            """, unsafe_allow_html=True)
            try:
                pipeline = get_pipeline()
                response = pipeline.process_query(prompt)
            except Exception as e:
                response = (
                    f"⚠️ An error occurred: {str(e)}\n\n"
                    "Please ensure your `GROQ_API_KEY` is configured correctly."
                )

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # Footer disclaimer
    st.markdown("""
    <div style="text-align:center;font-family:'Inter',sans-serif;font-size:10px;
                color:rgba(172,136,132,0.5);padding:8px;position:fixed;bottom:80px;
                left:260px;right:0;z-index:40;">
        ProMutual Analyst may produce inaccurate information. Verify facts independently.
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# FUND OVERVIEW PAGE
# ─────────────────────────────────────────────────────────────────────────────
elif "Fund Overview" in page:
    st.markdown("""
    <div style="padding:40px 32px 24px;">
        <div style="font-family:'Lexend',sans-serif;font-size:32px;font-weight:700;
                    color:#e3e2e2;margin-bottom:8px;">Fund Overview</div>
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:#ac8884;">
            5 HDFC Mutual Fund schemes — data refreshed daily at 10:30 AM IST
        </div>
    </div>
    """, unsafe_allow_html=True)

    FUNDS = [
        ("HDFC Silver ETF FoF Direct Growth",         "Commodities", "Silver",    "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth"),
        ("HDFC Mid Cap Fund Direct Growth",            "Equity",      "Mid Cap",   "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"),
        ("HDFC Equity Fund Direct Growth",             "Equity",      "Flexi Cap", "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth"),
        ("HDFC Defence Fund Direct Growth",            "Equity",      "Thematic",  "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth"),
        ("HDFC Gold ETF Fund of Fund Direct Growth",   "Commodities", "Gold",      "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth"),
    ]

    for name, cat, sub, url in FUNDS:
        st.markdown(f"""
        <div style="margin:0 32px 16px;background:#1a1c1c;border:1px solid rgba(92,64,60,0.4);
                    border-radius:16px;padding:20px 24px;display:flex;
                    align-items:center;justify-content:space-between;
                    transition:border-color 0.2s;"
             onmouseover="this.style.borderColor='rgba(220,38,38,0.4)'"
             onmouseout="this.style.borderColor='rgba(92,64,60,0.4)'">
            <div style="display:flex;align-items:center;gap:16px;">
                <div style="width:44px;height:44px;border-radius:12px;background:rgba(220,38,38,0.15);
                            border:1px solid rgba(220,38,38,0.3);display:flex;align-items:center;
                            justify-content:center;font-size:18px;">🏦</div>
                <div>
                    <div style="font-family:'Inter',sans-serif;font-size:15px;font-weight:600;
                                color:#e3e2e2;margin-bottom:4px;">{name}</div>
                    <div style="display:flex;gap:8px;align-items:center;">
                        <span style="font-family:'Inter',sans-serif;font-size:10px;font-weight:700;
                                     letter-spacing:0.05em;text-transform:uppercase;
                                     background:rgba(220,38,38,0.15);color:#dc2626;
                                     border-radius:9999px;padding:2px 10px;">{cat}</span>
                        <span style="font-family:'Inter',sans-serif;font-size:10px;font-weight:700;
                                     letter-spacing:0.05em;text-transform:uppercase;
                                     background:#1e2020;color:#ac8884;
                                     border-radius:9999px;padding:2px 10px;">{sub}</span>
                    </div>
                </div>
            </div>
            <a href="{url}" target="_blank"
               style="font-family:'Inter',sans-serif;font-size:11px;font-weight:700;
                      letter-spacing:0.05em;color:#dc2626;text-decoration:none;
                      border:1px solid rgba(220,38,38,0.3);border-radius:8px;
                      padding:8px 14px;transition:all 0.2s;"
               onmouseover="this.style.background='rgba(220,38,38,0.1)'"
               onmouseout="this.style.background='transparent'">
               VIEW ↗
            </a>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin:32px;padding:20px 24px;background:#0d0e0f;
                border:1px solid rgba(92,64,60,0.3);border-radius:16px;
                font-family:'Inter',sans-serif;font-size:13px;color:#ac8884;line-height:1.6;">
        <strong style="color:#dc2626;">ℹ️ Data Source:</strong>
        All fund data is scraped daily from <a href="https://groww.in" target="_blank">Groww.in</a>
        at <strong style="color:#e3e2e2;">10:30 AM IST</strong> via a GitHub Actions scheduler.
        The ChromaDB vector store is refreshed automatically.
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HISTORY PAGE
# ─────────────────────────────────────────────────────────────────────────────
elif "History" in page:
    st.markdown("""
    <div style="padding:40px 32px 24px;">
        <div style="font-family:'Lexend',sans-serif;font-size:32px;font-weight:700;
                    color:#e3e2e2;margin-bottom:8px;">Session History</div>
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:#ac8884;">
            Queries from the current session
        </div>
    </div>
    """, unsafe_allow_html=True)

    user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
    if not user_msgs:
        st.markdown("""
        <div style="margin:40px 32px;text-align:center;color:#ac8884;
                    font-family:'Inter',sans-serif;font-size:14px;">
            No queries yet this session. Start chatting to see your history here.
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, msg in enumerate(reversed(user_msgs)):
            st.markdown(f"""
            <div style="margin:0 32px 12px;background:#1a1c1c;border:1px solid rgba(92,64,60,0.3);
                        border-radius:12px;padding:14px 20px;display:flex;align-items:center;gap:14px;">
                <div style="width:28px;height:28px;border-radius:8px;background:rgba(220,38,38,0.1);
                            border:1px solid rgba(220,38,38,0.2);display:flex;align-items:center;
                            justify-content:center;font-size:12px;color:#dc2626;font-weight:700;
                            flex-shrink:0;">{len(user_msgs)-i}</div>
                <div style="font-family:'Inter',sans-serif;font-size:14px;color:#e3e2e2;
                            line-height:1.4;">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑️  Clear History", key="clear_history"):
            st.session_state.messages = []
            st.rerun()
