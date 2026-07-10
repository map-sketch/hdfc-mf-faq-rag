# MS2 — System Architecture: Mutual Fund FAQ Assistant (RAG)

## 1. Architecture Overview

This document describes the end-to-end system architecture for the **Mutual Fund FAQ Assistant** — a Retrieval-Augmented Generation (RAG) chatbot that answers facts-only queries about HDFC Mutual Fund schemes using data scraped exclusively from the Groww website.

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                │
│                         (Streamlit / Gradio App)                           │
│  ┌─────────────┐  ┌──────────────────┐  ┌─────────────────────────────┐   │
│  │ Welcome Msg  │  │ Example Queries  │  │ Disclaimer Banner           │   │
│  └─────────────┘  └──────────────────┘  │ "Facts-only. No investment  │   │
│                                          │  advice."                   │   │
│  ┌──────────────────────────────────┐    └─────────────────────────────┘   │
│  │        Chat Input Box           │                                      │
│  └──────────────┬───────────────────┘                                     │
└─────────────────┼───────────────────────────────────────────────────────────┘
                  │ User Query
                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          QUERY PROCESSING LAYER                            │
│                                                                            │
│  ┌──────────────────┐    ┌──────────────────────┐                          │
│  │  Input Sanitizer  │──▶│  Query Classifier     │                         │
│  │  (PII Detection)  │    │  (Factual / Advisory) │                        │
│  └──────────────────┘    └──────────┬─────────────┘                        │
│                                     │                                      │
│                          ┌──────────┴──────────┐                           │
│                          │                     │                           │
│                     [FACTUAL]            [ADVISORY/REFUSED]                │
│                          │                     │                           │
│                          ▼                     ▼                           │
│                   Continue to RAG     Return Refusal Response              │
│                                       + Educational Link                  │
└─────────────────┬───────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RETRIEVAL LAYER (RAG Core)                        │
│                                                                            │
│  ┌──────────────────┐    ┌──────────────────────────────────┐              │
│  │  BGE Embedding    │──▶│  Vector Store (ChromaDB / FAISS) │              │
│  │  (HuggingFace)    │    │  - HDFC Silver ETF FoF page      │             │
│  │                   │    │  - HDFC Mid Cap Fund page         │             │
│  │  Model:           │    │  - HDFC Flexi Cap Fund page       │             │
│  │  BAAI/bge-small-  │    │  - HDFC Defence Fund page         │             │
│  │  en-v1.5          │    │  - HDFC Gold ETF FoF page          │            │
│  └──────────────────┘    └──────────────┬────────────────────┘             │
│                                          │                                 │
│                                          │ Top-K Relevant Chunks           │
│                                          ▼                                 │
│                          ┌──────────────────────────────────┐              │
│                          │  Context Assembler                │              │
│                          │  - Rank & deduplicate chunks      │              │
│                          │  - Attach source metadata         │              │
│                          │  - Enforce chunk budget            │              │
│                          └──────────────┬───────────────────┘              │
└─────────────────────────────────────────┼──────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GENERATION LAYER                                  │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                        Groq LLM API                              │      │
│  │  Model: llama-3.3-70b-versatile (or mixtral-8x7b-32768)         │      │
│  │                                                                  │      │
│  │  System Prompt enforces:                                         │      │
│  │  ✓ Max 3 sentences                                               │      │
│  │  ✓ Exactly 1 citation link                                       │      │
│  │  ✓ "Last updated from sources: <date>" footer                    │      │
│  │  ✓ No investment advice                                          │      │
│  └──────────────────────────────────┬───────────────────────────────┘      │
│                                     │                                      │
│                                     ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                   Response Formatter                              │      │
│  │  - Validate citation presence                                    │      │
│  │  - Append footer with last-updated date                          │      │
│  │  - Truncate if exceeding 3-sentence limit                        │      │
│  └──────────────────────────────────┬───────────────────────────────┘      │
└─────────────────────────────────────┼──────────────────────────────────────┘
                                      │
                                      ▼
                              Final Response to User
