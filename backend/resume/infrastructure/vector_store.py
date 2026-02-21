"""VectorStoreAdapter — ChromaDB adapter for tenant-isolated embeddings.

Manages per-tenant vector collections for RAG retrieval. Each tenant
gets its own ChromaDB collection named ``tenant_{tenant_id}``.

Uses OpenAI ``text-embedding-3-small`` (1536 dims) when an API key
is available, otherwise falls back to ChromaDB's default embedding
function. All public methods degrade gracefully when ChromaDB is
unreachable — a failed embedding must never block a resume upload.
"""

from __future__ import annotations

import logging
from typing import Any, cast

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.types import EmbeddingFunction, Where

from config import Settings

logger = logging.getLogger(__name__)

# Distance metric used for all collections.  Cosine similarity is
# intuitive (1.0 = identical, 0.0 = orthogonal) and matches the
# OpenAI embedding space well.
_DISTANCE_METRIC = "cosine"

# Minimum relevance score to include in search results.
_MIN_RELEVANCE_SCORE = 0.0


def _build_openai_embedding_fn(
    api_key: str,
) -> EmbeddingFunction[list[str]] | None:
    """Create an OpenAI embedding function if the key is available.

    Returns:
        An ``OpenAIEmbeddingFunction`` instance, or ``None`` if the
        key is empty or the import fails.
    """
    if not api_key:
        return None
    try:
        from chromadb.utils.embedding_functions import (
            OpenAIEmbeddingFunction,
        )

        return OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-3-small",
        )
    except Exception:
        logger.warning(
            "Failed to create OpenAI embedding function — "
            "falling back to ChromaDB default",
            exc_info=True,
        )
        return None


