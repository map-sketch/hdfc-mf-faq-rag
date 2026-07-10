import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Vector Store Configurations
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./vectorstore")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "hdfc_mutual_fund_corpus")

# Model Configurations
BGE_MODEL_NAME = os.getenv("BGE_MODEL_NAME", "BAAI/bge-small-en-v1.5")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")

# Retrieval Configurations
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", 5))
RETRIEVAL_SCORE_THRESHOLD = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", 0.7))

# Scraping URLs (HDFC Mutual Funds from Groww)
GROWW_SCHEME_URLS = [
    "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth"
]

# Validation
if not GROQ_API_KEY or GROQ_API_KEY == "gsk_your_api_key_here":
    print("WARNING: GROQ_API_KEY is not set or is using the default placeholder. Please update the .env file.")
