# HDFC Mutual Fund FAQ Assistant — RAG Chatbot

A **facts-only Retrieval-Augmented Generation (RAG)** chatbot that answers questions about 5 HDFC Mutual Fund schemes using live data scraped daily from [Groww](https://groww.in).

> ⚠️ This assistant provides factual information only. It does **not** offer investment advice.

---

## 🚀 Live Demo

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hdfc-mf-faq-rag.streamlit.app)

---

## 📦 Funds Covered

| Fund | Source |
|------|--------|
| HDFC Silver ETF FoF Direct Growth | [Groww](https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth) |
| HDFC Mid Cap Fund Direct Growth | [Groww](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth) |
| HDFC Equity Fund Direct Growth | [Groww](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth) |
| HDFC Defence Fund Direct Growth | [Groww](https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth) |
| HDFC Gold ETF Fund of Fund Direct Growth | [Groww](https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth) |

---

## 🏗️ Architecture

```
GitHub Actions (10:30 AM IST daily)
        │
        ▼
  src/ingest.py ──▶ Groww Scraper ──▶ BGE Embeddings ──▶ ChromaDB
                                                              │
User Query ──▶ Query Processor ──▶ Smart Retriever ──▶ Groq LLM ──▶ Response
```

- **LLM:** Groq `llama-3.3-70b-versatile`
- **Embeddings:** `BAAI/bge-small-en-v1.5` (local, 384-dim)
- **Vector Store:** ChromaDB (persistent)
- **Scheduler:** GitHub Actions cron (`0 5 * * *` = 10:30 AM IST)

---

## ⚙️ Local Setup

```bash
git clone https://github.com/map-sketch/hdfc-mf-faq-rag.git
cd hdfc-mf-faq-rag

pip install -r requirements.txt

cp .env.example .env
# Edit .env and set your GROQ_API_KEY

python -m src.ingest       # Populate the vector store
streamlit run app.py       # Start the UI
```

---

## ☁️ Streamlit Cloud Deployment

1. **Fork** or connect this repo to [Streamlit Cloud](https://share.streamlit.io)
2. Set **Main file path** to `app.py`
3. Go to **App Settings → Secrets** and paste:

```toml
GROQ_API_KEY = "gsk_your_key_here"
CHROMA_PERSIST_DIR = "./vectorstore"
COLLECTION_NAME = "hdfc_mutual_fund_corpus"
BGE_MODEL_NAME = "BAAI/bge-small-en-v1.5"
GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
RETRIEVAL_TOP_K = "5"
RETRIEVAL_SCORE_THRESHOLD = "0.2"
```

4. Deploy — on first boot the app **auto-ingests** all 5 fund pages into ChromaDB.

---

## 🔄 Automated Daily Refresh

A GitHub Actions workflow (`.github/workflows/daily_refresh.yml`) runs at **10:30 AM IST** every day to:
- Scrape fresh data from all 5 Groww pages
- Re-embed and update ChromaDB
- Auto-commit the updated vectorstore back to `master`

Add `GROQ_API_KEY` (and optionally `HF_TOKEN`) to your **GitHub Repository Secrets** to enable this.

---

## 📁 Project Structure

```
├── app.py                          # Streamlit UI entry point
├── requirements.txt
├── .env.example
├── .github/workflows/
│   └── daily_refresh.yml          # GitHub Actions scheduler
├── src/
│   ├── config.py                  # Env vars + Groww URLs
│   ├── scraper.py                 # Web scraper (session-based, gzip)
│   ├── ingest.py                  # Ingestion: scrape → chunk → embed → store
│   ├── embeddings.py              # BGE embedding wrapper
│   ├── retriever.py               # Smart retriever (key-facts + multi-fund)
│   ├── query_processor.py         # PII detection + advisory classifier
│   ├── generator.py               # Groq LLM + response formatter
│   ├── rag_chain.py               # End-to-end orchestration
│   └── prompts.py                 # System prompt templates
└── vectorstore/                   # ChromaDB (auto-populated)
```
