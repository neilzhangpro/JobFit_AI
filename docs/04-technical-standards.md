# JobFit AI — Technical Standards and Development Conventions

This document defines the development standards, coding conventions, testing requirements, and CI/CD quality gates for the JobFit AI project. All contributors must follow these standards. CI/CD pipelines enforce these rules automatically — code that does not meet these standards will not be merged.

---

## 1. Core Principles

| # | Principle | Description |
|---|-----------|-------------|
| 1 | **Test First** | Write tests before or alongside implementation. No feature is complete without tests. |
| 2 | **Domain Purity** | Domain layer has ZERO external dependencies (no frameworks, no ORMs, no HTTP). |
| 3 | **Fail Fast** | Validate inputs at boundaries (API layer). Raise explicit exceptions rather than returning silent defaults. |
| 4 | **Explicit Over Implicit** | Prefer clear, verbose code over clever shortcuts. Every function should have a single, obvious purpose. |
| 5 | **Tenant Isolation by Default** | Every data access must be tenant-scoped. Treat unscoped queries as bugs. |
| 6 | **Convention Over Configuration** | Follow the project's established patterns. When in doubt, look at existing code. |

---

## 2. Code Style and Formatting

### 2.1 Python (Backend)

| Rule | Standard | Enforced By |
|------|----------|-------------|
| Formatter | Ruff (format mode, line length 88) | CI: `ruff format --check` |
| Linter | Ruff (select = E, F, W, I, UP, B, SIM, N) | CI: `ruff check` |
| Type Checking | mypy (strict mode) | CI: `mypy --strict` |
| Import Order | isort-compatible (via Ruff) | CI: `ruff check --select I` |
| Docstrings | Google style; required on all public classes and functions | Code review |
| Max Line Length | 88 characters | Ruff |
| Naming | `snake_case` for functions/variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants | Ruff (N convention) |

**Example: Properly documented function**

```python
def calculate_ats_score(
    optimized_content: list[str],
    jd_analysis: JDAnalysis,
) -> ATSScore:
    """Calculate ATS compatibility score for optimized resume content.

    Compares the optimized bullet points against JD requirements to produce
    a weighted score across multiple categories.

    Args:
        optimized_content: List of rewritten resume bullet points.
        jd_analysis: Structured JD analysis with extracted skills and requirements.

    Returns:
        ATSScore value object with overall score and category breakdown.

    Raises:
        ValueError: If optimized_content is empty.
    """
    if not optimized_content:
        raise ValueError("optimized_content must not be empty")
    ...
```

### 2.2 TypeScript (Frontend)

| Rule | Standard | Enforced By |
|------|----------|-------------|
| Formatter | Prettier (printWidth: 100, singleQuote: true, semi: true) | CI: `prettier --check` |
| Linter | ESLint with `@typescript-eslint` recommended rules | CI: `eslint .` |
| Type Checking | TypeScript strict mode (`"strict": true` in tsconfig.json) | CI: `tsc --noEmit` |
| Naming | `camelCase` for variables/functions; `PascalCase` for components/types/interfaces; `UPPER_SNAKE_CASE` for constants | ESLint |
| Component Files | One component per file; filename matches component name | Code review |
| Imports | Absolute imports using `@/` alias (e.g., `@/components/ui/Button`) | tsconfig paths |

### 2.3 Universal Rules

| Rule | Details |
|------|---------|
| **No magic numbers** | Extract numbers into named constants. `MAX_UPLOAD_SIZE_MB = 10` instead of bare `10`. |
| **No hardcoded strings** | API URLs, error messages, and config values must come from constants or environment variables. |
| **No commented-out code** | Dead code must be deleted, not commented out. Use git history for recovery. |
| **No `any` type** | TypeScript `any` is banned. Use `unknown` with type guards if type is truly unknown. |
| **No bare `except`** | Python `except Exception` minimum. Prefer specific exception types. |

---

## 3. Architecture and Layer Rules

### 3.1 Layer Dependency Rules

```
API Layer  -->  Application Layer  -->  Domain Layer
                      |
                      v
               Infrastructure Layer
```

| Rule | Description |
|------|-------------|
| **Domain Layer** | MUST NOT import from Application, Infrastructure, or API layers. MUST NOT import any framework (FastAPI, SQLAlchemy, etc.). |
| **Application Layer** | May import from Domain. MUST NOT import from Infrastructure directly — use dependency injection (interfaces defined in Domain, implementations in Infrastructure). |
| **Infrastructure Layer** | Implements interfaces defined in Domain. May import from Domain. May import external libraries (SQLAlchemy, ChromaDB, etc.). |
| **API Layer** | May import from Application (DTOs, services). MUST NOT import from Domain entities directly — use DTOs for data transfer. |