```

---

## 2. Component Breakdown

### 2.1 Data Ingestion Pipeline

The ingestion pipeline is an **offline, one-time process** (re-run when corpus is updated) that scrapes the 5 Groww scheme pages, converts the extracted HTML content into text chunks, embeds them, and stores them in the vector database.

**Data Sources (Groww URLs only):**

| # | Scheme | Groww URL |
|---|--------|-----------|
| 1 | HDFC Silver ETF FoF Direct Growth | `https://groww.in/mutual-funds/hdfc-silver-etf-fund-of-fund-direct-growth` |
| 2 | HDFC Mid Cap Fund Direct Growth | `https://groww.in/mutual-funds/hdfc-mid-cap-opportunities-fund-direct-plan-growth` |
| 3 | HDFC Flexi Cap Direct Plan Growth | `https://groww.in/mutual-funds/hdfc-flexi-cap-fund-direct-plan-growth` |
| 4 | HDFC Defence Fund Direct Growth | `https://groww.in/mutual-funds/hdfc-defence-fund-direct-plan-growth` |
| 5 | HDFC Gold ETF Fund of Fund Direct Plan Growth | `https://groww.in/mutual-funds/hdfc-gold-fund-direct-plan-growth` |

```
Groww URLs ──▶ Web Scraper ──▶ Text Splitter ──▶ BGE Embedder ──▶ Vector Store
  (5 scheme       (requests +      (Recursive        (BAAI/bge-       (ChromaDB)
   pages)         BeautifulSoup)    Character          small-en-v1.5)
                                    Splitter)
```

| Step | Component | Details |
|------|-----------|---------|
| **1. Web Scraping** | `requests` + `BeautifulSoup` | Fetch and parse HTML from the 5 Groww scheme URLs; extract structured text (NAV, expense ratio, exit load, holdings, peer comparison, etc.) |
| **2. Text Cleaning** | Custom parser | Strip navigation, ads, and boilerplate HTML; retain only scheme-relevant content sections |
| **3. Text Splitting** | `RecursiveCharacterTextSplitter` | Split into chunks of ~500–800 tokens with ~100 token overlap to preserve context boundaries |
| **4. Metadata Tagging** | Custom tagger | Attach metadata to each chunk: `source_url`, `scheme_name`, `section`, `scrape_date` |
| **5. Embedding** | `BAAI/bge-small-en-v1.5` (HuggingFace) | Generate 384-dimensional dense vectors for each chunk |
| **6. Storage** | ChromaDB (persistent mode) | Store embeddings + metadata on disk for retrieval at query time |

#### Chunk Metadata Schema

```json
{
  "chunk_id": "hdfc_midcap_groww_chunk_012",
  "text": "The exit load for HDFC Mid Cap Fund is 1% if redeemed within 1 year...",
  "scheme_name": "HDFC Mid Cap Fund Direct Growth",
  "section": "exit_load",
  "source_url": "https://groww.in/mutual-funds/hdfc-mid-cap-opportunities-fund-direct-plan-growth",
  "scrape_date": "2026-06-15"
}
```

---

### 2.2 Embedding Model — BGE (BAAI General Embedding)

| Property | Value |
|----------|-------|
| **Model** | `BAAI/bge-small-en-v1.5` |
| **Provider** | Hugging Face (`sentence-transformers`) |
| **Embedding Dimension** | 384 |
| **Max Sequence Length** | 512 tokens |
| **Why BGE?** | Strong performance on MTEB benchmark, lightweight, runs locally without API costs, supports query-instruction prefixing for better retrieval |

**Query Prefixing (BGE-specific):**

BGE models perform better when queries are prefixed with an instruction:

```python
query = "Represent this sentence for searching relevant passages: What is the exit load for HDFC Mid Cap Fund?"
```

This prefix is applied **only at query time**, not during document embedding.

---

### 2.3 Vector Store — ChromaDB

| Property | Value |
|----------|-------|
| **Database** | ChromaDB |
| **Mode** | Persistent (on-disk) |
| **Distance Metric** | Cosine similarity |
| **Collection Name** | `hdfc_mutual_fund_corpus` |

**Why ChromaDB?**
- Lightweight, no external server needed
- Built-in metadata filtering (filter by `scheme_name`, `document_type`)
- Native Python integration with LangChain
- Persistent storage across sessions

