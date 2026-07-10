# MS2 Implementation Plan — Mutual Fund FAQ Assistant

This document outlines a phase-wise implementation plan to build the Mutual Fund FAQ Assistant as defined in the `ms2_architecture.md`.

## Phase 1: Project Setup & Environment Configuration

**Goal:** Establish the project foundation, directory structure, and dependencies.

1. **Initialize Project Directory:**
   - Create the standard structure: `data/scraped_pages/`, `vectorstore/hdfc_mutual_fund_corpus/`, and `src/`.
2. **Environment & Secrets Setup:**
   - Create a `requirements.txt` with necessary libraries: `requests`, `beautifulsoup4`, `langchain`, `langchain-community`, `sentence-transformers`, `chromadb`, `groq`, `streamlit`, `python-dotenv`.
   - Setup `.env` and `.env.example` to store `GROQ_API_KEY` and other configurations (e.g., `CHROMA_PERSIST_DIR`, `BGE_MODEL_NAME`, etc.).
3. **Configuration Module (`src/config.py`):**
   - Centralize environment variables loading, URL lists, and other constants.

## Phase 2: Data Ingestion Pipeline (Offline Module)

**Goal:** Scrape the 5 Groww mutual fund pages, process the text, generate embeddings, and store them in ChromaDB.

1. **Web Scraper (`src/scraper.py`):**
   - Build a scraper using `requests` and `BeautifulSoup` to fetch HTML from the 5 specified Groww URLs.
   - Implement custom parsers to strip navigation/ads and extract relevant text sections.
2. **Data Ingestion Script (`src/ingest.py`):**
   - Implement `RecursiveCharacterTextSplitter` to split text into smaller 400 character chunks with 50 character overlap, prioritizing paragraph (`\n\n`) and newline (`\n`) separators to preserve factual isolation (e.g. keeping Exit Load separate from Expense Ratio).
   - Attach metadata to each chunk (`chunk_id`, `scheme_name`, `section`, `source_url`, `scrape_date`).
3. **Embeddings & Vector Store Setup (`src/embeddings.py`):**
   - Initialize HuggingFace embeddings using `BAAI/bge-small-en-v1.5`.
   - Setup a persistent ChromaDB collection (`hdfc_mutual_fund_corpus`).
   - Create a function to embed the text chunks and insert them into ChromaDB.
4. **Execution:** Run the ingest script to populate the local `vectorstore/`.

## Phase 3: Query Processing Layer

**Goal:** Implement pre-processing guardrails to handle PII and non-factual queries.

1. **Input Sanitization (`src/query_processor.py`):**
   - Implement regex patterns to detect PII (PAN, Aadhaar, Phone, Email, Account Numbers).
   - Return a refusal message if PII is detected.
2. **Query Classification (`src/query_processor.py`):**
   - Build a rule-based classifier using keyword matching (e.g., "should I", "recommend", "best").
   - Implement a lightweight Groq LLM fallback for ambiguous queries (Classify as `FACTUAL` or `ADVISORY`).
   - Define refusal responses for advisory queries.

## Phase 4: Core RAG Retrieval & Generation Layer

**Goal:** Retrieve relevant chunks and generate accurate, constrained answers using the Groq LLM.

1. **Retrieval Module (`src/retriever.py`):**
   - Create a retrieval function using ChromaDB similarity search (Cosine similarity).
   - Apply BGE instruction prefixing to the user's query (`Represent this sentence for searching...`).
   - Enforce retrieval parameters (`top_k=5`, `distance_threshold=0.7`).
   - Implement a context assembler to rank, deduplicate, and enforce a ~2000 token context budget.
2. **Generation Module (`src/prompts.py` & `src/generator.py`):**
   - Define the strict System Prompt in `src/prompts.py` enforcing the 3-sentence rule, facts-only constraint, and citation requirement.
   - Integrate with the Groq API (`llama-3.3-70b-versatile`) with a low temperature (0.1).
   - Implement a `format_response` post-processing function to validate citation links, sentence count, and append the "Last updated" footer.
3. **RAG Orchestration (`src/rag_chain.py`):**
   - Create the end-to-end pipeline that ties together `query_processor.py`, `retriever.py`, and `generator.py`.

## Phase 5: User Interface (Streamlit)

**Goal:** Build the single-page chat interface for user interaction.

1. **UI Layout (`app.py`):**
   - Setup the Streamlit application with standard configuration.
   - Add the disclaimer banner ("Facts-only. No investment advice").
   - Populate the sidebar or welcome message with example queries.
2. **Chat Integration:**
   - Use `st.chat_input` and `st.chat_message` to build the conversational flow.
   - Wire the chat input to the orchestrator (`src/rag_chain.py`).
   - Display the formatted response (including citations and footers).
3. **Testing:**
   - Test end-to-end flows with both factual queries, advisory (refused) queries, and queries with PII.