### 3.2 Layer-Specific Standards

**Domain Layer:**

```python
# GOOD: Pure domain logic, no external dependencies
class OptimizationSession:
    """Aggregate root for the optimization workflow."""

    def start_processing(self) -> None:
        """Transition session to processing state."""
        if self.status != SessionStatus.PENDING:
            raise DomainError(f"Cannot start processing: session is {self.status}")
        self.status = SessionStatus.PROCESSING
        self._add_event(OptimizationStarted(session_id=self.id))

# BAD: Domain entity importing framework
from sqlalchemy import Column  # NEVER in domain layer
```

**Application Layer:**

```python
# GOOD: Orchestrates use case, delegates to domain and infrastructure
class OptimizationApplicationService:
    """Application service orchestrating the optimization use case."""

    def __init__(
        self,
        repo: IOptimizationRepository,    # Interface (from domain)
        resume_repo: IResumeRepository,   # Interface (from domain)
        uow: IUnitOfWork,                 # Interface (from shared)
        graph_runner: IGraphRunner,        # Interface (from domain)
    ) -> None:
        self._repo = repo
        self._resume_repo = resume_repo
        self._uow = uow
        self._graph_runner = graph_runner

    async def run_optimization(self, command: RunOptimizationCommand) -> OptimizationResponse:
        """Execute the full optimization pipeline."""
        ...
```

**Infrastructure Layer:**

```python
# GOOD: Implements domain interface using SQLAlchemy
class OptimizationRepository(IOptimizationRepository):
    """SQLAlchemy implementation of the optimization repository."""

    def __init__(self, session: AsyncSession, tenant_context: TenantContext) -> None:
        self._session = session
        self._tenant_id = tenant_context.current_tenant_id

    async def find_by_id(self, session_id: str) -> OptimizationSession | None:
        """Find optimization session by ID, scoped to current tenant."""
        stmt = select(OptimizationSessionModel).where(
            OptimizationSessionModel.id == session_id,
            OptimizationSessionModel.tenant_id == self._tenant_id,  # ALWAYS filter by tenant
        )
        ...
```

---

## 4. Testing Standards

### 4.1 Test-First Development

| Rule | Description |
|------|-------------|
| **Write tests before implementation** | For domain logic, write unit tests first. For API endpoints, write integration tests first. Tests define the expected behavior. |
| **No PR without tests** | Every PR that adds/changes functionality must include corresponding tests. PRs without tests will be rejected. |
| **Tests are documentation** | Test names should clearly describe the behavior being tested. A reader should understand the feature by reading the test names alone. |

### 4.2 Test Categories and Requirements

| Category | Scope | Tools | Coverage Target | CI Gate |
|----------|-------|-------|-----------------|---------|
| **Unit Tests** | Domain entities, value objects, domain services, application services (with mocked repos) | pytest, Jest | >= 90% for domain layer | Must pass |
| **Integration Tests** | API endpoints, repository implementations, database queries, tenant isolation | pytest + httpx + TestClient, Jest + MSW | >= 70% for infra layer | Must pass |
| **Multi-Tenant Isolation Tests** | Verify no cross-tenant data leakage | pytest (dedicated test suite) | 100% of data access paths | Must pass |
| **Frontend Component Tests** | UI component rendering and interaction | React Testing Library | >= 70% | Must pass |
| **Overall Coverage** | Combined backend coverage | pytest-cov | >= 80% | Must pass |

### 4.3 Test Naming Convention

**Python (pytest):**

```python
# Pattern: test_<method_name>_<scenario>_<expected_result>

def test_start_processing_when_pending_transitions_to_processing():
    """Session in PENDING state should transition to PROCESSING."""
    ...

def test_start_processing_when_already_processing_raises_domain_error():
    """Session already in PROCESSING state should raise DomainError."""
    ...

def test_find_by_id_with_wrong_tenant_returns_none():
    """Repository should return None when querying with a different tenant_id."""
    ...
```

**TypeScript (Jest):**

