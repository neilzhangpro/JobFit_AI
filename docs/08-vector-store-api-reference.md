# Vector Store (ChromaDB) API Reference

> **Owner**: Person B (Platform & Infrastructure)
> **Consumer**: Person A (AI Workflow — RAG Retriever, JD Analyzer, etc.)
> **Module**: `backend/resume/infrastructure/vector_store.py`

---

## 1. Overview

The `VectorStoreAdapter` provides tenant-isolated vector storage and similarity search for resume embeddings via ChromaDB. It is the **only** interface AI workflow agents should use to retrieve resume content for RAG (Retrieval-Augmented Generation).

### Key Design Decisions

| Decision | Detail |
|---|---|
| **Tenant isolation** | One ChromaDB collection per tenant: `tenant_{tenant_id}` |
| **Embedding model** | OpenAI `text-embedding-3-small` (1536 dims) when API key is set; ChromaDB default `all-MiniLM-L6-v2` (384 dims) as fallback |
| **Distance metric** | Cosine similarity (`hnsw:space = cosine`) |
| **Graceful degradation** | All methods return safe defaults (empty list / no-op) when ChromaDB is unreachable — embedding failures never block resume uploads |
| **Idempotent writes** | Uses `upsert` — re-uploading the same resume overwrites previous embeddings cleanly |

---

## 2. Data Model

### 2.1 Collection Naming

```
tenant_{tenant_id}
```

Each tenant gets its own collection. Cross-tenant queries are impossible by design.

### 2.2 Document Schema

Each resume section is stored as a separate document:

| Field | Type | Example | Description |
|---|---|---|---|
| `id` | `str` | `"a1b2c3d4_0"` | `{resume_id}_{section_index}` |
| `document` | `str` | `"Senior Python developer..."` | Raw text content of the section |
| `metadata.resume_id` | `str` | `"a1b2c3d4-..."` | UUID of the parent resume |
| `metadata.section_type` | `str` | `"experience"` | One of: `contact_info`, `summary`, `experience`, `education`, `skills`, `certifications`, `projects`, `other` |
| `metadata.order_index` | `int` | `0` | Position of the section in the resume (0-based) |

---

## 3. Public API

### 3.1 `store_embeddings()`

Embed and store resume sections. Called automatically by `ResumeApplicationService.upload()`.

```python
def store_embeddings(
    self,
    tenant_id: str,       # Tenant UUID string
    resume_id: str,        # Resume UUID string
    sections: list[dict],  # [{"type": "experience", "content": "..."}]
) -> None:
```

**Behavior:**
- Generates one embedding per section
- Uses `upsert` — safe to call multiple times for the same resume
- Logs `"Stored N embeddings for resume {id} in tenant {id}"` on success
- Catches all exceptions internally — never raises

**Section dict format:**

```python
{
    "type": "experience",   # SectionType.value
    "content": "5 years of Python development at..."
}
```

---

### 3.2 `search()` ⭐ Primary RAG Interface

Similarity search for resume sections matching a query. **This is the method AI agents should call.**

```python
def search(
    self,
    tenant_id: str,                 # Tenant UUID string
    query: str,                     # Free-text query (will be embedded)
    k: int = 10,                    # Max results to return
    resume_id: str | None = None,   # Optional: filter to single resume
) -> list[dict]:
```

**Returns** a list of result dicts, sorted by relevance (highest first):

```python
[
    {
        "id": "a1b2c3d4_0",
        "content": "Senior Python developer with 5 years...",
        "metadata": {
            "resume_id": "a1b2c3d4-...",
            "section_type": "experience",
            "order_index": 0
        },
        "relevance_score": 0.8723   # 0.0 to 1.0 (cosine similarity)
    },
    ...
]
```

**Usage Examples:**

```python
# RAG Retriever: find resume sections relevant to a job description
results = vector_store.search(
    tenant_id=tenant_id,
    query="Python backend developer with AWS experience",
    k=5,
)

# Scoped search: search within a specific resume only
results = vector_store.search(
    tenant_id=tenant_id,
    query="machine learning projects",
    k=3,
    resume_id="a1b2c3d4-e5f6-...",
)

# Job Matching: find most relevant resume sections for a JD
for result in results:
    print(f"[{result['metadata']['section_type']}] "
          f"score={result['relevance_score']:.2f}")
    print(result["content"][:200])
```

