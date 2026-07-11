import streamlit as st
import os

# ── Streamlit Cloud: bridge st.secrets → os.environ ─────────────────────────
# This MUST run before any src.* imports, since those modules read os.getenv()
# at import time (e.g. config.py calls load_dotenv, ChatGroq reads GROQ_API_KEY).
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
    # Running locally — env vars already loaded from .env via python-dotenv
    pass

# Page configuration
st.set_page_config(
    page_title="HDFC Mutual Fund FAQ Assistant",
    page_icon="🏦",
    layout="centered"
)


@st.cache_resource(show_spinner="Loading knowledge base… (first run may take ~60 s)")
def get_pipeline():
    """
    All src.* imports live here so they run AFTER the secrets bridge above.
    On first Streamlit Cloud deploy the vectorstore is empty — auto-ingest fires.
    """
    # Lazy imports — after env vars are guaranteed to be set
    from src.embeddings import get_vectorstore
    from src.ingest import process_and_ingest
    from src.rag_chain import RAGPipeline

    vs = get_vectorstore()
    try:
        count = vs._collection.count()
    except Exception:
        count = 0

    if count == 0:
        st.info("📥 Vector store is empty — running initial data ingestion (~60 s)...")
        process_and_ingest()

    return RAGPipeline()


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []


def main():
    init_session_state()

    st.title("🏦 Mutual Fund FAQ Assistant")
    st.warning("⚠️ **Facts-only. No investment advice.**")

    st.markdown("""
    Welcome! I can help you with factual information about HDFC Mutual Fund schemes. Try asking:
    - 💡 *What is the expense ratio of HDFC Mid Cap Fund Direct Growth?*
    - 💡 *What is the exit load for HDFC Defence Fund?*
    - 💡 *What is the minimum SIP amount for HDFC Gold ETF FoF?*
    - 💡 *What is the NAV of all the funds in your database?*
    """)

    st.divider()

    # Load pipeline (cached — initialised only once per session)
    pipeline = get_pipeline()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Type your question here..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Analyzing your query..."):
            try:
                response = pipeline.process_query(prompt)
            except Exception as e:
                response = (
                    "An error occurred while processing your request. "
                    "Please ensure your API key is configured correctly.\n\n"
                    f"**Error:** {str(e)}"
                )

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