```typescript
// Pattern: describe('<ComponentOrHook>') > it('should <expected behavior> when <condition>')

describe('useOptimization', () => {
  it('should return loading state when optimization is in progress', () => { ... });
  it('should display error message when API returns 429', () => { ... });
});

describe('ScoreCard', () => {
  it('should render score as percentage when score is provided', () => { ... });
  it('should show empty state when score is null', () => { ... });
});
```

### 4.4 Test Data Management

| Rule | Details |
|------|---------|
| **Use Factories** | Use `factory_boy` (Python) to create test entities. Never hardcode entity construction in tests. |
| **Isolated Test Database** | Integration tests use a separate test database, reset between test sessions via transactions. |
| **No Shared State** | Each test must be independent. No test should depend on another test's side effects. |
| **Fixtures for Common Setup** | Use pytest fixtures for database sessions, authenticated clients, and tenant contexts. |

**Example: Test Factory**

```python
import factory
from identity.domain.entities import User

class UserFactory(factory.Factory):
    """Factory for creating test User entities."""

    class Meta:
        model = User

    id = factory.LazyFunction(uuid4)
    tenant_id = factory.LazyFunction(uuid4)
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    role = "member"
    status = "active"
```

### 4.5 Multi-Tenant Isolation Test Template

Every repository must include this isolation test pattern:

```python
async def test_tenant_a_cannot_see_tenant_b_data(
    tenant_a_repo: ResumeRepository,
    tenant_b_repo: ResumeRepository,
):
    """Verify strict tenant isolation at the repository level."""
    # Arrange: Create a resume for tenant A
    resume = ResumeFactory(tenant_id=TENANT_A_ID)
    await tenant_a_repo.save(resume)

    # Act: Try to access it from tenant B's context
    result = await tenant_b_repo.find_by_id(resume.id)

    # Assert: Tenant B should not see tenant A's data
    assert result is None
```

---

## 5. Design Pattern Usage Guide

### 5.1 When to Use Each Pattern

| Pattern | Use When | Do Not Use When |
|---------|----------|-----------------|
| **Factory** | Creating aggregates/entities requires validation, default values, or complex initialization logic. | Simple object construction with no invariants (use constructor directly). |
| **Repository** | Accessing persistent storage for aggregates. Always. | In-memory data structures that don't need persistence. |
| **Strategy** | Runtime selection between interchangeable algorithms (LLM providers, PDF parsers, export formats). | Only one implementation exists and no others are planned. |
| **Observer (Events)** | Loose coupling between bounded contexts (e.g., Optimization -> Billing). | Synchronous, in-context communication within the same aggregate. |
| **Unit of Work** | Transactional consistency across multiple repository operations. Always for write operations. | Read-only queries that don't modify state. |
| **Singleton** | Application-wide shared resources (config, DB pool, event bus). | Objects that carry request-specific or tenant-specific state. |
| **Template Method** | AI agents share a common workflow skeleton but differ in prompt/parsing logic. | Logic doesn't follow a fixed step sequence. |
| **Adapter** | Wrapping external libraries/APIs (ChromaDB, S3, Stripe) to isolate them from domain logic. | Internal code that you fully control. |
| **Dependency Injection** | Always. All service dependencies should be injected, never instantiated internally. | — (always use DI) |

### 5.2 Anti-Patterns to Avoid

| Anti-Pattern | Description | Correct Approach |
|-------------|-------------|-----------------|
| **Anemic Domain Model** | Entities with only getters/setters and no behavior. All logic in services. | Put business logic in entities and domain services. Entities enforce their own invariants. |
| **God Service** | One service class handling too many responsibilities. | Split by bounded context. Each application service handles one use case or a closely related set. |
| **Leaky Abstraction** | Infrastructure details leaking into domain (e.g., SQLAlchemy models used as domain entities). | Separate ORM models (infrastructure) from domain entities. Map between them in the repository. |
| **Shotgun Surgery** | A single change requires modifications across many files/layers. | Encapsulate related logic within a single bounded context. |
| **Shared Mutable State** | Global variables or module-level mutable state. | Use `ContextVar` for request-scoped state (tenant context). Use DI for service dependencies. |

---

## 6. Git Workflow and Commit Standards

### 6.1 Branch Strategy

| Branch | Purpose | Protection |
|--------|---------|-----------|
| `main` | Production-ready code | Protected; requires PR with passing CI + 1 approval |
| `develop` | Integration branch for features | Protected; requires passing CI |
| `feature/<name>` | Feature development | Branched from `develop`; merged via PR |
| `fix/<name>` | Bug fixes | Branched from `develop`; merged via PR |
| `hotfix/<name>` | Production emergency fixes | Branched from `main`; merged to both `main` and `develop` |

