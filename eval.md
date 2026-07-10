# MS2 — Evaluation Plan (eval.md)

This document provides a phase-wise evaluation checklist to ensure each component of the Mutual Fund FAQ Assistant is implemented correctly and meets the specifications defined in `ms2_implementationplan.md`.

## Phase 1: Project Setup & Environment Configuration
- [ ] **Directory Structure:** Are `data/scraped_pages/`, `vectorstore/hdfc_mutual_fund_corpus/`, and `src/` directories successfully created?
- [ ] **Dependencies:** Can the project run `pip install -r requirements.txt` without dependency conflicts?
- [ ] **Environment Variables:** Does the system gracefully fail with clear error messages if `.env` (e.g., `GROQ_API_KEY`, `CHROMA_PERSIST_DIR`) is missing?
- [ ] **Configuration Import:** Can `src/config.py` successfully load and expose all environment variables?

## Phase 2: Data Ingestion Pipeline (Offline Module)
- [ ] **Scraping Completeness:** Does `src/scraper.py` successfully fetch content from all 5 specified Groww URLs?
- [ ] **Content Extraction:** Are navigation elements and ads successfully stripped out, leaving only relevant content?
- [ ] **Chunking Verification:** Does the `RecursiveCharacterTextSplitter` correctly split text (are chunks roughly 500-800 tokens, with ~100 token overlaps)?
- [ ] **Metadata Accuracy:** Does each chunk in the vector store have accurate metadata (`chunk_id`, `scheme_name`, `section`, `source_url`, `scrape_date`)?
- [ ] **Embeddings Generation:** Does the BGE model (`BAAI/bge-small-en-v1.5`) successfully generate vectors (dimension 384) for the chunks?
- [ ] **Vector Persistence:** Is the ChromaDB collection `hdfc_mutual_fund_corpus` correctly saved to the disk in the `vectorstore/` directory?

## Phase 3: Query Processing Layer
- [ ] **PII Detection (PAN/Aadhaar/Phone):** Does the sanitizer successfully detect and block inputs like "My PAN is ABCDE1234F" or phone numbers?
- [ ] **PII Rejection Response:** Does the system return the expected refusal message without passing the query to the LLM when PII is detected?
- [ ] **Advisory Rule-based Rejection:** Does the system immediately block queries containing keywords like "recommend", "should I invest", or "best fund"?
- [ ] **Advisory LLM Rejection:** Do ambiguous advisory queries (e.g., "Is it a good idea to put my money here?") trigger the LLM fallback and get successfully flagged as `ADVISORY`?

## Phase 4: Core RAG Retrieval & Generation Layer
- [ ] **Retrieval Strategy:** Does querying ChromaDB with the BGE instruction prefix return the expected `top_k=5` chunks above the `0.7` distance threshold?
- [ ] **Context Assembly:** Is the context deduplicated, ranked properly, and within the 2000-token budget?
- [ ] **System Prompt Compliance:** Does the generated Groq LLM response adhere strictly to the rules (e.g., facts-only, no investment advice)?
- [ ] **Constraint: Sentence Limit:** Does the output always contain exactly 3 sentences or fewer? (Verified by the Response Formatter).
- [ ] **Constraint: Citations:** Does every response include exactly one valid citation link derived from the chunk metadata?
- [ ] **Constraint: Footer:** Does every response end with "Last updated from sources: <date>"?
- [ ] **Out-of-Scope Queries:** For unrelated queries, does the system successfully output "I don't have this information in my current sources"?

## Phase 5: User Interface (Streamlit)
- [ ] **UI Rendering:** Does `app.py` successfully render the chat interface, disclaimer banner, and example queries?
- [ ] **Session State:** Can a user send a message and see both their input and the assistant's response properly formatted in the chat UI?
- [ ] **End-to-End Latency:** Is the response time generally acceptable for a chat interface?
- [ ] **Error Handling:** Does the UI gracefully handle backend errors (e.g., API limits, missing vectorstore) and display helpful error messages?
