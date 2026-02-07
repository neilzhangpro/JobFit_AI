# JobFit AI — Technology Selection

## 1. Technology Stack Overview

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Next.js | 14.x | React-based full-stack web framework |
| **Frontend** | TypeScript | 5.x | Type-safe JavaScript superset |
| **Frontend** | Tailwind CSS | 3.x | Utility-first CSS framework |
| **Backend** | Python | 3.11+ | Core backend language |
| **Backend** | FastAPI | 0.110+ | High-performance async API framework |
| **Backend** | Uvicorn | 0.29+ | ASGI server for FastAPI |
| **Backend** | Pydantic | 2.x | Data validation and settings management |
| **AI/ML** | LangChain | 0.2+ | LLM application framework |
| **AI/ML** | LangGraph | 0.1+ | Agentic workflow orchestration |
| **AI/ML** | OpenAI API | GPT-4o / GPT-4o-mini | Primary LLM provider |
| **AI/ML** | DeepSeek API | DeepSeek-V3 | Alternative LLM provider |
| **Database** | PostgreSQL | 16.x | Primary relational database |
| **Database** | SQLAlchemy | 2.x | Python ORM with async support |
| **Database** | Alembic | 1.13+ | Database migration management |
| **Cache** | Redis | 7.x | Caching, rate limiting, session store |
| **Vector DB** | ChromaDB | 0.5+ | Vector database for RAG |
| **Storage** | MinIO / AWS S3 | — | Object storage for uploaded files |
| **PDF** | PyPDF2 | 3.x | PDF text extraction |
| **Auth** | python-jose | 3.x | JWT token generation and validation |
| **Auth** | passlib + bcrypt | — | Password hashing |
| **Billing** | Stripe SDK | — | Payment and subscription management |
| **DevOps** | Docker | 24+ | Containerization |
| **DevOps** | Docker Compose | 2.x | Multi-container orchestration |
| **DevOps** | AWS EC2 | — | Cloud hosting |
| **DevOps** | GitHub Actions | — | CI/CD pipeline |

---

## 2. Frontend: Next.js + TypeScript + Tailwind CSS

### 2.1 Selection: Next.js 14

**Why Next.js:**

- **Server-Side Rendering (SSR) and Static Site Generation (SSG)** — Provides fast initial page loads and better SEO, important for a public-facing SaaS application.
- **App Router** — Next.js 14's App Router enables a modern file-based routing system with React Server Components, reducing client-side JavaScript bundle size.
- **API Routes** — Serves as a BFF (Backend-for-Frontend) layer to proxy requests to the FastAPI backend, simplifying CORS and authentication token management.
- **Built-in Optimizations** — Image optimization, font loading, code splitting, and prefetching come out of the box.
- **Route Groups** — `(auth)` and `(dashboard)` route groups enable clean layout separation for public vs. authenticated pages.
- **Middleware Support** — Next.js middleware enables JWT validation at the edge, redirecting unauthenticated users before page load.

**Alternatives Considered:**

| Framework | Pros | Cons | Decision |
|-----------|------|------|----------|
| **Vite + React** | Faster dev server; simpler setup | No SSR out of the box; no file-based routing; need extra config for production builds | Rejected — lacks built-in SSR and routing |
| **Nuxt.js (Vue)** | Similar features to Next.js | Team has stronger React experience; smaller ecosystem for AI/resume-related UI libraries | Rejected — team expertise mismatch |
| **Angular** | Enterprise-grade; strong typing | Steep learning curve; heavier framework; slower iteration speed for MVP | Rejected — over-engineered for MVP scope |

### 2.2 Selection: TypeScript

**Why TypeScript:**

- **Type Safety** — Catches bugs at compile time, especially valuable when handling complex data structures (parsed resume, JD analysis, optimization results, multi-tenant contexts).
- **Developer Experience** — Autocompletion, refactoring support, and inline documentation in IDEs.
- **API Contract Enforcement** — Shared type definitions ensure frontend correctly handles backend API responses and auth tokens.
- **Industry Standard** — Expected in professional React/Next.js projects and SaaS products.