### 6.2 Conventional Commits

All commit messages MUST follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

**Types:**

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(optimization): add ATS scoring agent` |
| `fix` | Bug fix | `fix(resume): handle multi-column PDF parsing` |
| `test` | Adding or updating tests | `test(identity): add tenant isolation tests` |
| `refactor` | Code change with no feature/fix | `refactor(shared): extract base repository class` |
| `docs` | Documentation changes | `docs: update API endpoint documentation` |
| `chore` | Build/tooling changes | `chore: update Docker base images` |
| `ci` | CI/CD pipeline changes | `ci: add coverage gate to GitHub Actions` |
| `style` | Formatting (no logic change) | `style(backend): apply ruff formatting` |

**Scope** should match the bounded context: `identity`, `resume`, `optimization`, `interview`, `billing`, `shared`, `frontend`.

### 6.3 Pull Request Rules

| Rule | Details |
|------|---------|
| **PR Title** | Must follow Conventional Commits format. |
| **PR Description** | Must include: What changed, Why, How to test. |
| **Size Limit** | PRs should be < 400 lines of changed code. Split larger changes into multiple PRs. |
| **Tests Required** | All PRs must include tests. CI will reject PRs without adequate coverage. |
| **Review Required** | Minimum 1 approval from team member before merge. |
| **CI Must Pass** | All CI checks (lint, type check, test, coverage) must pass before merge. |

---

## 7. CI/CD Pipeline Quality Gates

### 7.1 Pipeline Stages

```mermaid
graph LR
    subgraph pr [On Pull Request]
        Lint[Lint + Format Check]
        TypeCheck[Type Check]
        UnitTest[Unit Tests]
        IntTest[Integration Tests]
        Coverage[Coverage >= 80%]
    end

    subgraph merge [On Merge to main]
        Build[Docker Build]
        E2E[Smoke Tests]
        Deploy[Deploy to EC2]
    end

    Lint --> TypeCheck
    TypeCheck --> UnitTest
    UnitTest --> IntTest
    IntTest --> Coverage

    Coverage -.->|merge approved| Build
    Build --> E2E
    E2E --> Deploy
```

### 7.2 Quality Gate Definitions

| Gate | Command | Pass Criteria | Blocks Merge? |
|------|---------|---------------|---------------|
| **Python Lint** | `ruff check backend/` | Zero errors | Yes |
| **Python Format** | `ruff format --check backend/` | No formatting changes needed | Yes |
| **Python Type Check** | `mypy --strict backend/` | Zero type errors | Yes |
| **Python Unit Tests** | `pytest backend/ -m "not integration"` | All pass | Yes |
| **Python Integration Tests** | `pytest backend/ -m integration` | All pass | Yes |
| **Python Coverage** | `pytest --cov=backend --cov-fail-under=80` | >= 80% overall | Yes |
| **Tenant Isolation Tests** | `pytest backend/ -m tenant_isolation` | All pass (100%) | Yes |
| **TS Lint** | `eslint frontend/src/` | Zero errors | Yes |
| **TS Format** | `prettier --check frontend/src/` | No formatting changes needed | Yes |
| **TS Type Check** | `tsc --noEmit` | Zero type errors | Yes |
| **TS Unit Tests** | `jest --ci` | All pass | Yes |
| **TS Coverage** | `jest --coverage --coverageThreshold='{"global":{"branches":70,"functions":70,"lines":80}}'` | Meets threshold | Yes |
| **Docker Build** | `docker compose build` | Builds successfully | Yes (on merge) |

### 7.3 GitHub Actions Workflow Structure

```yaml
# .github/workflows/ci.yml (conceptual outline)
name: CI Pipeline

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  backend-lint:
    # ruff check + ruff format --check + mypy --strict

  backend-test:
    needs: backend-lint
    # pytest with coverage gate
    # Includes: unit tests, integration tests, tenant isolation tests
    # Uploads coverage report

  frontend-lint:
    # eslint + prettier --check + tsc --noEmit

  frontend-test:
    needs: frontend-lint
    # jest with coverage gate

  docker-build:
    needs: [backend-test, frontend-test]
    if: github.ref == 'refs/heads/main'
    # docker compose build

  deploy:
    needs: docker-build
    if: github.ref == 'refs/heads/main'
    # SSH to EC2 + docker compose up -d
