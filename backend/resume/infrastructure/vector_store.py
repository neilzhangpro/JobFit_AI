"""VectorStoreAdapter — ChromaDB adapter for embedding storage (Adapter pattern).

Manages per-tenant ChromaDB collections (tenant_{tenant_id}).
Stores resume section embeddings and performs similarity search for RAG retrieval.
"""

# TODO(#62): Implement VectorStoreAdapter with store_embeddings() and search() methods
# TODO(#63): Implement collection-per-tenant isolation
