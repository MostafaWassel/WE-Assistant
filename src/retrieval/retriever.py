"""
RAG Retrieval Engine
Retrieves relevant context from vector stores and formats it for the LLM.
"""
import logging
from pathlib import Path

from langchain_chroma import Chroma

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    VECTORSTORE_DIR, WEBSITE_COLLECTION, UPLOADS_COLLECTION,
    RETRIEVAL_TOP_K, RETRIEVAL_SCORE_THRESHOLD,
)
from src.ingestion.indexer import get_embeddings

logger = logging.getLogger(__name__)


class Retriever:
    """RAG retriever that searches website and upload vector stores."""

    def __init__(self):
        self._website_store: Chroma | None = None
        self._uploads_store: Chroma | None = None
        self._embeddings = get_embeddings()

    def _load_store(self, collection_name: str) -> Chroma | None:
        """Load a ChromaDB collection."""
        try:
            store = Chroma(
                collection_name=collection_name,
                embedding_function=self._embeddings,
                persist_directory=str(VECTORSTORE_DIR),
            )
            count = store._collection.count()
            if count > 0:
                logger.info(f"Loaded '{collection_name}' with {count} chunks")
                return store
            return None
        except Exception as e:
            logger.warning(f"Could not load '{collection_name}': {e}")
            return None

    @property
    def website_store(self) -> Chroma | None:
        if self._website_store is None:
            self._website_store = self._load_store(WEBSITE_COLLECTION)
        return self._website_store

    @property
    def uploads_store(self) -> Chroma | None:
        if self._uploads_store is None:
            self._uploads_store = self._load_store(UPLOADS_COLLECTION)
        return self._uploads_store

    def reload_uploads(self):
        """Force reload of uploads store (after new documents are added)."""
        self._uploads_store = None

    def search(
        self,
        query: str,
        include_uploads: bool = True,
        top_k: int = RETRIEVAL_TOP_K,
    ) -> list[dict]:
        """
        Search vector stores for relevant context.

        Returns:
            List of dicts with keys: content, source, source_type, title, score
        """
        results = []

        # Search website knowledge base
        if self.website_store:
            try:
                website_results = self.website_store.similarity_search_with_relevance_scores(
                    query, k=top_k
                )
                for doc, score in website_results:
                    if score >= RETRIEVAL_SCORE_THRESHOLD:
                        results.append({
                            "content": doc.page_content,
                            "source": doc.metadata.get("source", "te.eg"),
                            "source_type": doc.metadata.get("source_type", "website"),
                            "title": doc.metadata.get("title", ""),
                            "score": round(score, 3),
                        })
            except Exception as e:
                logger.warning(f"Website search failed: {e}")

        # Search uploaded documents
        if include_uploads and self.uploads_store:
            try:
                upload_results = self.uploads_store.similarity_search_with_relevance_scores(
                    query, k=min(top_k, 3)  # Fewer results from uploads
                )
                for doc, score in upload_results:
                    if score >= RETRIEVAL_SCORE_THRESHOLD:
                        results.append({
                            "content": doc.page_content,
                            "source": doc.metadata.get("source", "uploaded document"),
                            "source_type": doc.metadata.get("source_type", "upload"),
                            "title": doc.metadata.get("title", ""),
                            "score": round(score, 3),
                        })
            except Exception as e:
                logger.warning(f"Upload search failed: {e}")

        # Sort by relevance score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)

        # Limit total results
        results = results[:top_k]

        logger.info(f"Retrieved {len(results)} relevant chunks for query: '{query[:50]}...'")
        return results

    def format_context(self, results: list[dict]) -> tuple[str, list[str]]:
        """
        Format retrieved results into a context string for the LLM.

        Returns:
            (context_string, list_of_source_urls)
        """
        if not results:
            return "", []

        context_parts = []
        sources = []

        for i, r in enumerate(results, 1):
            source_label = r["source"]
            if r["title"]:
                source_label = f"{r['title']} ({r['source']})"

            context_parts.append(
                f"--- Source {i}: {source_label} [Relevance: {r['score']}] ---\n"
                f"{r['content']}\n"
            )

            if r["source"] not in sources:
                sources.append(r["source"])

        context = "\n".join(context_parts)
        return context, sources


# Module-level singleton
_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    """Get or create the singleton retriever."""
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