```

---

## 8. Database Standards

### 8.1 Migration Rules

| Rule | Details |
|------|---------|
| **One migration per change** | Each schema change gets its own Alembic migration file. No combining unrelated changes. |
| **Reversible migrations** | Every migration must include both `upgrade()` and `downgrade()` functions. |
| **No data loss** | Column drops or table deletions must be preceded by a data migration or backup step. |
| **Test migrations** | Run migrations against a copy of production-like data before deploying. |
| **Naming convention** | Migration message format: `<action>_<table>_<detail>` (e.g., `add_users_table`, `add_tenant_id_to_resumes`). |

### 8.2 Table and Column Naming

| Rule | Convention | Example |
|------|-----------|---------|
| Table names | `snake_case`, plural | `users`, `optimization_sessions` |
| Column names | `snake_case` | `created_at`, `tenant_id` |
| Primary keys | `id` (UUID type) | `id UUID PRIMARY KEY` |
| Foreign keys | `<referenced_table_singular>_id` | `user_id`, `tenant_id` |
| Timestamps | Always include `created_at`; include `updated_at` for mutable entities | `created_at TIMESTAMP NOT NULL DEFAULT NOW()` |
| Soft delete | Use `deleted_at` column instead of hard delete for important entities | `deleted_at TIMESTAMP NULL` |
| Tenant column | Every tenant-scoped table MUST have `tenant_id NOT NULL` | `tenant_id UUID NOT NULL REFERENCES tenants(id)` |

### 8.3 Index Standards

| Rule | Details |
|------|---------|
| **Tenant + primary lookup** | Every tenant-scoped table should have a composite index on `(tenant_id, id)`. |
| **Foreign keys** | All foreign key columns must be indexed. |
| **Query-driven** | Add indexes based on actual query patterns; don't over-index. |

---

## 9. API Standards

### 9.1 REST Conventions

| Rule | Standard |
|------|----------|
| **URL Structure** | `/api/<resource>` (plural nouns, no verbs). Example: `/api/resumes`, not `/api/getResume`. |
| **HTTP Methods** | `GET` (read), `POST` (create), `PUT` (full update), `PATCH` (partial update), `DELETE` (remove). |
| **Status Codes** | `200` (success), `201` (created), `204` (deleted), `400` (bad request), `401` (unauthorized), `403` (forbidden), `404` (not found), `422` (validation error), `429` (rate limited), `500` (server error). |
| **Response Envelope** | All responses use `{ success, data, error, meta }` envelope format. |
| **Pagination** | Use cursor-based pagination for lists: `?cursor=<id>&limit=20`. |
| **Versioning** | URL prefix: `/api/v1/...` (introduce when breaking changes occur). |

### 9.2 Request/Response DTOs

| Rule | Details |
|------|---------|
| **Pydantic models for all requests** | Every API endpoint must define a Pydantic model for request validation. |
| **Separate request and response models** | Never reuse the same model for both. `CreateResumeRequest` != `ResumeResponse`. |
| **No domain entities in responses** | API responses use DTOs, not domain entities. Map entities to DTOs in the application service. |
| **Consistent field naming** | Use `snake_case` in JSON responses (Python convention). Frontend converts to `camelCase` as needed. |

---

## 10. Security Standards

### 10.1 Authentication Rules

| Rule | Details |
|------|---------|
| **Password requirements** | Minimum 8 characters; must include uppercase, lowercase, and number. |
| **Password storage** | bcrypt with default work factor (12 rounds). Never store plain text. |
| **Token storage (frontend)** | Access token in memory only. Refresh token in `httpOnly` cookie. Never in `localStorage`. |
| **Token refresh** | Implement silent refresh before access token expires. |

### 10.2 Input Validation

| Rule | Details |
|------|---------|
| **Validate at boundary** | All user input is validated in the API layer using Pydantic models. |
| **Sanitize text input** | JD text and any user-provided text must be sanitized to prevent injection. |
| **File validation** | Verify MIME type and magic bytes for uploaded PDFs. Don't rely on file extension alone. |
| **Size limits** | Enforce maximum request body size at the web server level. |

### 10.3 Tenant Security

| Rule | Details |
|------|---------|
| **Tenant from token only** | `tenant_id` must be extracted from the JWT token, never from request parameters. |
| **Repository-level enforcement** | Every repository query must include `WHERE tenant_id = ?`. This is enforced by the base repository class. |
| **No cross-tenant joins** | Database queries must never join across different tenant_id values. |
| **Audit logging** | Log all data access with `tenant_id`, `user_id`, and action type for security auditing. |

---

## 11. Documentation Standards

### 11.1 Code Documentation

| Rule | Details |
|------|---------|
| **Class-level docstrings** | Every class must have a docstring explaining its purpose and responsibilities. |
| **Function-level docstrings** | Every public function must have a Google-style docstring with Args, Returns, and Raises. |
| **Critical logic comments** | Non-obvious business rules or algorithmic decisions must have inline comments explaining "why", not "what". |
| **No TODO without issue** | `TODO` comments must reference a GitHub issue number: `# TODO(#42): implement caching`. |