**Alternative considered:** FAISS — faster for large-scale search but lacks built-in metadata filtering. ChromaDB is preferred for this project's scale (~500–2000 chunks).

---

### 2.4 Query Processing Layer

This layer sits between the user input and the RAG retrieval pipeline. It handles two critical tasks:

#### 2.4.1 Input Sanitizer (PII Detection)

```python
# Regex-based PII detection patterns
PII_PATTERNS = {
    "PAN":      r"[A-Z]{5}[0-9]{4}[A-Z]",
    "Aadhaar":  r"\d{4}\s?\d{4}\s?\d{4}",
    "Phone":    r"(\+91[\-\s]?)?[6-9]\d{9}",
    "Email":    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "Account":  r"\d{9,18}"
}
```

If PII is detected, the system returns a **refusal message** without forwarding the query to the LLM:

> *"I cannot process queries containing personal information (PAN, Aadhaar, phone numbers, etc.). Please remove any personal details and try again."*

#### 2.4.2 Query Classifier (Factual vs. Advisory)

A lightweight classification step determines whether the user's query is **factual** (answerable) or **advisory** (must be refused).

**Approach: Keyword + LLM-based classification**

| Method | Description |
|--------|-------------|
| **Rule-based (primary)** | Flag queries containing keywords: *"should I"*, *"recommend"*, *"better"*, *"best"*, *"worth it"*, *"good investment"*, *"predict"*, *"will it grow"* |
| **LLM fallback** | If rule-based is uncertain, use a short Groq prompt to classify: `"Is this query asking for factual information or investment advice? Reply FACTUAL or ADVISORY."` |

**Refusal Response Template:**

> *"I can only provide factual information about mutual fund schemes. For investment advice, please consult a registered financial advisor. You may find helpful resources at [AMFI](https://www.amfiindia.com/) or [SEBI Investor Education](https://investor.sebi.gov.in/)."*

---

### 2.5 Retrieval Layer

The retrieval layer converts the user's query into an embedding, searches the vector store, and assembles the context for the LLM.

#### Retrieval Flow

```
User Query
    │
    ▼
BGE Embed Query (with instruction prefix)
    │
    ▼
ChromaDB Similarity Search
    │  Parameters:
    │  - top_k = 5
    │  - distance threshold = 0.7 (cosine)
    │  - optional metadata filter (scheme_name)
    │
    ▼
Retrieved Chunks (with metadata)
    │
    ▼
Context Assembler
    │  - Deduplicate near-identical chunks
    │  - Rank by relevance score
    │  - Cap total context at ~2000 tokens
    │  - Preserve source_url metadata
    │
    ▼
Context Window (ready for LLM)
```

#### Retrieval Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `top_k` | 5 | Balance between coverage and noise; mutual fund facts are usually concentrated in 2–3 chunks |
| `distance_threshold` | 0.7 | Filter out low-relevance results to prevent hallucination |
| `context_budget` | ~2000 tokens | Leave room for system prompt + response within Groq's context window |

---

### 2.6 Generation Layer — Groq LLM

| Property | Value |
|----------|-------|
| **Provider** | Groq Cloud API |
| **Model** | `llama-3.3-70b-versatile` (primary) / `mixtral-8x7b-32768` (fallback) |
| **Temperature** | 0.1 (near-deterministic for factual accuracy) |
| **Max Output Tokens** | 256 |
| **Context Window** | 128K tokens (llama-3.3-70b) |

**Why Groq?**
- Extremely fast inference (~10x faster than standard cloud LLMs) via custom LPU hardware
- Low latency is critical for a FAQ chatbot experience
- Supports large context windows for RAG
- Free tier available for development

#### System Prompt

```text
You are a facts-only mutual fund FAQ assistant. You answer questions about 
HDFC Mutual Fund schemes using ONLY the provided context.

STRICT RULES:
1. Answer in a MAXIMUM of 3 sentences.
2. Include EXACTLY ONE source citation link from the context metadata.
3. End every response with: "Last updated from sources: <date>"
4. NEVER provide investment advice, recommendations, or opinions.
5. NEVER compare fund performance or predict returns.
6. If the context does not contain the answer, say: 
   "I don't have this information in my current sources. 
    Please check the official HDFC Mutual Fund website."
7. For performance-related queries, provide the official factsheet link only.

CONTEXT:
{retrieved_context}

USER QUERY:
{user_query}
```

