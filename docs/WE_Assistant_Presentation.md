# WE Intelligent Assistant (Telecom Egypt) — Presentation Deck

> Format: Markdown slide deck (works well in GitHub, and can be converted to PPT/PDF).

---

## 1) Title

**WE Intelligent Assistant**  
Telecom Egypt (WE) — Local, RAG-powered Customer Support Chatbot

- Runs fully locally with **Ollama**
- Answers grounded in **te.eg** website content
- Supports **Arabic + Egyptian dialect + English**

---

## 2) Problem & Motivation

Customer support teams and users face:

- Information scattered across pages and FAQs
- Repetitive questions (plans, bills, roaming, routers)
- Multilingual demand (Arabic + English, plus Egyptian dialect)

**Goal:** Provide a fast, accurate assistant that answers using *official* WE content with citations.

---

## 3) What We Built (Outcome)

A production-ready assistant that:

- Uses **RAG** (Retrieval-Augmented Generation)
- Provides **source citations** (website pages + uploaded docs)
- Lets users **upload PDFs/DOCX/TXT/HTML/images** to extend knowledge
- Runs **offline/local** (privacy-friendly)

---

## 4) Live Demo Flow (What to Show)

1. Open the Streamlit app (landing page)
2. Ask a question (Arabic / English)
3. Show:
   - Answer quality
   - **Sources** expander with links
4. Upload a PDF → ask about its content
5. Rate an answer (feedback control)

---

## 5) Architecture (High Level)

**Layers**

- **UI:** Streamlit chat app
- **Orchestrator:** conversation state + RAG pipeline
- **Domain Services:** language detection, retrieval, prompting, LLM calls
- **Data Layer:** scraper, document loader, vector store

Key principle: **clean separation** (easy to swap components).

---

## 6) System Diagram

```
User
  ↓
Streamlit UI (app.py)
  ↓
Language Detection (src/language)
  ↓
Retriever (src/retrieval)  →  ChromaDB (data/vectorstore)
  ↓
Prompt Builder (src/llm/prompts)
  ↓
LLM Engine (src/llm/engine) → Ollama (qwen3:1.7b)
  ↓
Answer + Citations
```

---

## 7) Tech Stack

- **LLM:** Ollama `qwen3:1.7b`
- **Embeddings:** Ollama `nomic-embed-text`
- **Vector DB:** ChromaDB (persistent local store)
- **Framework:** LangChain (core + chroma + ollama)
- **UI:** Streamlit (modern chat UX)
- **Scraping:** Requests + BeautifulSoup + html2text
- **Docs:** PyMuPDF, python-docx, Pillow + OCR (optional)

---

## 8) Data Ingestion: Website Knowledge Base

- BFS crawl starting from `https://te.eg`
- Rate-limited requests to be polite (avoid hammering)
- Extracts readable text (HTML → text)
- Stores raw outputs in `data/raw/`

Result: a local corpus ready for chunking and indexing.

---

## 9) Chunking & Indexing

- Chunking with `RecursiveCharacterTextSplitter`
- Defaults (from `config/settings.py`):
  - `CHUNK_SIZE = 800`
  - `CHUNK_OVERLAP = 150`
- Embeds chunks using `nomic-embed-text`
- Persists embeddings locally in **ChromaDB** (`data/vectorstore/`)

---

## 10) Retrieval (RAG)

At question time:

- Detect language style (Arabic / Egyptian / English)
- Retrieve top-K relevant chunks from:
  - WE website collection
  - Optional uploaded-docs collection
- Apply score threshold filtering

Output: *ranked context* + *sources* for citation.

---

## 11) Prompting Strategy

System rules emphasize:

- Answer **only** from provided context
- If context is missing → say you don’t know + ask clarifying Qs
- Match the **user’s language**
- Provide clear, helpful, customer-support tone

---

## 12) Multilingual & Egyptian Dialect Support

- Lightweight language detection:
  - Arabic character ratio
  - Egyptian dialect markers (مثل: "ازاي", "دلوقتي", "عايز")
- Adds a language instruction to the prompt

Why it matters:
- Better user trust
- More natural support experience

---

## 13) Document Uploads (User Knowledge)

Users can upload documents to extend knowledge:

- PDF (page-level extraction)
- DOCX
- TXT / HTML
- Images (OCR optional)

Then:
- chunk → embed → index into an uploads collection
- retrieval can include uploads when enabled

---

## 14) UI/UX Highlights

- Two-screen experience (landing → chat)
- Suggestion quick-start prompts
- Sources expander for transparency
- Feedback control to rate responses
- White + purple theme for modern look

---

## 15) Local-First & Privacy

- No external API calls required for inference
- Ollama runs on local machine
- Vector store is local

Benefits:
- Security & privacy
- Lower cost
- Works offline (once models are installed)

---

## 16) Reliability & Operations

- One-click startup:
  - `start.sh` (checks env + launches)
  - macOS `.command` launcher
- Health checks:
  - Ollama reachability
  - knowledge base exists

---

## 17) Key Files (Quick Tour)

- `app.py` — Streamlit UI + orchestration
- `config/settings.py` — all config defaults & env overrides
- `src/ingestion/scraper.py` — te.eg crawler
- `src/ingestion/indexer.py` — chunk + embed + store
- `src/retrieval/retriever.py` — retrieval logic
- `src/llm/engine.py` — ChatOllama wrapper
- `src/llm/prompts.py` — system and RAG prompts
- `.streamlit/config.toml` — theme (purple/white)

---

## 18) Risks / Limitations (Honest Notes)

- Website content can change → requires re-scrape + re-index
- Small local model (1.7B) may:
  - be less fluent for complex queries
  - need strong prompting + strict grounding
- Retrieval quality depends on chunking and coverage

---

## 19) Improvements / Next Steps

- Add hybrid retrieval (BM25 + vectors)
- Add better evaluation harness (golden Q/A + metrics)
- Add caching + streaming tokens
- Add admin page to manage corpora + re-index
- Better Arabic normalization (diacritics, Alef variants)

---

## 20) Closing

**WE Intelligent Assistant** delivers:

- Grounded answers with citations
- Multilingual, friendly customer support experience
- Fully local, privacy-first deployment

Q&A