### 11.2 API Documentation

| Rule | Details |
|------|---------|
| **Swagger/OpenAPI** | All endpoints are documented via FastAPI's auto-generated OpenAPI spec. |
| **Request/Response examples** | Every endpoint should have example request and response bodies in Pydantic model schemas. |
| **Error documentation** | All error codes and their conditions are documented in the OpenAPI spec. |

---

## 12. Environment Management Standards

### 12.1 Environment Definitions

| Environment | Purpose | Infra | `APP_ENV` Value |
|-------------|---------|-------|-----------------|
| **Development** | Local coding and debugging | `docker compose -f docker-compose.yml -f docker-compose.dev.yml` | `development` |
| **Test / CI** | Automated testing in CI pipeline | Ephemeral containers in GitHub Actions runners | `test` |
| **Production** | Live SaaS platform serving real users | `docker compose -f docker-compose.yml -f docker-compose.prod.yml` on AWS EC2 | `production` |

### 12.2 Docker Compose File Rules

| Rule | Details |
|------|---------|
| **Base file is environment-agnostic** | `docker-compose.yml` defines services, networks, and volumes with NO environment-specific settings (no ports, no volumes mounts, no resource limits, no restart policies). |
| **Never use `docker-compose.override.yml`** | The implicit auto-loading behavior is error-prone. Always use explicit `-f` flags. `docker-compose.override.yml` is listed in `.gitignore`. |
| **Dev overrides are for developer convenience** | `docker-compose.dev.yml` exposes ports, mounts source code, enables debug mode. These settings must NEVER appear in the base or prod files. |
| **Prod overrides are for reliability** | `docker-compose.prod.yml` adds health checks, resource limits, restart policies, and restricts port exposure. |
| **Use shell aliases or Makefile** | Provide `make dev`, `make prod`, `make down` shortcuts so developers don't need to remember the `-f` flags. |

### 12.3 Makefile Conventions

A root `Makefile` MUST provide standard commands to abstract Docker Compose complexity:

```makefile
# Standard targets every developer should know
dev:              docker compose -f ... -f docker-compose.dev.yml up
dev-build:        docker compose -f ... -f docker-compose.dev.yml up --build
prod:             docker compose -f ... -f docker-compose.prod.yml up -d
prod-build:       docker compose -f ... -f docker-compose.prod.yml up -d --build
down:             docker compose down
logs:             docker compose logs -f
test:             run tests inside containers
migrate:          run Alembic migrations
seed:             seed development database with test data
clean:            remove all containers, volumes, and images
```

### 12.4 Dockerfile Standards

| Rule | Details |
|------|---------|
| **Multi-stage builds required** | Every Dockerfile must have at least a `dev` and `prod` stage, sharing a common `base` stage. |
| **Minimal production images** | Production stage should use slim/alpine base images; install only runtime dependencies; no dev tools (pytest, ruff, eslint). |
| **Non-root user in production** | Production containers must run as a non-root user (`USER appuser`). Dev containers may run as root for convenience. |
| **`.dockerignore` required** | Every directory containing a Dockerfile must have a `.dockerignore` file. |
| **Pin base image versions** | Always pin specific versions (`python:3.11.9-slim`, not `python:3.11-slim`). Update deliberately. |
| **No secrets in build args** | Never pass secrets via `ARG` or `ENV` in Dockerfiles. Secrets are injected at runtime via `.env` files or environment variables. |

### 12.5 Environment-Specific Behavior in Code

Application code must use `APP_ENV` to adjust runtime behavior:

