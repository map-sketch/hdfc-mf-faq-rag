import re
from langchain_groq import ChatGroq
from src.prompts import RAG_PROMPT
from src.config import GROQ_API_KEY, GROQ_MODEL_NAME

class ResponseGenerator:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0.1,
            groq_api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL_NAME,
            max_tokens=256,
            max_retries=5 # Increased retries with exponential backoff to handle 30 RPM / 12K TPM Groq rate limits gracefully
        )
        self.chain = RAG_PROMPT | self.llm
        
    def generate_response(self, user_query: str, assembled_docs: list):
        if not assembled_docs:
            return "I don't have this information in my current sources. Please check the official HDFC Mutual Fund website."
            
        # Format context
        context_parts = []
        for doc in assembled_docs:
            source = doc.metadata.get("source_url", "Unknown source")
            date = doc.metadata.get("scrape_date", "Unknown date")
            context_parts.append(f"Content: {doc.page_content}\nSource: {source}\nDate: {date}")
            
        retrieved_context = "\n\n---\n\n".join(context_parts)
        
        # Capture metadata of highest-ranked chunk for the formatter
        top_metadata = assembled_docs[0].metadata
        
        # Invoke LLM
        response = self.chain.invoke({
            "retrieved_context": retrieved_context,
            "user_query": user_query
        })
        
        return self._format_response(response.content, top_metadata)
        
    def _format_response(self, llm_output: str, source_metadata: dict):
        # 1. Validate sentence count (<= 3)
        # Using a simple period split, preserving periods
        sentences = re.split(r'(?<=[.!?]) +', llm_output.strip())
        if len(sentences) > 3:
            llm_output = " ".join(sentences[:3])
            if not llm_output.endswith(('.', '!', '?')):
                llm_output += '.'
                
        # 2. Ensure citation link is present
        url_pattern = r'https?://[^\s]+'
        has_url = re.search(url_pattern, llm_output)
        source_url = source_metadata.get("source_url", "No URL provided")
        
        if not has_url:
            llm_output += f"\nSource: {source_url}"
            
        # 3. Append footer
        last_updated = source_metadata.get("scrape_date", "Unknown date")
        footer_text = f"Last updated from sources: {last_updated}"
        
        if footer_text not in llm_output:
            llm_output += f"\n\n{footer_text}"
            
        return llm_output
