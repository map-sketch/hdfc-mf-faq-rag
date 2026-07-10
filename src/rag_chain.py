from src.query_processor import QueryProcessor
from src.retriever import retrieve_context
from src.generator import ResponseGenerator

class RAGPipeline:
    def __init__(self):
        self.query_processor = QueryProcessor()
        self.generator = ResponseGenerator()
        
    def process_query(self, user_query: str) -> str:
        # Step 1: Pre-processing (Sanitize and Classify)
        is_valid, error_msg = self.query_processor.process(user_query)
        if not is_valid:
            # Return refusal message (PII or Advisory)
            return error_msg
            
        # Step 2: Retrieval
        assembled_docs = retrieve_context(user_query)
        
        # Step 3: Generation
        final_response = self.generator.generate_response(user_query, assembled_docs)
        
        return final_response