### 2.3 Selection: Tailwind CSS

**Why Tailwind CSS:**

- **Rapid Prototyping** — Utility classes enable fast UI development without writing custom CSS files, crucial for MVP timeline.
- **Consistent Design** — Built-in design system (spacing, colors, typography) ensures visual consistency across the SaaS application.
- **Small Production Bundle** — Tree-shaking removes unused styles, resulting in minimal CSS in production.
- **Component-Friendly** — Pairs excellently with React component architecture and the Container/Presenter pattern.

**Alternatives Considered:**

| Framework | Pros | Cons | Decision |
|-----------|------|------|----------|
| **Material UI (MUI)** | Pre-built components; material design | Heavy bundle size; opinionated styling; harder to customize | Rejected — too heavy for custom design needs |
| **Styled Components** | CSS-in-JS; scoped styles | Runtime CSS generation; additional dependency; slower dev iteration | Rejected — runtime overhead unnecessary |
| **Plain CSS / SCSS** | Full control; no learning curve | Slower development; harder to maintain consistency | Rejected — too slow for MVP timeline |

---

## 3. Backend: Python + FastAPI

### 3.1 Selection: Python 3.11+

**Why Python:**

- **AI/ML Ecosystem** — The dominant language for AI/ML with best-in-class libraries (LangChain, LangGraph, OpenAI SDK, ChromaDB, PyPDF2).
- **LangChain/LangGraph Native** — Both frameworks are Python-first, with the most complete feature sets and documentation in Python.
- **DDD Support** — Python's class system, dataclasses, and abstract base classes support clean DDD patterns (entities, value objects, repository interfaces).
- **Community** — Massive open-source community for NLP, embeddings, and LLM-related tooling.

### 3.2 Selection: FastAPI

**Why FastAPI:**

- **Performance** — Built on Starlette and Pydantic, FastAPI is one of the fastest Python web frameworks, comparable to Node.js/Go in benchmark tests.
- **Async Support** — Native `async/await` support is essential for handling concurrent LLM API calls and streaming responses across multiple tenants.
- **Dependency Injection** — FastAPI's `Depends()` system is the backbone for injecting repositories, services, auth context, and tenant context. This naturally supports the DDD layered architecture.
- **Automatic API Documentation** — Auto-generates OpenAPI (Swagger) and ReDoc documentation from code, reducing documentation overhead.
- **Pydantic Integration** — Request/response validation via Pydantic models ensures data integrity with minimal boilerplate. Aligns with DTO pattern in the application layer.

**Alternatives Considered:**

| Framework | Pros | Cons | Decision |
|-----------|------|------|----------|
| **Flask** | Simple; lightweight; large community | No native async support; manual request validation; no auto-generated docs; no built-in DI | Rejected — lacks async, DI, and auto-docs |
| **Django** | Full-featured; ORM; admin panel | Too opinionated for DDD; Django ORM couples domain to infrastructure; slower startup | Rejected — ORM architecture conflicts with DDD repository pattern |
| **Express.js (Node.js)** | JavaScript full-stack; fast | Weaker AI/ML ecosystem; LangChain JS is less mature than Python version | Rejected — Python AI ecosystem is superior |

---

## 4. AI and Orchestration Layer

### 4.1 Selection: LangChain

**Why LangChain:**

- **Abstraction Layer** — Provides unified interfaces for LLM calls, prompt templates, output parsers, and chain composition, reducing boilerplate code.
- **RAG Support** — Built-in document loaders, text splitters, embedding models, and vector store integrations streamline the RAG pipeline.
- **Provider Agnostic** — Easily switch between OpenAI, DeepSeek, Anthropic, or local models without code changes. Supports the **Strategy pattern** for LLM provider selection.
- **Output Parsing** — Structured output parsers ensure LLM responses conform to expected schemas (critical for JD analysis, scoring, etc.).

### 4.2 Selection: LangGraph

**Why LangGraph:**

