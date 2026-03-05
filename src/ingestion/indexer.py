"""
Vector Store Indexer
Chunks scraped/loaded content and builds a ChromaDB vector store.
"""
import json
import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    RAW_DIR, VECTORSTORE_DIR, EMBEDDING_MODEL, OLLAMA_BASE_URL,
    CHUNK_SIZE, CHUNK_OVERLAP, WEBSITE_COLLECTION, UPLOADS_COLLECTION,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def get_embeddings() -> OllamaEmbeddings:
    """Create the Ollama embedding model instance."""
    return OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Create a text splitter tuned for multilingual content."""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", "。", "،", "؟", "!", " ", ""],
        length_function=len,
    )


def load_scraped_pages() -> list[Document]:
    """Load scraped pages from JSON and convert to LangChain Documents."""
    pages_file = RAW_DIR / "te_eg_pages.json"
    if not pages_file.exists():
        logger.error(f"Scraped data not found at {pages_file}. Run the scraper first.")
        return []

    with open(pages_file, "r", encoding="utf-8") as f:
        pages = json.load(f)

    docs = []
    for page in pages:
        if not page.get("content"):
            continue
        docs.append(Document(
            page_content=page["content"],
            metadata={
                "source": page["url"],
                "source_type": "te.eg_website",
                "title": page.get("title", ""),
                "description": page.get("description", ""),
            }
        ))

    logger.info(f"Loaded {len(docs)} documents from scraped data")
    return docs


def build_website_vectorstore(documents: list[Document] | None = None) -> Chroma:
    """Build or update the website vector store."""
    if documents is None:
        documents = load_scraped_pages()

    if not documents:
        logger.warning("No documents to index.")
        return None

    # Chunk the documents
    splitter = get_text_splitter()
    chunks = splitter.split_documents(documents)
    logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")

    # Build the vector store
    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=WEBSITE_COLLECTION,
        persist_directory=str(VECTORSTORE_DIR),
    )

    logger.info(f"Vector store built with {len(chunks)} chunks at {VECTORSTORE_DIR}")
    return vectorstore


def build_uploads_vectorstore(documents: list[Document]) -> Chroma:
    """Build or update the uploads vector store."""
    if not documents:
        logger.warning("No uploaded documents to index.")
        return None

    splitter = get_text_splitter()
    chunks = splitter.split_documents(documents)
    logger.info(f"Split uploaded docs into {len(chunks)} chunks")

    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=UPLOADS_COLLECTION,
        persist_directory=str(VECTORSTORE_DIR),
    )

    logger.info(f"Uploads vector store updated with {len(chunks)} chunks")
    return vectorstore


def load_existing_vectorstore(collection_name: str = WEBSITE_COLLECTION) -> Chroma | None:
    """Load an existing vector store from disk."""
    if not VECTORSTORE_DIR.exists():
        return None

    try:
        embeddings = get_embeddings()
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(VECTORSTORE_DIR),
        )
        # Check if collection has data
        count = vectorstore._collection.count()
        if count == 0:
            return None
        logger.info(f"Loaded vector store '{collection_name}' with {count} chunks")
        return vectorstore
    except Exception as e:
        logger.warning(f"Could not load vector store '{collection_name}': {e}")
        return None


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    logger.info("Building website vector store...")
    vs = build_website_vectorstore()
    if vs:
        count = vs._collection.count()
        logger.info(f"✅ Website vector store ready — {count} chunks indexed")
    else:
        logger.error("❌ Failed to build vector store")


if __name__ == "__main__":
    main()