| Behavior | Development | Production |
|----------|-------------|------------|
| **CORS origins** | `["*"]` (allow all) | `["https://jobfit.ai"]` (whitelist) |
| **Log level** | `DEBUG` | `WARNING` |
| **Log format** | Human-readable text | Structured JSON |
| **Swagger docs** | Enabled (`/docs`, `/redoc`) | Disabled (or behind auth) |
| **Error details** | Full stack trace in API responses | Generic error message only; stack trace in logs only |
| **JWT expiry** | Longer (60min access, 30d refresh) | Shorter (15min access, 7d refresh) |
| **Rate limiting** | Relaxed or disabled | Strict per-tenant limits |
| **Email sending** | Print to console (no real emails) | Send via real email service |

**Implementation pattern:**

```python
# config.py — Singleton settings loaded from environment
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    app_env: str = "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def log_level(self) -> str:
        return "WARNING" if self.is_production else "DEBUG"

    @property
    def cors_origins(self) -> list[str]:
        return ["https://jobfit.ai"] if self.is_production else ["*"]
```

### 12.6 Database per Environment

| Environment | Database Name | Data | Migrations |
|-------------|-------------|------|------------|
| **Development** | `jobfit_dev` | Seed data + developer test data | Run manually: `make migrate` |
| **Test / CI** | `jobfit_test` | Created and destroyed per test session | Auto-run by pytest fixtures |
| **Production** | `jobfit_prod` | Real user data | Run as part of deployment pipeline |

**Rules:**

- Development and test databases must NEVER contain real user data.
- Production database backups must be encrypted and stored in a separate S3 bucket.
- Developers may use `make seed` to populate their local database with realistic but fake test data.

---

## 13. Sensitive Files and Secrets Management

### 13.1 Core Principle

**No secret shall ever be committed to the repository.** All credentials, private keys, API keys, and connection strings must be managed through environment variables or a secrets manager. A leaked secret is treated as a **critical security incident** — the key must be rotated immediately.

### 13.2 Git Ignore Rules (`.gitignore`)

The project root `.gitignore` MUST include the following patterns. These rules are non-negotiable and enforced by CI secret scanning.

**Environment and Secrets:**

| Pattern | Reason |
|---------|--------|
| `.env` | Contains all runtime secrets (API keys, DB passwords, JWT secrets) |
| `.env.*` | Environment-specific variants (`.env.local`, `.env.production`, `.env.staging`) |
| `!.env.example` | Exception: the template file with placeholder values IS committed |
| `**/secrets/` | Any directory named `secrets` |
| `config/secrets.*` | Secret configuration files |

**Private Keys and Certificates:**

| Pattern | Reason |
|---------|--------|
| `*.pem` | PEM-encoded private keys and certificates |
| `*.key` | Private key files |
| `*.p12`, `*.pfx` | PKCS#12 certificate bundles (contain private keys) |
| `*.jks`, `*.keystore` | Java KeyStore files |
| `id_rsa`, `id_ed25519` | SSH private keys |
| `*.crt` (in non-fixture paths) | TLS/SSL certificates (may reveal infrastructure details) |

**Cloud and Service Credentials:**

| Pattern | Reason |
|---------|--------|
| `.aws/` | AWS CLI credentials and config directory |
| `credentials` | Generic credentials file |
| `*.credentials` | Any credentials file |
| `service-account*.json` | GCP service account keys |
| `*-keypair.pem` | AWS EC2 key pairs |

**Application and Infrastructure:**

| Pattern | Reason |
|---------|--------|
| `docker-compose.override.yml` | May contain local secret overrides |
| `*.sql.dump` | Database dumps may contain user PII |
| `*.sqlite3` | Local SQLite databases with real data |

**IDE and OS:**

| Pattern | Reason |
|---------|--------|
| `.idea/` | JetBrains IDE settings (may contain run configs with secrets) |
| `.vscode/settings.json` | VS Code settings (may contain local paths and secrets) |
| `.DS_Store` | macOS filesystem metadata |
| `Thumbs.db` | Windows thumbnail cache |

### 13.3 Docker Ignore Rules (`.dockerignore`)

Each Dockerfile context (frontend and backend) MUST have a `.dockerignore` to prevent sensitive files from being included in Docker build context and image layers.

**Backend `.dockerignore`:**