class VectorStoreAdapter:
    """ChromaDB adapter for storing and searching resume embeddings.

    Constructor accepts optional ``client`` and ``embedding_fn``
    parameters so that tests can inject an ``EphemeralClient`` and
    skip the OpenAI dependency.

    Args:
        settings: Application settings with ChromaDB connection info.
        client: Pre-built ChromaDB client (for testing).
        embedding_fn: Pre-built embedding function (for testing).
    """

    def __init__(
        self,
        settings: Settings,
        client: ClientAPI | None = None,
        embedding_fn: EmbeddingFunction[list[str]] | None = None,
    ) -> None:
        self._settings = settings
        self._available = True

        # --- Client ---------------------------------------------------
        if client is not None:
            self._client = client
        else:
            try:
                self._client = chromadb.HttpClient(
                    host=settings.chroma_host,
                    port=settings.chroma_port,
                )
                # Quick connectivity check
                self._client.heartbeat()
            except Exception:
                logger.warning(
                    "ChromaDB not reachable at %s:%s — embeddings disabled",
                    settings.chroma_host,
                    settings.chroma_port,
                    exc_info=True,
                )
                self._available = False
                return

        # --- Embedding function ----------------------------------------
        if embedding_fn is not None:
            self._embedding_fn: EmbeddingFunction[list[str]] | None = embedding_fn
        else:
            self._embedding_fn = _build_openai_embedding_fn(
                settings.openai_api_key,
            )
            # None means "use ChromaDB default" — that is acceptable.

    # ------------------------------------------------------------------
    # Collection helper
    # ------------------------------------------------------------------

    def _get_collection(
        self,
        tenant_id: str,
    ) -> chromadb.Collection:
        """Get or create the tenant-scoped collection.

        Args:
            tenant_id: Tenant UUID string used in the collection name.

        Returns:
            A ``chromadb.Collection`` ready for upsert / query.
        """
        kwargs: dict[str, Any] = {
            "name": f"tenant_{tenant_id}",
            "metadata": {"hnsw:space": _DISTANCE_METRIC},
        }
        if self._embedding_fn is not None:
            kwargs["embedding_function"] = self._embedding_fn
        return self._client.get_or_create_collection(**kwargs)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store_embeddings(
        self,
        tenant_id: str,
        resume_id: str,
        sections: list[dict[str, Any]],
    ) -> None:
        """Embed and store resume sections in ChromaDB.

        Each section is stored as a separate document with metadata
        containing ``resume_id``, ``section_type``, and
        ``order_index``.  Uses ``upsert`` so repeated uploads of the
        same resume overwrite previous embeddings cleanly.

        Args:
            tenant_id: Tenant UUID string for collection isolation.
            resume_id: Resume UUID string.
            sections: List of dicts, each with ``type`` and ``content``.
        """
        if not self._available:
            logger.warning(
                "ChromaDB unavailable — skipping store_embeddings for resume %s",
                resume_id,
            )
            return

        if not sections:
            return

        try:
            collection = self._get_collection(tenant_id)

            ids: list[str] = []
            documents: list[str] = []
            metadatas: list[dict[str, Any]] = []

            for idx, section in enumerate(sections):
                ids.append(f"{resume_id}_{idx}")
                documents.append(section["content"])
                metadatas.append(
                    {
                        "resume_id": resume_id,
                        "section_type": section["type"],
                        "order_index": idx,
                    }
                )

            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,  # type: ignore[arg-type]
            )
            logger.info(
                "Stored %d embeddings for resume %s in tenant %s",
                len(documents),
                resume_id,
                tenant_id,
            )
        except Exception:
            logger.error(
                "ChromaDB store_embeddings failed for resume %s",
                resume_id,
                exc_info=True,
            )

    def search(
        self,
        tenant_id: str,
        query: str,
        k: int = 10,
        resume_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for resume sections similar to *query*.

        Args:
            tenant_id: Tenant UUID — determines the collection.
            query: Free-text search query (will be embedded).
            k: Maximum number of results to return.
            resume_id: Optional filter to limit results to a
                single resume.

        Returns:
            A list of dicts, each containing ``content``,
            ``metadata``, and ``relevance_score`` (0.0–1.0).
            Returns an empty list on any failure.
        """
        if not self._available:
            logger.warning(
                "ChromaDB unavailable — returning empty search results",
            )
            return []

        try:
            collection = self._get_collection(tenant_id)

            where_filter: Where | None = None
            if resume_id is not None:
                where_filter = cast(Where, {"resume_id": resume_id})

            results = collection.query(
                query_texts=[query],
                n_results=k,
                where=where_filter,
            )

            chunks: list[dict[str, Any]] = []
            if not results or not results["ids"] or not results["ids"][0]:
                return chunks

            distances = results.get("distances")
            documents = results.get("documents")
            metadatas = results.get("metadatas")

            for i, doc_id in enumerate(results["ids"][0]):
                # Cosine distance → relevance: 1.0 - distance
                distance = distances[0][i] if distances else 0.0
                relevance = max(1.0 - distance, _MIN_RELEVANCE_SCORE)

                content = documents[0][i] if documents else ""
                metadata = metadatas[0][i] if metadatas else {}

                chunks.append(
                    {
                        "id": doc_id,
                        "content": content,
                        "metadata": metadata,
                        "relevance_score": round(relevance, 4),
                    }
                )

            return chunks

        except Exception:
            logger.error(
                "ChromaDB search failed for tenant %s",
                tenant_id,
                exc_info=True,
            )
            return []

    def delete_embeddings(
        self,
        tenant_id: str,
        resume_id: str,
    ) -> None:
        """Remove all embeddings for a specific resume.

        Args:
            tenant_id: Tenant UUID — determines the collection.
            resume_id: Resume UUID whose embeddings to delete.
        """
        if not self._available:
            logger.warning(
                "ChromaDB unavailable — skipping delete_embeddings for resume %s",
                resume_id,
            )
            return

        try:
            collection = self._get_collection(tenant_id)
            existing = collection.get(
                where={"resume_id": resume_id},
            )
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
                logger.info(
                    "Deleted %d embeddings for resume %s in tenant %s",
                    len(existing["ids"]),
                    resume_id,
                    tenant_id,
                )
        except Exception:
            logger.error(
                "ChromaDB delete_embeddings failed for resume %s",
                resume_id,
                exc_info=True,
            )
