import re
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from src.config import GROQ_API_KEY, GROQ_MODEL_NAME

# Regex-based PII detection patterns
PII_PATTERNS = {
    "PAN": r"[A-Z]{5}[0-9]{4}[A-Z]",
    "Aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "Phone": r"\b(\+91[\-\s]?)?[6-9]\d{9}\b",
    "Email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "Account": r"\b\d{9,18}\b"
}

# Advisory Keywords for Rule-Based Classification
ADVISORY_KEYWORDS = [
    "should i", "recommend", "better", "best", "worth it", 
    "good investment", "predict", "will it grow", "advice",
    "where to invest", "compare"
]

class QueryProcessor:
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0.1,
            groq_api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL_NAME,
            max_retries=5 # Increased retries with exponential backoff to handle 30 RPM / 12K TPM Groq rate limits gracefully
        )
        self.classification_prompt = PromptTemplate(
            input_variables=["query"],
            template="""You are a query intent classifier for a mutual fund FAQ bot.
Analyze the following user query and determine if it is asking for factual information (FACTUAL) or seeking investment advice/recommendations (ADVISORY).
Reply strictly with only one word: FACTUAL or ADVISORY.

Query: "{query}"
Intent:"""
        )
        self.classification_chain = self.classification_prompt | self.llm

    def check_pii(self, query: str):
        """
        Checks for PII in the query.
        Returns (True, message) if PII is detected, else (False, "").
        """
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, query, re.IGNORECASE):
                return True, "I cannot process queries containing personal information (PAN, Aadhaar, phone numbers, etc.). Please remove any personal details and try again."
        return False, ""

    def classify_intent(self, query: str):
        """
        Classifies the intent of the query (FACTUAL vs ADVISORY).
        Returns (True, message) if it's an ADVISORY query, else (False, "").
        """
        # 1. Rule-based check
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ADVISORY_KEYWORDS):
            return True, self._advisory_refusal()
            
        # 2. LLM fallback check
        try:
            response = self.classification_chain.invoke({"query": query})
            intent = response.content.strip().upper()
            if "ADVISORY" in intent:
                return True, self._advisory_refusal()
        except Exception as e:
            print(f"Warning: Intent classification LLM fallback failed: {e}")
            
        return False, ""

    def _advisory_refusal(self):
        return "I can only provide factual information about mutual fund schemes. For investment advice, please consult a registered financial advisor. You may find helpful resources at [AMFI](https://www.amfiindia.com/) or [SEBI Investor Education](https://investor.sebi.gov.in/)."
        
    def process(self, query: str):
        """
        Runs the full pre-processing pipeline.
        Returns (is_valid, message_or_error).
        If is_valid is True, message_or_error is empty and the query should proceed to RAG.
        If is_valid is False, message_or_error contains the refusal message to show the user.
        """
        has_pii, pii_msg = self.check_pii(query)
        if has_pii:
            return False, pii_msg
            
        is_advisory, advisory_msg = self.classify_intent(query)
        if is_advisory:
            return False, advisory_msg
            
        return True, ""
