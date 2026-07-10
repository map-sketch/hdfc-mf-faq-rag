import streamlit as st
from src.rag_chain import RAGPipeline

# Page configuration
st.set_page_config(
    page_title="HDFC Mutual Fund FAQ Assistant",
    page_icon="🏦",
    layout="centered"
)

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "rag_pipeline" not in st.session_state:
        # Initialize RAG Pipeline only once
        st.session_state.rag_pipeline = RAGPipeline()

def main():
    init_session_state()
    
    st.title("🏦 Mutual Fund FAQ Assistant")
    
    # Disclaimer Banner
    st.warning("⚠️ **Facts-only. No investment advice.**")
    
    st.markdown("""
    Welcome! I can help you with factual information about HDFC Mutual Fund schemes. Try asking:
    - 💡 *What is the expense ratio of HDFC Mid Cap Fund Direct Growth?*
    - 💡 *What is the exit load for HDFC Flexi Cap?*
    - 💡 *What is the minimum SIP amount for HDFC Defence Fund?*
    """)
    
    st.divider()

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Type your question here..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Analyzing your query..."):
            try:
                response = st.session_state.rag_pipeline.process_query(prompt)
            except Exception as e:
                response = f"An error occurred while processing your request. Please ensure your `.env` configuration (e.g. Groq API key) is valid. \n\n**Error details:** {str(e)}"
                
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