#### Response Formatter

After the LLM generates a response, a post-processing step ensures compliance:

```python
def format_response(llm_output, source_metadata):
    # 1. Validate sentence count (≤ 3)
    sentences = split_sentences(llm_output)
    if len(sentences) > 3:
        llm_output = ". ".join(sentences[:3]) + "."
    
    # 2. Ensure citation link is present
    if not contains_url(llm_output):
        llm_output += f"\nSource: {source_metadata['source_url']}"
    
    # 3. Append footer
    llm_output += f"\n\nLast updated from sources: {source_metadata['last_updated']}"
    
    return llm_output
```

---

### 2.7 User Interface Layer

| Property | Value |
|----------|-------|
| **Framework** | Streamlit (primary) or Gradio |
| **Layout** | Single-page chat interface |
| **Deployment** | Local / Streamlit Cloud |

#### UI Components

```
┌──────────────────────────────────────────────────────┐
│  🏦 Mutual Fund FAQ Assistant                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                      │
│  ⚠️ Facts-only. No investment advice.                │
│                                                      │
│  Welcome! I can help you with factual information    │
│  about HDFC Mutual Fund schemes. Try asking:         │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │ 💡 "What is the expense ratio of HDFC Mid Cap  │  │
│  │     Fund Direct Growth?"                       │  │
│  │ 💡 "What is the exit load for HDFC Flexi Cap?" │  │
│  │ 💡 "What is the minimum SIP amount for HDFC    │  │
│  │     Defence Fund?"                             │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │ 🧑 What is the benchmark index for HDFC Mid    │  │
│  │    Cap Fund?                                   │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │ 🤖 The benchmark index for HDFC Mid Cap Fund   │  │
│  │    Direct Growth is NIFTY Midcap 150 TRI.      │  │
│  │    Source: https://groww.in/mutual-funds/...    │  │
│  │                                                │  │
│  │    Last updated from sources: 2026-06-15       │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────────────────────┐ ┌──────────┐  │
│  │ Type your question...            │ │  Send ▶  │  │
│  └──────────────────────────────────┘ └──────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack Summary

| Layer | Technology | Version / Model | Purpose |
|-------|-----------|-----------------|---------|
| **LLM** | Groq API | `llama-3.3-70b-versatile` | Answer generation |
| **Embeddings** | BGE (HuggingFace) | `BAAI/bge-small-en-v1.5` | Semantic search embeddings |
| **Vector Store** | ChromaDB | latest | Persistent vector storage + metadata filtering |
| **Orchestration** | LangChain | latest | RAG pipeline orchestration |
| **Web Scraping** | requests, BeautifulSoup | latest | Groww page scraping & HTML parsing |
| **UI** | Streamlit | latest | Chat interface |
| **Language** | Python | 3.10+ | Core development language |
| **Environment** | python-dotenv | latest | Secrets management (API keys) |

---

## 4. Project Directory Structure

```
RAG/
├── problem_statement.md          # Project requirements
├── ms2_architecture.md           # This document
├── README.md                     # Setup & usage instructions
│
├── data/                         # Scraped corpus data
│   └── scraped_pages/            # Raw HTML / text scraped from Groww URLs
│
├── vectorstore/                  # Persisted ChromaDB data
│   └── hdfc_mutual_fund_corpus/
│
├── src/                          # Source code
│   ├── __init__.py
│   ├── config.py                 # Configuration constants
│   ├── scraper.py                # Groww URL scraping logic
│   ├── ingest.py                 # Data ingestion pipeline (scrape → chunk → embed → store)
│   ├── embeddings.py             # BGE embedding wrapper
│   ├── retriever.py              # Vector store retrieval logic
│   ├── query_processor.py        # PII detection + query classification
│   ├── generator.py              # Groq LLM integration + response formatting
│   ├── rag_chain.py              # End-to-end RAG chain orchestration
│   └── prompts.py                # System prompt templates
│
├── app.py                        # Streamlit UI entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Template for environment variables
└── .gitignore
```

---

## 5. Data Flow — End-to-End Query Lifecycle

```
Step 1: User types query in Streamlit chat input
         │
