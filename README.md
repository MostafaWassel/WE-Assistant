# 🇪🇬 WE-CHB — Telecom Egypt Intelligent Assistant

A production-ready **RAG-powered chatbot** for Telecom Egypt (WE) that answers customer queries using the official website as its primary knowledge base. Supports **Arabic, English, and Egyptian dialect**, with document upload capabilities.

> UI inspired by [streamlit/demo-ai-assistant](https://github.com/streamlit/demo-ai-assistant)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│              Streamlit UI (Chat + Upload)            │
│   Landing screen → Suggestions → Chat → Feedback    │
├─────────────────────────────────────────────────────┤
│              RAG Orchestrator Pipeline               │
│   Language Detection → Retrieval → Prompt → LLM     │
├──────────────┬──────────────┬───────────────────────┤
│  Web Scraper │  Doc Loader  │   Vector Store        │
│  (te.eg)     │  (PDF/DOCX/  │   (ChromaDB)          │
│              │   TXT/HTML/  │                       │
│              │   Images)    │                       │
├──────────────┴──────────────┴───────────────────────┤
│              Embedding Engine                        │
│         (nomic-embed-text via Ollama)                │
├─────────────────────────────────────────────────────┤
│                LLM Engine                            │
│            (qwen3:1.7b via Ollama)                   │
└─────────────────────────────────────────────────────┘
```

## 📦 Tech Stack

| Component        | Technology                    |
|-----------------|-------------------------------|
| LLM             | Ollama — qwen3:1.7b           |
| Embeddings      | Ollama — nomic-embed-text     |
| Vector Store    | ChromaDB                      |
| Framework       | LangChain                     |
| UI              | Streamlit                     |
| Web Scraping    | BeautifulSoup + Requests      |
| Doc Processing  | PyMuPDF, python-docx, Pillow  |
| OCR             | Tesseract (optional)          |

## 🚀 Quick Start (One Click)

### Option A: Double-click launcher (macOS)

1. Double-click **`Launch WE Assistant.command`** in Finder
2. It will auto-check everything and open the app in your browser

### Option B: Terminal

```bash
./start.sh
```

The start script automatically:
- ✅ Checks & starts Ollama
- ✅ Pulls required AI models
- ✅ Creates virtual environment & installs dependencies
- ✅ Scrapes te.eg if needed
- ✅ Builds vector store if needed
- ✅ Launches the app & opens browser

### Option C: Manual Setup

```bash
# 1. Prerequisites — Install Ollama and pull models
ollama pull qwen3:1.7b
ollama pull nomic-embed-text

# 2. Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Scrape the knowledge base
python3 -m src.ingestion.scraper

# 4. Build the vector store
python3 -m src.ingestion.indexer

# 5. Launch
streamlit run app.py
```

## ✨ Features

- 🌐 **RAG from te.eg** — Answers grounded in official website content
- 🗣️ **Multilingual** — Arabic (MSA), Egyptian dialect, English
- 📄 **Document Upload** — PDF, DOCX, TXT, HTML, Images (OCR)
- 📌 **Source Citations** — Every answer links back to its source
- ⭐ **Feedback System** — Rate each response
- 🔒 **Fully Local** — Nothing leaves your machine (Ollama)
- 💡 **Suggestion Pills** — Quick-start example questions
- 🎨 **Professional UI** — Clean, modern chat interface

## 📁 Project Structure

```
WE-CHB/
├── app.py                          # Streamlit entry point
├── start.sh                        # CLI start script
├── Launch WE Assistant.command     # macOS double-click launcher
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── config.toml                 # Streamlit theme & config
├── config/
│   └── settings.py                 # Central configuration
├── src/
│   ├── ingestion/
│   │   ├── scraper.py              # te.eg website crawler
│   │   ├── indexer.py              # ChromaDB vector store builder
│   │   └── document_loader.py      # Multi-format document loader
│   ├── retrieval/
│   │   └── retriever.py            # RAG retrieval engine
│   ├── llm/
│   │   ├── engine.py               # Ollama LLM wrapper
│   │   └── prompts.py              # Prompt templates
│   ├── language/
│   │   └── detector.py             # Arabic/English/Egyptian detector
│   └── ui/
│       ├── chat.py                 # (legacy) Chat component
│       └── sidebar.py              # (legacy) Sidebar component
├── data/
│   ├── raw/                        # Scraped website JSON
│   ├── vectorstore/                # ChromaDB persistence
│   └── uploads/                    # User-uploaded files
└── assets/
```

## 🔧 Configuration

All settings are in `config/settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_MODEL` | `qwen3:1.7b` | Ollama LLM model |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |
| `SCRAPE_MAX_PAGES` | `100` | Max pages to crawl |
| `CHUNK_SIZE` | `800` | Text chunk size |
| `CHUNK_OVERLAP` | `150` | Chunk overlap |
| `RETRIEVAL_TOP_K` | `5` | Top results to retrieve |

Override with environment variables:
```bash
LLM_MODEL=mistral SCRAPE_MAX_PAGES=200 streamlit run app.py
```

