"""RAGRetrieverAgent — performs vector similarity search against resume embeddings."""

# TODO: Implement RAGRetrieverAgent
#   - Inherits from BaseAgent
#   - prepare(): initialize ChromaDB client, get tenant-specific collection
#   - execute(): perform vector similarity search using JD requirements as query
#   - parse_output(): return top-k relevant resume sections
#   - Tenant isolation: ensure collection name includes tenant_id prefix