| Pattern | Reason |
|---------|--------|
| `.env`, `.env.*` | Secrets must be injected at runtime, not baked into images |
| `*.pem`, `*.key` | Private keys must never exist inside container images |
| `.git/`, `.github/` | Repository history and CI configs are unnecessary in images |
| `docs/` | Documentation is not needed at runtime |
| `tests/` | Test code is not needed in production images |
| `*.md` | Markdown files are unnecessary in images |
| `__pycache__/`, `*.pyc` | Python bytecode should be regenerated in the container |
| `.mypy_cache/`, `.ruff_cache/` | Tool caches are not needed |
| `alembic/versions/*.pyc` | Compiled migration files |

**Frontend `.dockerignore`:**

| Pattern | Reason |
|---------|--------|
| `.env`, `.env.*` | Secrets must be injected at build/runtime |
| `node_modules/` | Dependencies are reinstalled during `docker build` |
| `.next/` | Build output is regenerated during `docker build` |
| `.git/`, `.github/` | Not needed in images |
| `docs/`, `*.md` | Not needed in images |
| `coverage/` | Test coverage reports |

### 13.4 Environment Variable Template

The repository MUST include a `.env.example` file that lists every required environment variable with placeholder values and comments. This file IS committed to git and serves as documentation.

```bash
# .env.example — Copy to .env and fill in real values. NEVER commit .env itself.

# === Database ===
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/jobfit_db

# === Redis ===
REDIS_URL=redis://localhost:6379/0

# === Authentication ===
JWT_SECRET_KEY=CHANGE_ME_TO_A_RANDOM_64_CHAR_STRING
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# === LLM Providers ===
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
LLM_PROVIDER=openai

# === Vector Store ===
CHROMA_HOST=localhost
CHROMA_PORT=8200

# === Object Storage (S3 / MinIO) ===
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=jobfit-uploads

# === Stripe (stubbed in MVP) ===
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx

# === Application ===
MAX_UPLOAD_SIZE_MB=10
```

### 13.5 Pre-Commit Secret Scanning

A pre-commit hook MUST be configured to prevent accidental secret commits before they reach the repository.

**Tool:** `gitleaks` (recommended) or `detect-secrets`.

| Check | Description |
|-------|-------------|
| **Pattern scanning** | Detects API keys, tokens, passwords, and private key headers in staged files. |
| **Entropy detection** | Flags high-entropy strings that are likely secrets (e.g., random 64-char strings). |
| **Allowlist** | `.env.example` and test fixtures with fake credentials are allowlisted. |

**Pre-commit config (`.pre-commit-config.yaml`):**

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

### 13.6 CI/CD Secret Scanning

| Layer | Tool | Trigger | Action on Detection |
|-------|------|---------|---------------------|
| **GitHub Native** | GitHub Secret Scanning | Automatic (push) | Alerts repository admins; blocks push if push protection is enabled. |
| **CI Pipeline** | `gitleaks` GitHub Action | On every PR | Fails the CI pipeline; PR cannot be merged. |
| **Scheduled Audit** | `trufflehog` full repo scan | Weekly cron job | Creates a GitHub Issue for any findings. |

**GitHub Actions integration:**

```yaml
# Part of CI pipeline
secret-scan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - uses: gitleaks/gitleaks-action@v2
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 13.7 Production Secrets Management

| Environment | Strategy | Details |
|-------------|----------|---------|
| **Local Development** | `.env` file | Developers maintain their own `.env` (git-ignored). Copy from `.env.example`. |
| **CI/CD** | GitHub Actions Secrets | Secrets stored in GitHub repository settings; injected as environment variables during pipeline runs. |
| **Production** | AWS Secrets Manager or EC2 environment variables | Secrets injected into Docker containers at runtime via `docker-compose.yml` `environment` section or `env_file` directive pointing to a server-local `.env`. |

**Critical Rule:** The production `.env` file on the EC2 instance must have restricted permissions (`chmod 600`) and be owned by the deploy user only.

### 13.8 Incident Response for Leaked Secrets

If a secret is accidentally committed or detected in the repository:

| Step | Action | Timeframe |
|------|--------|-----------|
| 1 | **Rotate the secret immediately** at the provider (regenerate API key, change password, etc.). | Within 15 minutes |
| 2 | **Revoke the old secret** to ensure it cannot be used. | Immediately after rotation |
| 3 | **Remove from git history** using `git filter-branch` or BFG Repo-Cleaner if the commit was pushed. | Within 1 hour |
| 4 | **Update all environments** with the new secret (local, CI/CD, production). | Within 1 hour |
| 5 | **Post-mortem** — document what happened, why, and what process improvement prevents recurrence. | Within 24 hours |