- **Agentic Workflows** — LangGraph extends LangChain with a state machine abstraction, enabling multi-step agent workflows with conditional branching, loops, and parallel execution.
- **State Management** — Built-in state persistence between agent nodes eliminates manual state passing.
- **Conditional Edges** — The score-check-then-rewrite loop (if ATS score < threshold, re-run the rewriter) is natively supported via conditional edges.
- **Observability** — Built-in tracing and debugging support via LangSmith integration.
- **Template Method Fit** — Each agent node naturally maps to a `BaseAgent` subclass with the prepare/execute/parse skeleton.

**Why not plain LangChain chains:**

Simple LangChain chains (Sequential/Parallel) lack the ability to implement conditional loops (e.g., re-running the rewriter if the score is too low). LangGraph's state graph model is specifically designed for these agentic patterns.

### 4.3 Selection: LLM Providers

#### Primary: OpenAI (GPT-4o / GPT-4o-mini)

| Aspect | Details |
|--------|---------|
| **Model** | GPT-4o for complex tasks (rewriting, analysis); GPT-4o-mini for simpler tasks (scoring, categorization) |
| **Strengths** | State-of-the-art reasoning; excellent instruction following; strong at structured output |
| **Pricing** | GPT-4o: ~$2.50/1M input, ~$10/1M output; GPT-4o-mini: ~$0.15/1M input, ~$0.60/1M output |
| **Rate Limits** | Generous for development; scalable via tiered API access |

#### Alternative: DeepSeek (DeepSeek-V3)

| Aspect | Details |
|--------|---------|
| **Model** | DeepSeek-V3 / DeepSeek-R1 |
| **Strengths** | Significantly cheaper; competitive quality for structured tasks; strong multilingual support |
| **Pricing** | ~$0.27/1M input, ~$1.10/1M output (significantly cheaper than GPT-4o) |
| **Trade-offs** | Slightly less reliable for complex creative rewriting; API stability less proven than OpenAI |

