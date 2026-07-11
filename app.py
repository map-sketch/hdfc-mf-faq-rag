import streamlit as st
import os
from src.rag_chain import RAGPipeline

# ── Streamlit Cloud: load secrets into env vars ──────────────────────────────
# On Streamlit Cloud, secrets are in st.secrets (TOML), not a .env file.
# This block bridges them so the rest of the code (which reads os.getenv) works.
if hasattr(st, "secrets"):
    for key in ["GROQ_API_KEY", "HF_TOKEN", "CHROMA_PERSIST_DIR",
                "COLLECTION_NAME", "BGE_MODEL_NAME", "GROQ_MODEL_NAME",
                "RETRIEVAL_TOP_K", "RETRIEVAL_SCORE_THRESHOLD"]:
        if key in st.secrets and not os.environ.get(key):
            os.environ[key] = str(st.secrets[key])

# Page configuration
st.set_page_config(
    page_title="HDFC Mutual Fund FAQ Assistant",
    page_icon="🏦",
    layout="centered"
)


@st.cache_resource(show_spinner="Loading knowledge base... (first run may take a minute)")
def get_pipeline():
    """
    Initialise the RAG pipeline once per session.
    On first cloud deploy the vectorstore is empty — auto-ingest runs here.
    """
    from src.embeddings import get_vectorstore
    from src.ingest import process_and_ingest

    vs = get_vectorstore()
    try:
        count = vs._collection.count()
    except Exception:
        count = 0

    if count == 0:
        st.info("📥 Vector store is empty — running initial data ingestion. This takes ~60 seconds...")
        process_and_ingest()

    return RAGPipeline()


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []


def main():
    init_session_state()

    st.title("🏦 Mutual Fund FAQ Assistant")

    # Disclaimer Banner
    st.warning("⚠️ **Facts-only. No investment advice.**")

    st.markdown("""
    Welcome! I can help you with factual information about HDFC Mutual Fund schemes. Try asking:
    - 💡 *What is the expense ratio of HDFC Mid Cap Fund Direct Growth?*
    - 💡 *What is the exit load for HDFC Defence Fund?*
    - 💡 *What is the minimum SIP amount for HDFC Gold ETF FoF?*
    - 💡 *What is the NAV of all the funds in your database?*
    """)

    st.divider()

    # Load pipeline (cached — only initialised once per session)
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
                    f"An error occurred while processing your request. "
                    f"Please ensure your API key configuration is valid.\n\n"
                    f"**Error details:** {str(e)}"
                )

        with st.chat_message("assistant"):
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
