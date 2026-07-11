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
   - Ensure the UI reflects the most recent data ingested by the Phase 6 scheduler.

## Phase 6: Scheduler Component (Automated Daily Refresh)

**Goal:** Automate daily re-scraping and re-ingestion of the 5 Groww pages so the vector store always reflects live fund data (NAV, expense ratio, holdings, etc.) without any manual intervention.

### 6.1 Scheduler Design

The scheduler is implemented as a **GitHub Actions cron workflow** (`.github/workflows/daily_refresh.yml`). It runs fully in the cloud — no additional infrastructure, no server to maintain.

| Property | Value |
|---|---|
| **Platform** | GitHub Actions |
| **Trigger** | Cron schedule: `30 4 * * *` (04:30 UTC = 10:00 AM IST) |
| **Manual trigger** | `workflow_dispatch` (run anytime from GitHub UI) |
| **Runner** | `ubuntu-latest` (GitHub-hosted) |

### 6.2 Workflow Steps

1. **Checkout** — Clone the repository (including `vectorstore/` if committed).
2. **Setup Python 3.10** — Match the local development environment.
3. **Cache pip dependencies** — Avoid reinstalling on every run using `actions/cache`.
4. **Install dependencies** — `pip install -r requirements.txt`.
5. **Run ingestion** — `python -m src.ingest`
   - Clears existing ChromaDB entries (no duplicate chunks).
   - Scrapes all 5 Groww URLs with the session-based scraper.
   - Sanitizes unicode characters (`₹` → `INR`, etc.).
   - Embeds clean chunks and persists to ChromaDB.
6. **Commit updated vectorstore** — If the vectorstore changed, auto-commit back to `master` branch with message `chore: auto-refresh vectorstore [YYYY-MM-DD]`.

### 6.3 Secrets Required

Add these to **GitHub Repository Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `GROQ_API_KEY` | Groq Cloud API key for the LLM generation layer |
| `HF_TOKEN` | HuggingFace token (optional; increases download rate limits for BGE model) |

### 6.4 Workflow File

**Path:** `.github/workflows/daily_refresh.yml`

```yaml
name: Daily Data Refresh

on:
  schedule:
    - cron: '30 4 * * *'   # 10:00 AM IST daily
  workflow_dispatch:        # Allow manual trigger

jobs:
  refresh-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
      - run: pip install -r requirements.txt
      - name: Run ingestion pipeline
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: python -m src.ingest
      - name: Commit updated vectorstore
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add vectorstore/
          git diff --staged --quiet || git commit -m "chore: auto-refresh vectorstore [$(date +'%Y-%m-%d')]"
          git push
```

### 6.5 Integration with Ingestion Pipeline

The scheduler calls `python -m src.ingest` which in turn:

```
GitHub Actions Cron (10AM IST)
        │
        ▼
   src/ingest.py
        │
        ├── Clear existing ChromaDB entries
        ├── src/scraper.py  ──▶  Groww URLs (5 pages)
        ├── Text splitting + unicode sanitization
        ├── src/embeddings.py  ──▶  BGE embedding
        └── Persist to vectorstore/
```

### 6.6 Testing the Scheduler

1. **Manual test:** Go to the repository on GitHub → Actions → Daily Data Refresh → Run workflow.
2. **Verify:** Check the Actions run log for `Vector store successfully updated and persisted!`.
3. **Confirm commit:** A new commit `chore: auto-refresh vectorstore [YYYY-MM-DD]` should appear on `master`.