**Strategy:** Implement a provider-agnostic interface via the **Strategy pattern** (LangChain's chat model abstraction). Default to OpenAI during development, with DeepSeek as a configurable fallback. Per-tenant LLM provider configuration is supported via tenant settings.

---

## 5. Database and Storage Layer

### 5.1 Selection: PostgreSQL 16

**Why PostgreSQL:**

- **Multi-Tenant Support** — Row-Level Security (RLS) policies provide database-level tenant isolation as a defense-in-depth layer.
- **JSONB Columns** — Store semi-structured data (JD analysis, ATS score breakdown, gap reports) without separate tables, reducing schema complexity.
- **UUID Primary Keys** — Native UUID type supports globally unique identifiers across tenants.
- **Mature Ecosystem** — Battle-tested; excellent tooling; strong SQLAlchemy support.
- **Full-Text Search** — Built-in FTS can supplement vector search for keyword matching.

**Alternatives Considered:**

| Database | Pros | Cons | Decision |
|----------|------|------|----------|
| **MySQL** | Popular; good performance | Weaker JSON support; no native RLS; less feature-rich | Rejected — PostgreSQL has better multi-tenant features |
| **MongoDB** | Schema-flexible; JSON-native | Weaker consistency guarantees; harder to enforce relational integrity for multi-tenant data | Rejected — relational model better suits DDD aggregates |
| **SQLite** | Zero config; file-based | No concurrent writes; no network access; not suitable for multi-tenant SaaS | Rejected — not production-viable |

### 5.2 Selection: SQLAlchemy 2.x (ORM)

**Why SQLAlchemy:**

- **Repository Pattern Support** — SQLAlchemy's Session API maps naturally to the repository pattern: repositories use sessions to load and persist aggregates.
- **Async Support** — SQLAlchemy 2.x supports native async via `AsyncSession`, aligning with FastAPI's async architecture.
- **Mapping Flexibility** — Supports both declarative (ORM models) and imperative mapping, enabling clean separation between domain entities and ORM models.
- **Unit of Work** — SQLAlchemy's Session implements the Unit of Work pattern natively, tracking changes and committing them atomically.

### 5.3 Selection: Alembic (Database Migrations)

**Why Alembic:**

- **SQLAlchemy Native** — Designed specifically for SQLAlchemy; auto-generates migration scripts from model changes.
- **Version Control** — Migration files are version-controlled, enabling reproducible database state across environments.
- **Multi-Tenant Migrations** — Supports running migrations with RLS policies, ensuring schema changes don't break tenant isolation.

### 5.4 Selection: Redis 7

**Why Redis:**

- **JWT Token Blacklist** — Store invalidated refresh tokens for secure logout.
- **Rate Limiting** — Sliding window rate limiting per tenant and per user using Redis sorted sets.
- **Caching** — Cache frequently accessed data (tenant settings, quota limits) to reduce database load.
- **Performance** — Sub-millisecond latency for auth and rate-limit checks on every request.

**Alternatives Considered:**

| Solution | Pros | Cons | Decision |
|----------|------|------|----------|
| **In-Memory (Python dict)** | Zero setup | Lost on restart; not shared across workers; not scalable | Rejected — not production-viable |
| **Memcached** | Fast; simple | No data structures (only key-value); no persistence | Rejected — Redis has richer features |

### 5.5 Selection: ChromaDB (Vector Store)

**Why ChromaDB:**

- **Ease of Use** — Simple Python API; no complex setup or infrastructure required.
- **Docker Support** — Official Docker image available for containerized deployment.
- **LangChain Integration** — First-class integration with LangChain's vector store interface.
- **Collection-Per-Tenant** — Create separate collections per tenant for vector data isolation.
- **Metadata Filtering** — Filter vectors by user_id, section type, etc., enabling precise retrieval within a tenant's collection.

**Comparison with FAISS:**

| Feature | ChromaDB | FAISS |
|---------|----------|-------|
| **Setup Complexity** | Low (pip install + optional Docker) | Low (pip install) |
| **Persistence** | Built-in (file-based or client-server) | Manual (save/load index files) |
| **Metadata Storage** | Native metadata support with filtering | No native metadata; requires external storage |
| **Client-Server Mode** | Yes (HTTP API via Docker) | No (in-process only) |
| **Multi-Tenant Isolation** | Collection-per-tenant with easy cleanup | Manual index management per tenant |
| **LangChain Support** | Full integration | Full integration |
| **Scalability** | Suitable for small-medium scale | Highly optimized for large-scale (millions of vectors) |

**Decision:** ChromaDB is selected because its collection-per-tenant model, built-in metadata filtering, and client-server Docker deployment align perfectly with the multi-tenant SaaS architecture.

### 5.6 Selection: MinIO / AWS S3 (Object Storage)

**Why MinIO:**

- **S3-Compatible API** — Same API as AWS S3, enabling seamless migration to AWS S3 in production.
- **Self-Hosted** — Runs as a Docker container for local development; no cloud dependency during development.
- **Tenant Isolation** — Path-based isolation (`/{tenant_id}/{user_id}/`) with bucket policies.
- **Cost-Effective** — Free for self-hosted; AWS S3 pricing is minimal for resume-sized files.

**Strategy:** Use MinIO in Docker for development and testing. Switch to AWS S3 in production via environment variable configuration (same SDK, different endpoint).

### 5.7 Selection: PyPDF2 (PDF Processing)

**Why PyPDF2:**

- **Pure Python** — No system-level dependencies (unlike pdfminer or poppler-based libraries).
- **Text Extraction** — Reliable text extraction for standard PDF resumes.
- **Lightweight** — Minimal footprint; fast installation.
- **Active Maintenance** — Actively maintained with regular releases.

**Alternatives Considered:**

| Library | Pros | Cons | Decision |
|---------|------|------|----------|
| **pdfplumber** | Better table extraction; more accurate layout parsing | Heavier dependency; slower; over-featured for resume text extraction | Backup option if PyPDF2 quality is insufficient |
| **pdfminer.six** | Detailed layout analysis | Complex API; slower; harder to use | Rejected — complexity not justified |
| **Unstructured** | AI-powered parsing; handles many formats | Heavy dependency; requires additional models | Rejected — too heavy for MVP |

**Risk Mitigation:** If PyPDF2 produces poor results for certain PDF layouts (e.g., multi-column resumes, image-heavy PDFs), `pdfplumber` will be used as a fallback parser (implemented via **Strategy pattern**).

### 5.8 Embedding Model

| Option | Dimensions | Performance | Cost |
|--------|-----------|-------------|------|
| **OpenAI text-embedding-3-small** | 1536 | Good quality; fast | $0.02/1M tokens |
| **OpenAI text-embedding-3-large** | 3072 | Higher quality | $0.13/1M tokens |

**Decision:** Use `text-embedding-3-small` for the MVP. The quality difference is marginal for resume-length documents, and the cost savings are significant in a multi-tenant SaaS context.

---

## 6. Authentication and Security

### 6.1 Selection: JWT (python-jose + passlib)

**Why JWT:**

- **Stateless** — No server-side session storage for access tokens; reduces database load at scale.
- **Multi-Tenant Claims** — JWT payload carries `user_id`, `tenant_id`, and `role`, enabling middleware to extract tenant context without additional database queries.
- **Refresh Token Flow** — Short-lived access tokens (15 min) + long-lived refresh tokens (7 days) balance security and UX.
- **SaaS Standard** — Industry standard for SaaS API authentication.

**Token Structure:**

```json
{
  "sub": "user_uuid",
  "tenant_id": "tenant_uuid",
  "role": "member",
  "exp": 1700000000,
  "iat": 1699999100
}
```

**Security Measures:**

| Measure | Implementation |
|---------|---------------|
| Password Hashing | bcrypt with salt (passlib) |
| Access Token TTL | 15 minutes |
| Refresh Token TTL | 7 days |
| Token Blacklist | Redis set for revoked refresh tokens |
| CORS | Whitelist frontend origin only |
| HTTPS | Enforced in production (TLS 1.3) |

### 6.2 Alternatives Considered

| Solution | Pros | Cons | Decision |
|----------|------|------|----------|
| **Session-based auth** | Simple; server-controlled | Requires sticky sessions or shared session store; not ideal for stateless APIs | Rejected — doesn't scale for SaaS |
| **OAuth2 / OIDC (Auth0, Clerk)** | Managed; supports SSO | External dependency; cost at scale; less control | Deferred to Phase 3 for SSO support |

---

## 7. Billing: Stripe

### 7.1 Selection: Stripe

**Why Stripe:**

- **Subscription Management** — Built-in support for recurring billing, plan upgrades/downgrades, and prorated charges.
- **Webhook Integration** — Stripe webhooks notify the backend of payment events, enabling automated plan activation/deactivation.
- **Python SDK** — Official, well-documented Python SDK.
- **Industry Standard** — Most widely used payment platform for SaaS applications.

**MVP Strategy:** Billing context is implemented with proper domain model and interfaces, but Stripe integration is **stubbed** in Phase 1. All tenants default to the free plan. Stripe gateway is activated in Phase 2.

---

## 8. DevOps and Infrastructure

### 8.1 Selection: Docker + Docker Compose

**Why Docker:**

- **Environment Consistency** — Eliminates "works on my machine" issues; identical base service definitions across development and production.
- **Isolation** — Each service runs in its own container with defined resource limits (production) or unbounded access (development).
- **Multi-File Compose** — Docker Compose's `-f` flag enables a base + override pattern, cleanly separating shared definitions from environment-specific configurations.
- **Multi-Stage Builds** — Single Dockerfile per service with `dev` and `prod` stages reduces duplication while optimizing production images.
- **Industry Standard** — Demonstrates professional DevOps practices.

**Multi-File Compose Strategy:**

The project uses three Docker Compose files to manage environment differences without duplication:

```
docker-compose.yml              # Base: service definitions, networks, volumes
docker-compose.dev.yml          # Override: dev ports, volume mounts, hot reload, debug
docker-compose.prod.yml         # Override: resource limits, health checks, restart policies
```

- `docker-compose.yml` defines all 6 services with their base images, internal network, and named volumes. It contains NO environment-specific settings.
- `docker-compose.dev.yml` adds development-only overrides: host port mappings for all services, source code bind mounts for hot reload, debug ports, and relaxed security.
- `docker-compose.prod.yml` adds production-only overrides: resource limits (`deploy.resources`), restart policies (`unless-stopped`), health checks, restricted port exposure (only frontend), and optimized worker counts.

**Usage:**

```bash
# Development
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Container Architecture:**

```
docker-compose.yml (base)
├── jobfit-frontend   (Node.js 20 Alpine)   — dev: HMR / prod: next start
├── jobfit-backend    (Python 3.11 Slim)    — dev: --reload / prod: 4 workers
├── jobfit-postgres   (PostgreSQL 16 Alpine)
├── jobfit-redis      (Redis 7 Alpine)
├── jobfit-chromadb   (ChromaDB Official)
└── jobfit-minio      (MinIO Official)      — dev: +console / prod: API only
```

**Alternatives Considered for Environment Management:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **Single `docker-compose.yml` with `.env` switching** | Simplest file structure | Cannot change structural settings (volumes, ports, resource limits) via env vars alone; grows unwieldy | Rejected — insufficient flexibility |
| **Separate `docker-compose.dev.yml` and `docker-compose.prod.yml` (no base)** | Complete independence | Heavy duplication of service definitions; changes must be applied to both files | Rejected — DRY violation |
| **`docker-compose.yml` + `docker-compose.override.yml`** | Override file auto-loaded in dev | `override.yml` auto-loading is implicit and error-prone; conflicts with git ignore rules | Rejected — too implicit |
| **Base + explicit override files** | No duplication; explicit `-f` flags; clear separation | Slightly longer CLI commands | **Selected** — best balance of DRY and clarity |

### 8.2 Selection: AWS EC2

**Why AWS EC2:**

- **Full Control** — Complete control over server configuration, unlike PaaS solutions.
- **Docker Support** — Easy to run Docker Compose on a Linux EC2 instance.
- **Cost-Effective** — A single `t3.medium` instance (2 vCPU, 4GB RAM) is sufficient for MVP; scale vertically or add instances as needed.
- **Educational Value** — Demonstrates cloud deployment skills relevant to industry.

**Alternatives Considered:**

| Platform | Pros | Cons | Decision |
|----------|------|------|----------|
| **AWS ECS/EKS** | Managed container orchestration | Over-engineered for 6 containers; complex setup; higher cost | Rejected — too complex for MVP |
| **Vercel + Railway** | Zero-config for Next.js; managed Python hosting | Split infrastructure; limited Docker support; less educational | Rejected — less DevOps learning |
| **DigitalOcean Droplet** | Simpler than AWS; good docs | Smaller ecosystem; less resume-relevant than AWS | Acceptable alternative |

### 8.3 Selection: GitHub Actions (CI/CD)

**Why GitHub Actions:**

- **Native Integration** — Directly integrated with GitHub repositories; no external CI/CD service needed.
- **Free Tier** — Generous free tier for public repositories (2,000 minutes/month for private).
- **YAML Configuration** — Simple, declarative pipeline definitions.
- **Docker Support** — Built-in Docker build and push actions.

**Pipeline Design:**

| Stage | Tools | Trigger | Gate |
|-------|-------|---------|------|
| **Lint** | ESLint (frontend), Ruff (backend) | On push / PR | Must pass |
| **Type Check** | TypeScript `tsc` (frontend), mypy (backend) | On push / PR | Must pass |
| **Unit Test** | Jest (frontend), pytest (backend) | On push / PR | Must pass |
| **Integration Test** | pytest with test containers | On push / PR | Must pass |
| **Coverage** | Jest --coverage, pytest-cov | On push / PR | >= 80% |
| **Build** | Docker build | On merge to `main` | Must pass |
| **Deploy** | SSH + Docker Compose | On merge to `main` | — |

---

## 9. Development Tools

### 9.1 Code Quality

| Tool | Language | Purpose |
|------|----------|---------|
| **ESLint** | TypeScript/JavaScript | Linting and code style enforcement |
| **Prettier** | TypeScript/JavaScript | Code formatting |
| **Ruff** | Python | Fast Python linter and formatter (replaces flake8 + black + isort) |
| **mypy** | Python | Static type checking (strict mode) |

### 9.2 Testing

| Tool | Language | Purpose |
|------|----------|---------|
| **Jest** | TypeScript | Frontend unit and integration tests |
| **React Testing Library** | TypeScript | Frontend component testing |
| **pytest** | Python | Backend unit and integration tests |
| **pytest-asyncio** | Python | Async test support for FastAPI |
| **httpx** | Python | Async HTTP client for API testing with FastAPI's TestClient |
| **factory_boy** | Python | Test data factories for domain entities |
| **pytest-cov** | Python | Code coverage reporting |

### 9.3 Documentation

| Tool | Purpose |
|------|---------|
| **Swagger UI** | Auto-generated API documentation (built into FastAPI) |
| **Mermaid** | Architecture and flow diagrams in Markdown |

### 9.4 Version Control Strategy

- **Main branch** — Production-ready code; protected; only accepts PRs.
- **Feature branches** — `feature/resume-parser`, `feature/jd-analyzer`, etc.
- **Conventional Commits** — Commit messages follow the format: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.

---

## 10. Risk Assessment and Mitigation

| # | Risk | Likelihood | Impact | Mitigation Strategy |
|---|------|-----------|--------|---------------------|
| R1 | **LLM output quality inconsistency** — Resume rewriting may produce hallucinated or inaccurate content. | High | High | Use structured prompts with strict output schemas; implement the score-check loop to validate output quality; provide side-by-side comparison for human verification. |
| R2 | **PDF parsing failures** — Complex PDF layouts (multi-column, graphics-heavy) may not parse correctly. | Medium | High | Implement fallback parser (pdfplumber) via Strategy pattern; add UI for users to manually review/correct extracted text; restrict to text-based PDFs in MVP. |
| R3 | **LLM API rate limits or downtime** — External API dependency may cause service interruptions. | Medium | High | Implement retry logic with exponential backoff; support multiple LLM providers (OpenAI + DeepSeek) with automatic failover; cache frequently used prompts/responses. |
| R4 | **High LLM API costs** — Each optimization session involves multiple LLM calls, costs may escalate across tenants. | Medium | High | Use GPT-4o-mini for simpler tasks; implement per-tenant token usage tracking and quota enforcement; support DeepSeek for cost optimization; per-tenant LLM provider configuration. |
| R5 | **Multi-tenant data leakage** — Programming errors could expose one tenant's data to another. | Low | Critical | Row-Level Security (RLS) at DB level; ContextVar-based tenant injection at app level; automated integration tests for cross-tenant isolation; code review checklist for tenant-scoped queries. |
| R6 | **Session data security** — Resumes contain sensitive PII that could be exposed. | Low | High | Encrypted at rest (AES-256); encrypted in transit (TLS); tenant-isolated storage; access audit logs. |
| R7 | **Slow optimization pipeline** — Multiple sequential LLM calls may result in long wait times. | Medium | Medium | Implement streaming responses for real-time feedback; show progress indicators; parallelize independent agent nodes where possible; set timeout limits. |
| R8 | **Database migration complexity** — Schema changes across multi-tenant tables can be risky. | Medium | Medium | Use Alembic with strict migration review process; test migrations against production-like data; always include rollback scripts. |
| R9 | **Scope creep** — Feature requests beyond MVP may delay delivery. | Medium | Medium | Strictly adhere to phased delivery (Phase 1/2/3); track features in backlog; use sprint planning. |
| R10 | **DDD over-engineering** — Excessive abstraction may slow development for a small team. | Medium | Medium | Apply DDD pragmatically: strict layers for core domain (Optimization), simpler structure for supporting domains (Interview, Billing stub). |