Step 2: Input Sanitizer checks for PII (regex-based)
         │── PII found → Return refusal, STOP
         │
Step 3: Query Classifier determines intent
         │── Advisory → Return refusal + AMFI/SEBI link, STOP
         │
Step 4: BGE model embeds the query (with instruction prefix)
         │
Step 5: ChromaDB similarity search retrieves top-5 chunks
         │── No relevant chunks (all below threshold) → "I don't have this info", STOP
         │
Step 6: Context Assembler deduplicates, ranks, and caps at ~2000 tokens
         │
Step 7: System prompt + context + query sent to Groq LLM
         │
Step 8: LLM generates factual response (≤ 3 sentences)
         │
Step 9: Response Formatter validates citation, appends footer
         │
Step 10: Final response displayed in Streamlit chat
```

---

## 6. Environment Variables

```bash
# .env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxx
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxx        # Optional, for gated models
CHROMA_PERSIST_DIR=./vectorstore
COLLECTION_NAME=hdfc_mutual_fund_corpus
BGE_MODEL_NAME=BAAI/bge-small-en-v1.5
GROQ_MODEL_NAME=llama-3.3-70b-versatile
RETRIEVAL_TOP_K=5
RETRIEVAL_SCORE_THRESHOLD=0.7
```

---

## 7. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Embedding model** | BGE-small (local) over OpenAI Ada | No API cost, runs locally, strong MTEB performance, data stays private |
| **LLM provider** | Groq over OpenAI/Anthropic | Ultra-low latency (<500ms), free tier for development, open-source model support |
| **Vector store** | ChromaDB over Pinecone/FAISS | Metadata filtering, persistent storage, zero infrastructure, LangChain native |
| **Data source** | Groww web pages only | Single authoritative source; no PDFs or multi-format parsing complexity; easy to re-scrape |
| **Chunking strategy** | Recursive character (500–800 tokens) | Groww pages have clear section boundaries; moderate chunk size balances precision and context |
| **Temperature** | 0.1 | Near-zero to minimize hallucination for factual Q&A |
| **Classification** | Rule-based + LLM fallback | Fast for obvious cases; LLM handles edge cases without over-engineering |

---

## 8. Guardrails & Compliance

| Guardrail | Implementation |
|-----------|---------------|
| **No investment advice** | System prompt enforcement + query classifier pre-filter |
| **PII protection** | Regex-based input sanitizer blocks PAN, Aadhaar, phone, email, account numbers |
| **Source transparency** | Every response includes exactly one citation URL + last-updated date |
| **Response length** | Post-processing enforces ≤ 3 sentence limit |
| **Hallucination mitigation** | Low temperature (0.1), retrieval threshold filtering, "I don't know" fallback |
| **Official sources only** | Corpus scraped exclusively from the 5 Groww scheme URLs listed in the problem statement |

---

## 9. Limitations & Future Scope

### Known Limitations

- **Static corpus**: Data does not auto-update; NAV and page content changes on Groww require manual re-scraping and re-ingestion
- **Single AMC**: Limited to HDFC Mutual Fund (5 schemes); not multi-AMC
- **English only**: No multi-language support
- **No conversation memory**: Each query is independent (no multi-turn context)
- **No authentication**: Open access, no user session management

### Future Enhancements

| Enhancement | Description |
|-------------|-------------|
| **Automated ingestion** | Scheduled re-scraping of Groww URLs to keep corpus current |
| **Multi-AMC support** | Expand corpus to SBI, ICICI Prudential, Axis, etc. |
| **Conversation memory** | Add session-based context for follow-up questions |
| **Evaluation framework** | RAGAS-based evaluation (faithfulness, answer relevancy, context precision) |
| **Caching** | Cache frequent queries to reduce Groq API calls |
| **Multilingual** | Hindi and regional language support via multilingual embeddings |
