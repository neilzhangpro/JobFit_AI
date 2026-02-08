"""VectorStoreAdapter — ChromaDB adapter stub (Adapter pattern).

Manages per-tenant vector collections for RAG retrieval.
This is a STUB implementation for the current PR — actual
ChromaDB integration will be implemented in a future PR.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class VectorStoreAdapter:
    """Stub vector store adapter — no actual embedding calls.

    # TODO(#next): Implement real ChromaDB integration
    # - Connect to ChromaDB via settings.chroma_host/port
    # - Create collection per tenant: tenant_{tenant_id}
    # - Use OpenAI embeddings or sentence-transformers
    # - Implement similarity search for RAG retrieval
    """

    def store_embeddings(
        self,
        tenant_id: str,
        resume_id: str,
        sections: list[dict[str, Any]],
    ) -> None:
        """Store resume section embeddings (STUB).

        Args:
            tenant_id: Tenant UUID string.
            resume_id: Resume UUID string.
            sections: List of section dicts with type and content.
        """
        logger.info(
            "STUB: Would store %d embeddings for resume %s in tenant %s",
            len(sections),
            resume_id,
            tenant_id,
        )

    def search(
        self,
        tenant_id: str,
        query: str,
        k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for similar sections (STUB).

        Args:
            tenant_id: Tenant UUID string.
            query: Search query text.
            k: Number of results to return.

        Returns:
            Empty list (stub implementation).
        """
        logger.info(
            "STUB: Would search tenant %s for: %s",
            tenant_id,
            query[:50],
        )
        return []