**Important Notes:**
- Returns `[]` if ChromaDB is unavailable (graceful degradation)
- Returns `[]` on any internal error (logged, not raised)
- `relevance_score` is computed as `1.0 - cosine_distance`, clamped to `[0.0, 1.0]`
- Results are already sorted by relevance (ChromaDB default behavior)

---

### 3.3 `delete_embeddings()`

Remove all embeddings for a specific resume. Called automatically by `ResumeApplicationService.delete_resume()`.

```python
def delete_embeddings(
    self,
    tenant_id: str,   # Tenant UUID string
    resume_id: str,    # Resume UUID string
) -> None:
```

**Behavior:**
- Queries all documents with `metadata.resume_id == resume_id`, then deletes by IDs
- Logs `"Deleted N embeddings for resume {id} in tenant {id}"` on success
- No-op if ChromaDB is unavailable

---

## 4. Integration Guide for AI Agents

### 4.1 Dependency Injection

The `VectorStoreAdapter` is instantiated in the API layer and injected into services via FastAPI `Depends()`. AI workflow agents should receive it the same way:

```python
from resume.infrastructure.vector_store import VectorStoreAdapter
from config import Settings

# In your FastAPI route / dependency:
def get_vector_store(settings: Settings = Depends(get_settings)) -> VectorStoreAdapter:
    return VectorStoreAdapter(settings)
```

### 4.2 Typical RAG Flow

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  JD Analyzer │────▶│  RAG Retriever   │────▶│  Resume Rewriter│
│  (extract    │     │  (search vectors)│     │  (optimize CV)  │
│   keywords)  │     │                  │     │                 │
└──────────────┘     └──────────────────┘     └─────────────────┘
                            │
                            ▼
                     vector_store.search(
                         tenant_id=...,
                         query=jd_keywords,
                         k=5,
                         resume_id=target_resume
                     )
```

### 4.3 Recommended Parameters

| Use Case | `k` | `resume_id` | Notes |
|---|---|---|---|
| **RAG for optimization** | 5–10 | Set to target resume | Retrieve relevant sections of the resume being optimized |
| **Job matching** | 10–20 | `None` | Search across ALL resumes for the tenant |
| **Gap analysis** | 5 | Set to target resume | Find sections related to required skills |
| **Interview prep** | 5–8 | Set to target resume | Find experience/project sections for question generation |

### 4.4 Error Handling

The adapter handles all errors internally. AI agents do **not** need try/except around calls:

```python
# This is safe — will return [] if ChromaDB is down
results = vector_store.search(tenant_id=tid, query=q)
if not results:
    # Fallback: use raw resume text from database instead
    resume = await resume_repo.find_by_id(resume_id, tenant_id)
    raw_text = "\n".join(s.content for s in resume.sections)
```

---

## 5. Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `CHROMA_HOST` | `chromadb` | ChromaDB hostname (Docker service name) |
| `CHROMA_PORT` | `8000` | ChromaDB internal port (mapped to `8200` on host) |
| `OPENAI_API_KEY` | `""` | If set, uses OpenAI embeddings; if empty, uses ChromaDB default |

### Docker Compose

ChromaDB runs as the `chromadb` service on internal port `8000`, mapped to host port `8200`:

```yaml
chromadb:
  image: chromadb/chroma:latest
  ports:
    - "8200:8000"
```

The backend connects to `chromadb:8000` (Docker internal network), **not** `localhost:8200`.

---

## 6. Testing

### Unit Tests (no Docker required)

Use `chromadb.EphemeralClient()` for in-memory testing:

```python
import chromadb
from config import Settings

client = chromadb.EphemeralClient()
adapter = VectorStoreAdapter(
    settings=Settings(),
    client=client,          # In-memory, no server needed
    embedding_fn=None,      # Use ChromaDB default
)

# Now call store_embeddings / search / delete_embeddings as normal
```

### Tenant Isolation Test

```python
def test_tenant_isolation():
    adapter.store_embeddings("tenant_a", "r1", sections=[...])
    results = adapter.search("tenant_b", "query")
    assert results == []  # Tenant B cannot see Tenant A's data
```

---

## 7. Changelog

| Date | Author | Change |
|---|---|---|
| 2026-02-11 | Tomie (Person B) | Initial implementation — `store_embeddings`, `search`, `delete_embeddings` |
