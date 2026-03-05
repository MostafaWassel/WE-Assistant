"""
Telecom Egypt Intelligent Assistant — Central Configuration
"""
import os
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
ASSETS_DIR = PROJECT_ROOT / "assets"
UPLOAD_DIR = DATA_DIR / "uploads"

# Create directories on import
for d in [RAW_DIR, PROCESSED_DIR, VECTORSTORE_DIR, ASSETS_DIR, UPLOAD_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Ollama Configuration ────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3:1.7b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# ─── Scraping Configuration ──────────────────────────────────────────────────
TARGET_URL = "https://te.eg"
SCRAPE_MAX_PAGES = int(os.getenv("SCRAPE_MAX_PAGES", "100"))
SCRAPE_DELAY = float(os.getenv("SCRAPE_DELAY", "1.5"))  # seconds between requests
SCRAPE_TIMEOUT = int(os.getenv("SCRAPE_TIMEOUT", "15"))

# ─── Chunking Configuration ──────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# ─── Retrieval Configuration ─────────────────────────────────────────────────
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
RETRIEVAL_SCORE_THRESHOLD = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.3"))

# ─── Collection Names ────────────────────────────────────────────────────────
WEBSITE_COLLECTION = "te_eg_website"
UPLOADS_COLLECTION = "user_uploads"

# ─── UI Configuration ────────────────────────────────────────────────────────
APP_TITLE = "🇪🇬 Telecom Egypt Intelligent Assistant"
APP_ICON = "🇪🇬"
ASSISTANT_AVATAR = "🤖"
USER_AVATAR = "👤"
