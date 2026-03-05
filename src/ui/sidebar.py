"""
Sidebar UI Component
Handles file upload, settings, and status indicators.
"""
import tempfile
import logging
from pathlib import Path

import streamlit as st

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import UPLOAD_DIR, APP_TITLE
from src.ingestion.document_loader import DocumentLoader
from src.ingestion.indexer import build_uploads_vectorstore, load_existing_vectorstore
from src.retrieval.retriever import get_retriever

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = ["pdf", "docx", "txt", "html", "png", "jpg", "jpeg"]


def render_sidebar():
    """Render the sidebar with file upload and status."""
    with st.sidebar:
        st.markdown(f"### {APP_TITLE}")
        st.markdown("---")

        # ─── System Status ────────────────────────────────────────────
        st.markdown("#### 🔌 System Status")
        _render_status()

        st.markdown("---")

        # ─── Document Upload ──────────────────────────────────────────
        st.markdown("#### 📄 Upload Documents")
        st.caption("Upload PDF, DOCX, TXT, HTML, or images to query.")

        uploaded_files = st.file_uploader(
            "Choose files",
            type=SUPPORTED_TYPES,
            accept_multiple_files=True,
            key="file_uploader",
        )

        if uploaded_files:
            if st.button("📥 Process & Index Files", type="primary", use_container_width=True):
                _process_uploads(uploaded_files)

        # Show uploaded file count
        if "uploaded_file_count" in st.session_state:
            st.success(f"✅ {st.session_state.uploaded_file_count} document(s) indexed")

        st.markdown("---")

        # ─── Chat Controls ────────────────────────────────────────────
        st.markdown("#### 💬 Chat Controls")

        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pop("chat_sources", None)
            st.rerun()

        include_uploads = st.toggle(
            "Include uploaded docs in search",
            value=True,
            key="include_uploads",
        )
        st.session_state.search_uploads = include_uploads

        st.markdown("---")

        # ─── Info ─────────────────────────────────────────────────────
        st.markdown("#### ℹ️ About")
        st.markdown("""
        **Telecom Egypt AI Assistant**
        - 🌐 Knowledge: [te.eg](https://te.eg)
        - 🗣️ Arabic, English & Egyptian dialect
        - 📄 Upload your own documents
        - 📌 Source citations included
        """)


def _render_status():
    """Show system component status."""
    from src.llm.engine import get_llm_engine

    # Check Ollama
    engine = get_llm_engine()
    if engine.is_available():
        st.markdown("✅ **Ollama:** Connected")
    else:
        st.markdown("❌ **Ollama:** Not reachable")
        st.warning("Make sure Ollama is running: `ollama serve`")

    # Check vector store
    from src.ingestion.indexer import load_existing_vectorstore
    from config.settings import WEBSITE_COLLECTION
    ws = load_existing_vectorstore(WEBSITE_COLLECTION)
    if ws:
        count = ws._collection.count()
        st.markdown(f"✅ **Knowledge Base:** {count} chunks")
    else:
        st.markdown("⚠️ **Knowledge Base:** Not built")
        st.info("Run `python3 -m src.ingestion.scraper` then `python3 -m src.ingestion.indexer`")


def _process_uploads(uploaded_files):
    """Process uploaded files and add them to the vector store."""
    loader = DocumentLoader()
    all_docs = []

    progress = st.progress(0, text="Processing files...")

    for i, uploaded_file in enumerate(uploaded_files):
        progress.progress(
            (i + 1) / len(uploaded_files),
            text=f"Processing {uploaded_file.name}...",
        )

        # Save to temp file
        suffix = Path(uploaded_file.name).suffix
        temp_path = UPLOAD_DIR / uploaded_file.name
        temp_path.write_bytes(uploaded_file.getbuffer())

        # Load and parse
        docs = loader.load(temp_path)
        all_docs.extend(docs)

    if all_docs:
        progress.progress(1.0, text="Building index...")
        build_uploads_vectorstore(all_docs)

        # Force retriever to reload
        retriever = get_retriever()
        retriever.reload_uploads()

        st.session_state.uploaded_file_count = len(uploaded_files)
        progress.empty()
        st.success(f"✅ Indexed {len(all_docs)} document(s) from {len(uploaded_files)} file(s)")
    else:
        progress.empty()
        st.warning("No text could be extracted from the uploaded files.")
