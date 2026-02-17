# JobFit AI — Unified PR Feature Plan

This document defines **all Pull Requests** required to complete the JobFit AI platform.
It covers both developers working in parallel:

- **Brandy (Person A)**: AI Workflow — Optimization pipeline, Interview agents
- **Tomie (Person B)**: Platform & Infrastructure — Billing, Frontend, Shared infra

Each PR follows the conventions in
[06-git-workflow-guide.md](../06-git-workflow-guide.md) and implements sections of
[02-system-architecture.md](../02-system-architecture.md) and
[07-ai-workflow-architecture.md](../07-ai-workflow-architecture.md).

**Rules applied to every PR:**

- Branch from `develop`, target `develop`.
- Branch naming: `feature/<bounded-context>-<description>`.
- PR title: Conventional Commits `feat(scope): description`.
- Size: < 400 lines of changed code.
- Tests included (test-first workflow).
- PR description includes Summary, Motivation, Changes, Testing.
- Squash and merge when approved.

---

## Current Implementation Status

| Context | Status | Owner |
|---|---|---|
| `shared/` | ✅ Implemented (base entities, middleware, DB, UoW, tenant context) | Both |
| `identity/` | ✅ Implemented (register, login, JWT, refresh) | Tomie (B) |
| `resume/` | ✅ Implemented (upload, parse, CRUD, ChromaDB vector store) | Tomie (B) |
| `optimization/` | 🟡 A1 domain models done; A2 BaseAgent + state schema done | Brandy (A) |
| `interview/` | 🔲 Scaffolded — all files are stubs/TODOs | Brandy (A) |
| `billing/` | 🔲 Scaffolded — all files are stubs/TODOs | Tomie (B) |
| `frontend/` | 🔲 Scaffolded — API client, hooks, pages, components are stubs | Tomie (B) |

---

## Unified Dependency Graph

```
                        ┌─────────────────────────────────────────────────────┐
                        │           BRANDY (Person A) — AI Workflow           │
                        │                                                     │
                        │  A1 (domain models)                                 │
                        │    └── A2 (BaseAgent + state schema)                │
                        │          ├── A3 (JD Analyzer)     ← parallel        │
                        │          ├── A4 (RAG Retriever)   ← parallel        │
                        │          │     └── A5 (Resume Rewriter)             │
                        │          │           └── A6 (ATS Scorer)            │
                        │          │                 └── A7 (Gap Analyzer)    │
                        │          └──────── A8 (Pipeline Integration) ◄──┐  │
                        │                      └── A9 (Question Gen)      │  │
                        │                            └── A10 (Cover Letter)│  │
                        └──────────────────────────────────────────────────│──┘
                                                                          │
        ┌─────────────────────────────────────────────────────────────────┘
        │ A8 depends on T2 (quota service)
        │
┌───────┴─────────────────────────────────────────────────────────────────────┐
│                  TOMIE (Person B) — Platform & Infrastructure               │
│                                                                             │
│  T1 (billing domain) ──► T2 (quota service + repo) ──► T3 (billing API)    │
│                                                            │                │
│  T4 (event bus) ──────────────────────────────► T5 (billing event handler)  │
│                                                                             │
│  T6 (frontend API client + auth) ──► T7 (resume UI)                        │
│                                       ──► T8 (optimization UI)             │
│                                       ──► T9 (interview UI)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Cross-team dependency**: Brandy's **A8** (Full Pipeline) calls `QuotaEnforcementService.check_quota()`,
which is delivered by Tomie's **T2**. All other PRs are independent between the two developers.

---

## Parallel Development Timeline

```
Week 1-2:
  Tomie:   T1 → T2 → T4 → T6
  Brandy:  A1 → A2 → A3 + A4 (parallel)

Week 3-4:
  Tomie:   T3 → T5 → T7
  Brandy:  A5 → A6 → A7

Week 5:
  Tomie:   T8 (mock data first)
  Brandy:  A8 (Pipeline Integration, depends on T2 ✅)

Week 6:
  Tomie:   T9 → T8/T9 wire to real API
  Brandy:  A9 → A10

Final:
  Both:    End-to-end integration testing, bug fixes
```

---

# Part 1: Brandy (Person A) — AI Workflow PRs

## A1 — Optimization Domain Models

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-domain-models` |
| **PR Title** | `feat(optimization): add domain value objects, entities, and repository interface` |
| **Target** | `develop` |
| **Est. Lines** | ~250-300 |
| **Depends On** | shared/domain (done) |

### PR Description

```markdown
## Summary
- Implements SessionStatus enum, JDAnalysis, ATSScore, GapReport value objects
- Implements OptimizationSession (aggregate root) and OptimizationResult (entity)
- Defines IOptimizationRepository interface (ABC)
- Adds OptimizationSessionFactory and OptimizationDomainService
- Adds AgentExecutionError to shared exceptions

## Motivation
Foundation for all optimization pipeline code. Every subsequent PR depends on these
domain models. Pure Python with zero framework imports.

## Changes
- `optimization/domain/value_objects.py` — SessionStatus, JDAnalysis, ATSScore, GapReport, ScoreBreakdown
- `optimization/domain/entities.py` — OptimizationSession, OptimizationResult
- `optimization/domain/repository.py` — IOptimizationRepository (ABC)
- `optimization/domain/factories.py` — OptimizationSessionFactory
- `optimization/domain/services.py` — OptimizationDomainService (status transitions, score validation)
- `shared/domain/exceptions.py` — Add AgentExecutionError
- `tests/test_optimization.py` — Unit tests for all value objects, entity status transitions, factory

## Testing
- [x] Unit tests for value object immutability and validation
- [x] Unit tests for entity status transitions (pending→processing→completed/failed)
- [x] Unit tests for factory default initialization
- [x] Zero framework imports verified in domain layer
```

### Files Touched

- `optimization/domain/value_objects.py`
- `optimization/domain/entities.py`
- `optimization/domain/repository.py`
- `optimization/domain/factories.py`
- `optimization/domain/services.py`
- `shared/domain/exceptions.py`
- `tests/test_optimization.py`

---

## A2 — BaseAgent + State Schema + Graph Skeleton

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-base-agent` |
| **PR Title** | `feat(optimization): add BaseAgent template method and LangGraph state schema` |
| **Target** | `develop` |
| **Est. Lines** | ~200-280 |
| **Depends On** | A1 |

### PR Description

```markdown
## Summary
- Implements BaseAgent ABC with run/prepare/execute/parse_output template method
- Adds _get_model() strategy for LLM provider selection (OpenAI/DeepSeek)
- Adds _track_tokens() for billing integration
- Defines OptimizationState TypedDict with all sub-types
- Creates graph skeleton with build_optimization_graph() (nodes as stubs)

## Motivation
All 5 optimization agents inherit from BaseAgent. The state schema and graph
skeleton must exist before any individual agent can be wired in.

## Changes
- `optimization/infrastructure/agents/base_agent.py` — BaseAgent ABC
- `optimization/infrastructure/agents/graph.py` — OptimizationState, build_optimization_graph(), score_check_router(), result_aggregator_node()
- `tests/test_optimization.py` — Tests for BaseAgent error wrapping, token tracking, model selection

## Testing
- [x] Unit test: BaseAgent subclass with mock prepare/execute/parse
- [x] Unit test: _get_model returns correct provider based on config
- [x] Unit test: score_check_router routes correctly for all 3 conditions
- [x] Unit test: result_aggregator_node assembles final_result
```

### Files Touched

- `optimization/infrastructure/agents/base_agent.py`
- `optimization/infrastructure/agents/graph.py`
- `tests/test_optimization.py`

---

## A3 — JD Analyzer Agent

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-jd-analyzer` |
| **PR Title** | `feat(optimization): implement JD analyzer agent with structured extraction` |
| **Target** | `develop` |
| **Est. Lines** | ~150-200 |
| **Depends On** | A2 |

### PR Description

```markdown
## Summary
- Implements JDAnalyzerAgent (inherits BaseAgent)
- Extracts hard_skills, soft_skills, responsibilities, qualifications, keyword_weights
- Uses GPT-4o-mini with temperature 0.0 for deterministic extraction
- Validates output JSON schema in parse_output()

## Motivation
First agent in the pipeline. Produces the JDAnalysis that all downstream agents
(retriever, rewriter, scorer, gap analyzer) depend on.

## Changes
- `optimization/infrastructure/agents/jd_analyzer.py` — JDAnalyzerAgent + jd_analyzer_node()
- `tests/test_optimization.py` — 5+ test cases (valid JD, short JD, empty JD, malformed LLM output, timeout)

## Testing
- [x] Unit tests with mocked LLM responses
- [x] Edge case: JD text too short raises ValidationError
- [x] Edge case: invalid JSON triggers retry logic
- [x] Verified prompt matches architecture doc Section 3.2
```

### Files Touched

- `optimization/infrastructure/agents/jd_analyzer.py`
- `tests/test_optimization.py`

---

## A4 — RAG Retriever Agent

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-rag-retriever` |
| **PR Title** | `feat(optimization): implement RAG retriever agent with vector search` |
| **Target** | `develop` |
| **Est. Lines** | ~150-200 |
| **Depends On** | A2, Tomie's ChromaDB adapter (done ✅) |

### PR Description

```markdown
## Summary
- Implements RAGRetrieverAgent (inherits BaseAgent)
- Queries ChromaDB tenant collection using JD keywords
- Pure vector search — no LLM call, zero token cost
- Includes VectorStoreReader adapter (read-only access to Resume context)
- Filters by relevance score, deduplicates, respects top_k limit

## Motivation
Bridges the Resume context (upstream) and Optimization context (downstream).
Provides relevant resume chunks for the Resume Rewriter.

## Changes
- `optimization/infrastructure/agents/rag_retriever.py` — RAGRetrieverAgent + rag_retriever_node()
- `tests/test_optimization.py` — Tests for query construction, empty collection fallback, relevance filtering

## Testing
- [x] Unit tests with mocked ChromaDB client
- [x] Edge case: collection not found returns empty chunks
- [x] Edge case: zero results proceeds with warning
- [x] Verified top_k and relevance threshold from architecture doc Section 3.3
```

### Files Touched

- `optimization/infrastructure/agents/rag_retriever.py`
- `tests/test_optimization.py`

---

## A5 — Resume Rewriter Agent

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-resume-rewriter` |
| **PR Title** | `feat(optimization): implement resume rewriter agent for multi-section optimization` |
| **Target** | `develop` |
| **Est. Lines** | ~200-300 |
| **Depends On** | A3, A4 |

### PR Description

```markdown
## Summary
- Implements ResumeRewriterAgent (inherits BaseAgent)
- Rewrites experience bullets, skills summary, and project descriptions
- Uses GPT-4o with temperature 0.7 for creative rewriting
- Supports first-attempt and retry prompts (with previous score feedback)
- Enforces compact context policy (top_k chunks, max_chunk_chars)

## Motivation
Core value-producing agent — the most token-intensive and user-visible step in the
pipeline. Supports the two-stage rewrite strategy from architecture doc Section 3.7.3.

## Changes
- `optimization/infrastructure/agents/resume_rewriter.py` — ResumeRewriterAgent + resume_rewriter_node()
- `tests/test_optimization.py` — Tests for first attempt, retry with score feedback, section-keyed output, fallback on malformed JSON

## Testing
- [x] Unit tests with mocked LLM responses
- [x] Verify output schema: dict with experience/skills_summary/projects keys
- [x] Verify retry prompt includes previous score breakdown
- [x] Edge case: missing sections handled gracefully
```

### Files Touched

- `optimization/infrastructure/agents/resume_rewriter.py`
- `tests/test_optimization.py`

---

## A6 — ATS Scorer Agent

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-ats-scorer` |
| **PR Title** | `feat(optimization): implement ATS scorer with rule-based fast-path` |
| **Target** | `develop` |
| **Est. Lines** | ~200-280 |
| **Depends On** | A5 |

### PR Description

```markdown
## Summary
- Implements ATSScorerAgent (inherits BaseAgent)
- Adds deterministic pre-scorer (keyword overlap, formatting checks)
- LLM scoring via GPT-4o-mini only when rule-based confidence is below threshold
- Scores: overall, keywords, skills, experience, formatting (all 0.0-1.0)
- Clamps out-of-range values in parse_output()

## Motivation
Gate for the rewrite retry loop. The rule-based fast-path reduces token usage by
skipping LLM calls when the match is clearly strong. Architecture doc Sections 3.5 + 3.7.1.

## Changes
- `optimization/infrastructure/agents/ats_scorer.py` — ATSScorerAgent + ats_scorer_node() + rule-based pre-scorer
- `tests/test_optimization.py` — Tests for high/medium/low confidence paths, score clamping, default fallback

## Testing
- [x] Unit test: high-confidence path skips LLM call
- [x] Unit test: low-confidence path invokes LLM
- [x] Unit test: out-of-range scores clamped to [0.0, 1.0]
- [x] Unit test: invalid JSON returns default 0.5 score with warning
```

### Files Touched

- `optimization/infrastructure/agents/ats_scorer.py`
- `tests/test_optimization.py`

---

## A7 — Gap Analyzer Agent

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-gap-analyzer` |
| **PR Title** | `feat(optimization): implement gap analyzer agent` |
| **Target** | `develop` |
| **Est. Lines** | ~120-180 |
| **Depends On** | A6 |

### PR Description

```markdown
## Summary
- Implements GapAnalyzerAgent (inherits BaseAgent)
- Identifies missing skills, recommendations, transferable skills, priority levels
- Uses GPT-4o-mini with temperature 0.2

## Motivation
Final analytical step before result aggregation. Provides actionable gap feedback
that users value highly.

## Changes
- `optimization/infrastructure/agents/gap_analyzer.py` — GapAnalyzerAgent + gap_analyzer_node()
- `tests/test_optimization.py` — Tests for valid output, empty gap report fallback, LLM timeout

## Testing
- [x] Unit tests with mocked LLM responses
- [x] Edge case: timeout returns empty report (non-fatal)
- [x] Verify output schema matches GapReportDict
```

### Files Touched

- `optimization/infrastructure/agents/gap_analyzer.py`
- `tests/test_optimization.py`

---

## A8 — Full Pipeline Integration

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-pipeline` |
| **PR Title** | `feat(optimization): wire full pipeline with application service, routes, and persistence` |
| **Target** | `develop` |
| **Est. Lines** | ~350-400 |
| **Depends On** | A3-A7, **T2** (Tomie's quota service) |

### PR Description

```markdown
## Summary
- Wires all 5 agents into compiled LangGraph with conditional routing
- Implements OptimizationApplicationService (create session → invoke graph → persist result → publish event)
- Implements ORM models, repository, DTOs, commands
- Implements API routes: POST /optimize, GET /sessions, GET /sessions/{id}
- Adds budget guardrails (max tokens, max latency, max LLM calls)

## Motivation
Connects all individual agents into the working end-to-end pipeline accessible
via API. This is the integration PR that makes the optimization feature usable.

## Changes
- `optimization/infrastructure/agents/graph.py` — Finalize build_optimization_graph() with all real nodes
- `optimization/application/services.py` — OptimizationApplicationService
- `optimization/application/dto.py` — OptimizationRequest, OptimizationResponse, SessionDetailDTO
- `optimization/application/commands.py` — RunOptimizationCommand
- `optimization/infrastructure/models.py` — OptimizationSessionModel, OptimizationResultModel
- `optimization/infrastructure/repository_impl.py` — OptimizationRepository
- `optimization/api/routes.py` — POST /optimize, GET /sessions, GET /sessions/{id}
- `tests/test_optimization.py` — Integration tests, tenant isolation test

## Testing
- [x] Integration test: POST /optimize returns optimized result
- [x] Integration test: GET /sessions returns session list scoped by tenant
- [x] Tenant isolation test: tenant_a_cannot_see_tenant_b_sessions
- [x] Budget guardrail test: pipeline stops when max tokens exceeded
```

### Files Touched

- `optimization/infrastructure/agents/graph.py`
- `optimization/application/services.py`
- `optimization/application/dto.py`
- `optimization/application/commands.py`
- `optimization/infrastructure/models.py`
- `optimization/infrastructure/repository_impl.py`
- `optimization/api/routes.py`
- `tests/test_optimization.py`

---

## A9 — Interview Question Generator

| Field | Value |
|-------|-------|
| **Branch** | `feature/interview-question-gen` |
| **PR Title** | `feat(interview): implement question generator with STAR-format answers` |
| **Target** | `develop` |
| **Est. Lines** | ~300-380 |
| **Depends On** | A8 |

### PR Description

```markdown
## Summary
- Implements InterviewPrep aggregate root, value objects, factory, repository interface
- Implements QuestionGeneratorAgent (inherits BaseAgent) with GPT-4o
- Generates 10+ categorized questions (behavioral, technical, situational) with STAR answers
- Implements InterviewApplicationService, DTOs, ORM model, repository, API route
- POST /interview-prep endpoint

## Motivation
First interview context feature. Depends on completed optimization session result
for JD analysis and optimized resume content.

## Changes
- `interview/domain/entities.py` — InterviewPrep aggregate root
- `interview/domain/value_objects.py` — InterviewQuestion, QuestionCategory
- `interview/domain/factories.py` — InterviewPrepFactory
- `interview/domain/repository.py` — IInterviewPrepRepository
- `interview/infrastructure/agents/question_generator.py` — QuestionGeneratorAgent
- `interview/application/services.py` — InterviewApplicationService (question generation)
- `interview/application/dto.py` — InterviewPrepResponse, InterviewQuestionDTO
- `interview/infrastructure/models.py` — InterviewPrepModel
- `interview/infrastructure/repository_impl.py` — InterviewPrepRepository
- `interview/api/routes.py` — POST /interview-prep
- `tests/test_interview.py` — Unit + integration tests

## Testing
- [x] Unit tests for question generator with mocked LLM
- [x] Verify >= 10 questions across 3 categories
- [x] Integration test: POST /interview-prep with valid session_id
- [x] Tenant isolation test: tenant_a_cannot_see_tenant_b_interview_preps
```

### Files Touched

- `interview/domain/entities.py`
- `interview/domain/value_objects.py`
- `interview/domain/factories.py`
- `interview/domain/repository.py`
- `interview/infrastructure/agents/question_generator.py`
- `interview/application/services.py`
- `interview/application/dto.py`
- `interview/infrastructure/models.py`
- `interview/infrastructure/repository_impl.py`
- `interview/api/routes.py`
- `tests/test_interview.py`

---

## A10 — Cover Letter Generator

| Field | Value |
|-------|-------|
| **Branch** | `feature/interview-cover-letter` |
| **PR Title** | `feat(interview): implement cover letter generator with tone selection` |
| **Target** | `develop` |
| **Est. Lines** | ~150-200 |
| **Depends On** | A9 |

### PR Description

```markdown
## Summary
- Implements CoverLetterGeneratorAgent (inherits BaseAgent) with GPT-4o
- Supports 3 tones: formal, conversational, enthusiastic
- Adds CoverLetter value object
- Extends InterviewApplicationService with cover letter generation method
- POST /cover-letter endpoint

## Motivation
Final interview feature. Completes the full AI workflow scope (optimization + interview).

## Changes
- `interview/infrastructure/agents/cover_letter_generator.py` — CoverLetterGeneratorAgent
- `interview/domain/value_objects.py` — Add CoverLetter value object
- `interview/application/services.py` — Add generate_cover_letter() method
- `interview/application/dto.py` — Add CoverLetterResponse DTO
- `interview/api/routes.py` — Add POST /cover-letter endpoint
- `tests/test_interview.py` — Tests for tone selection, output length, error handling

## Testing
- [x] Unit tests with mocked LLM for each tone
- [x] Verify cover letter length (250-400 words)
- [x] Integration test: POST /cover-letter returns valid content
```

### Files Touched

- `interview/infrastructure/agents/cover_letter_generator.py`
- `interview/domain/value_objects.py`
- `interview/application/services.py`
- `interview/application/dto.py`
- `interview/api/routes.py`
- `tests/test_interview.py`

---

# Part 2: Tomie (Person B) — Platform & Infrastructure PRs

## T1 — Billing Domain Models

| Field | Value |
|-------|-------|
| **Branch** | `feature/billing-domain-models` |
| **PR Title** | `feat(billing): add domain value objects, entities, and repository interfaces` |
| **Target** | `develop` |
| **Est. Lines** | ~200-250 |
| **Depends On** | shared/domain (done) |

### PR Description

```markdown
## Summary
- Implements Plan enum (FREE, PRO, ENTERPRISE) and Quota value object (max_optimizations, max_tokens)
- Implements Subscription aggregate root with lifecycle (active, cancelled, expired)
- Implements UsageRecord entity for tracking resource consumption
- Defines ISubscriptionRepository and IUsageRepository interfaces (ABC)
- Adds SubscriptionFactory with plan-based defaults

## Motivation
Foundation for billing and quota enforcement. The QuotaEnforcementService (T2) and
Brandy's pipeline integration (A8) both depend on these domain models. Pure Python
with zero framework imports.

## Changes
- `billing/domain/value_objects.py` — Plan enum, Quota value object, plan-to-quota mapping
- `billing/domain/entities.py` — Subscription (aggregate root), UsageRecord (entity)
- `billing/domain/repository.py` — ISubscriptionRepository, IUsageRepository (ABC)
- `billing/domain/factories.py` — SubscriptionFactory
- `tests/test_billing.py` — Unit tests for value objects, entity lifecycle, factory

## Testing
- [x] Unit tests for Plan enum values and Quota immutability
- [x] Unit tests for Subscription status transitions (active→cancelled, active→expired)
- [x] Unit tests for SubscriptionFactory plan-based initialization
- [x] Unit tests for UsageRecord creation and validation
- [x] Zero framework imports verified in domain layer
```

### Files Touched

- `billing/domain/value_objects.py`
- `billing/domain/entities.py`
- `billing/domain/repository.py`
- `billing/domain/factories.py`
- `tests/test_billing.py`

---

## T2 — Quota Enforcement Service + Repository

| Field | Value |
|-------|-------|
| **Branch** | `feature/billing-quota-enforcement` |
| **PR Title** | `feat(billing): implement quota enforcement service and persistence layer` |
| **Target** | `develop` |
| **Est. Lines** | ~300-350 |
| **Depends On** | T1 |
| **⚠️ Blocks** | **A8** (Brandy's pipeline integration) |

### PR Description

```markdown
## Summary
- Implements QuotaEnforcementService (domain service): check_optimization_quota(),
  check_token_quota(), record_usage()
- Implements SubscriptionModel and UsageRecordModel (SQLAlchemy ORM)
- Implements SubscriptionRepository and UsageRepository with tenant-scoped queries
- Adds Alembic migration for subscriptions and usage_records tables
- Implements BillingApplicationService (get subscription, get usage summary)

## Motivation
Brandy's A8 (Full Pipeline Integration) calls check_quota() before running the
optimization pipeline. This PR unblocks Brandy by providing the quota enforcement
interface. Also provides the persistence layer for billing data.

## Changes
- `billing/domain/services.py` — QuotaEnforcementService (check_optimization_quota, check_token_quota, record_usage)
- `billing/application/services.py` — BillingApplicationService (get_subscription, get_usage_summary, create_subscription)
- `billing/infrastructure/models.py` — SubscriptionModel, UsageRecordModel (SQLAlchemy)
- `billing/infrastructure/repository_impl.py` — SubscriptionRepository, UsageRepository
- `alembic/versions/xxx_add_billing_tables.py` — Migration for subscriptions and usage_records
- `tests/test_billing.py` — Unit tests for quota enforcement, repository tests, tenant isolation test

## Testing
- [x] Unit test: check_optimization_quota returns True when under limit
- [x] Unit test: check_optimization_quota raises QuotaExceededError when over limit
- [x] Unit test: record_usage correctly increments usage count
- [x] Unit test: monthly quota resets at period boundary
- [x] Tenant isolation test: tenant_a_cannot_see_tenant_b_subscriptions
- [x] Tenant isolation test: tenant_a_cannot_see_tenant_b_usage_records
```

### Files Touched

- `billing/domain/services.py`
- `billing/application/services.py`
- `billing/infrastructure/models.py`
- `billing/infrastructure/repository_impl.py`
- `alembic/versions/xxx_add_billing_tables.py`
- `tests/test_billing.py`

---

## T3 — Billing API Routes + Stripe Gateway Stub

| Field | Value |
|-------|-------|
| **Branch** | `feature/billing-api-routes` |
| **PR Title** | `feat(billing): add billing API routes and Stripe gateway stub` |
| **Target** | `develop` |
| **Est. Lines** | ~250-300 |
| **Depends On** | T2 |

### PR Description

```markdown
## Summary
- Implements GET /billing/usage endpoint (current month usage summary)
- Implements GET /billing/subscription endpoint (active subscription details)
- Implements POST /billing/subscribe endpoint (create/upgrade subscription)
- Implements StripeGateway adapter (stubbed for MVP — returns mock responses)
- Adds Pydantic request/response DTOs for all billing endpoints

## Motivation
Exposes billing data to the frontend. The Stripe gateway is stubbed for MVP but
follows the Adapter pattern for easy real integration in Phase 2.

## Changes
- `billing/api/routes.py` — GET /usage, GET /subscription, POST /subscribe
- `billing/application/dto.py` — UsageSummaryDTO, SubscriptionDTO, SubscribeRequest
- `billing/application/commands.py` — SubscribeCommand
- `billing/infrastructure/stripe_gateway.py` — StripeGateway (stubbed, Adapter pattern)
- `tests/test_billing.py` — Integration tests for all 3 endpoints

## Testing
- [x] Integration test: GET /billing/usage returns correct usage for authenticated user
- [x] Integration test: GET /billing/subscription returns active subscription
- [x] Integration test: POST /billing/subscribe creates subscription with correct plan
- [x] Stripe gateway stub returns expected mock responses
- [x] Unauthenticated requests return 401
```

### Files Touched

- `billing/api/routes.py`
- `billing/application/dto.py`
- `billing/application/commands.py`
- `billing/infrastructure/stripe_gateway.py`
- `tests/test_billing.py`

---

## T4 — Domain Event Bus Implementation

| Field | Value |
|-------|-------|
| **Branch** | `feature/shared-event-bus` |
| **PR Title** | `feat(shared): implement in-process domain event bus` |
| **Target** | `develop` |
| **Est. Lines** | ~120-150 |
| **Depends On** | shared/domain (done) |

### PR Description

```markdown
## Summary
- Implements InProcessEventBus (Observer pattern) fulfilling IEventBus interface
- Supports async handler registration and dispatch
- Provides subscribe() for event type → handler mapping
- Provides publish() that fans out to all registered handlers
- Errors in one handler do not block other handlers (logged, not raised)

## Motivation
Cross-context communication (e.g., OptimizationCompleted → Billing token tracking)
requires a working event bus. Currently IEventBus exists but InProcessEventBus is
a stub. This PR enables the Observer pattern used throughout the architecture.

## Changes
- `shared/infrastructure/event_bus_impl.py` — InProcessEventBus (implements IEventBus)
- `tests/test_shared.py` — Unit tests for publish/subscribe, multi-handler fan-out, error isolation

## Testing
- [x] Unit test: subscribe + publish delivers event to handler
- [x] Unit test: multiple handlers for same event type all receive event
- [x] Unit test: handler exception is logged but does not block other handlers
- [x] Unit test: unsubscribed event types are silently ignored
```

### Files Touched

- `shared/infrastructure/event_bus_impl.py`
- `tests/test_shared.py`

---

## T5 — Billing Event Handler (OptimizationCompleted)

| Field | Value |
|-------|-------|
| **Branch** | `feature/billing-event-handler` |
| **PR Title** | `feat(billing): add OptimizationCompleted event handler for token tracking` |
| **Target** | `develop` |
| **Est. Lines** | ~100-150 |
| **Depends On** | T2, T4 |

### PR Description

```markdown
## Summary
- Implements OptimizationCompletedEventHandler that subscribes to
  OptimizationCompleted domain events
- Extracts token_usage from event payload and records via UsageRepository
- Registers handler with event bus during application startup
- Handles errors gracefully — never blocks the optimization flow

## Motivation
Closes the loop between AI pipeline execution and billing. When Brandy's pipeline
completes, it publishes an OptimizationCompleted event carrying token counts. This
handler records that usage for quota tracking.

## Changes
- `billing/application/event_handlers.py` — OptimizationCompletedEventHandler
- `main.py` or startup hook — Register handler with event bus
- `tests/test_billing.py` — Unit tests for event handling and usage recording

## Testing
- [x] Unit test: handler correctly extracts token_usage and records usage
- [x] Unit test: handler error does not propagate (graceful degradation)
- [x] Unit test: handler ignores events with missing payload fields
- [x] Integration test: publish event → verify usage record created
```

### Files Touched

- `billing/application/event_handlers.py`
- `main.py` (or application startup)
- `tests/test_billing.py`

---

## T6 — Frontend API Client + Auth Flow

| Field | Value |
|-------|-------|
| **Branch** | `feature/frontend-api-auth` |
| **PR Title** | `feat(frontend): implement API client, auth hooks, and login/register pages` |
| **Target** | `develop` |
| **Est. Lines** | ~350-400 |
| **Depends On** | identity API (done) |

### PR Description

```markdown
## Summary
- Implements createApiClient() with JWT token injection and auto-refresh
- Implements useAuth() hook with login, register, logout, token management
- Implements LoginPage with email/password form, validation, error display
- Implements RegisterPage with email, password, tenant name, validation
- Adds AuthProvider context for global auth state
- Stores JWT in httpOnly cookie or secure localStorage with refresh logic

## Motivation
Every frontend page depends on authentication. This PR wires the frontend to the
existing identity API, enabling all subsequent UI work to use authenticated requests.

## Changes
- `src/lib/api/client.ts` — createApiClient() with JWT interceptor, refresh logic
- `src/hooks/useAuth.ts` — Full auth state: login, register, logout, refresh, user state
- `src/providers/AuthProvider.tsx` — Auth context provider wrapping the app
- `src/app/(auth)/login/page.tsx` — Login form with validation and error handling
- `src/app/(auth)/register/page.tsx` — Registration form with tenant name
- `src/lib/api/types.ts` — Add AuthResponse, UserDTO, LoginRequest, RegisterRequest types

## Testing
- [x] Login form submits correct payload and handles success/error
- [x] Register form validates inputs and creates account
- [x] JWT token persisted and injected into subsequent requests
- [x] Token refresh triggers automatically on 401 response
- [x] Logout clears token and redirects to login page
```

### Files Touched

- `frontend/src/lib/api/client.ts`
- `frontend/src/hooks/useAuth.ts`
- `frontend/src/providers/AuthProvider.tsx`
- `frontend/src/app/(auth)/login/page.tsx`
- `frontend/src/app/(auth)/register/page.tsx`
- `frontend/src/lib/api/types.ts`

---

## T7 — Frontend Resume Management UI

| Field | Value |
|-------|-------|
| **Branch** | `feature/frontend-resume-ui` |
| **PR Title** | `feat(frontend): implement resume upload, list, and management pages` |
| **Target** | `develop` |
| **Est. Lines** | ~300-380 |
| **Depends On** | T6 |

### PR Description

```markdown
## Summary
- Implements ResumeUploader component with drag-and-drop PDF upload
- Implements ResumesPage with resume list (cards showing filename, sections, date)
- Implements useResume() hook with upload, list, delete operations
- Implements resume detail view showing parsed sections
- Adds loading states, error handling, and empty state UI

## Motivation
Resume management is the entry point for the user journey. Users must upload a
resume before they can optimize it. The backend API is fully ready.

## Changes
- `src/components/resume/ResumeUploader.tsx` — Drag-and-drop PDF upload widget
- `src/app/(dashboard)/resumes/page.tsx` — Resume list with cards
- `src/hooks/useResume.ts` — upload, list, get, delete operations via API client
- `src/lib/api/types.ts` — Add ResumeDTO, ResumeListItemDTO, UploadResponse types

## Testing
- [x] Upload component accepts PDF files and shows progress
- [x] Resume list displays uploaded resumes with correct metadata
- [x] Delete action removes resume and refreshes list
- [x] Error states displayed for failed uploads (file too large, non-PDF)
- [x] Empty state shown when no resumes uploaded
```

### Files Touched

- `frontend/src/components/resume/ResumeUploader.tsx`
- `frontend/src/app/(dashboard)/resumes/page.tsx`
- `frontend/src/hooks/useResume.ts`
- `frontend/src/lib/api/types.ts`

---

## T8 — Frontend Optimization Workflow UI

| Field | Value |
|-------|-------|
| **Branch** | `feature/frontend-optimization-ui` |
| **PR Title** | `feat(frontend): implement optimization workflow with JD input, score card, and gap report` |
| **Target** | `develop` |
| **Est. Lines** | ~350-400 |
| **Depends On** | T6, T7, Brandy's A8 API (can use mock data first) |

### PR Description

```markdown
## Summary
- Implements OptimizePage with full optimization workflow
- Implements JDInputPanel with character count and validation
- Implements OptimizationContainer orchestrating the workflow (select resume → paste JD → optimize)
- Implements OptimizationView with side-by-side diff (original vs optimized)
- Implements ScoreCard with ATS score gauge and category breakdown
- Implements GapReport with missing skills and recommendations
- Implements useOptimization() hook for API calls and state management
- Adds real-time progress tracker during pipeline execution

## Motivation
Core user-facing feature. The optimization UI ties together resume selection,
JD input, and result display. Can be developed with mock data before A8 API
is ready, then wired to real API.

## Changes
- `src/app/(dashboard)/optimize/page.tsx` — Optimization workspace page
- `src/containers/OptimizationContainer.tsx` — Workflow orchestration
- `src/components/optimization/JDInputPanel.tsx` — JD text input with validation
- `src/components/optimization/OptimizationView.tsx` — Side-by-side diff view
- `src/components/optimization/ScoreCard.tsx` — ATS score gauge + breakdown
- `src/components/optimization/GapReport.tsx` — Gap analysis display
- `src/hooks/useOptimization.ts` — optimize, getSession, listSessions
- `src/lib/api/types.ts` — Add OptimizationRequest, OptimizationResponse, SessionDTO types

## Testing
- [x] JD input validates minimum length and shows character count
- [x] Optimization triggers correctly with selected resume + JD text
- [x] Score card displays correct scores with visual breakdown
- [x] Gap report renders missing skills and recommendations
- [x] Progress tracker shows current pipeline step
- [x] Error states handled for failed optimizations
```

### Files Touched

- `frontend/src/app/(dashboard)/optimize/page.tsx`
- `frontend/src/containers/OptimizationContainer.tsx`
- `frontend/src/components/optimization/JDInputPanel.tsx`
- `frontend/src/components/optimization/OptimizationView.tsx`
- `frontend/src/components/optimization/ScoreCard.tsx`
- `frontend/src/components/optimization/GapReport.tsx`
- `frontend/src/hooks/useOptimization.ts`
- `frontend/src/lib/api/types.ts`

---

## T9 — Frontend Interview Prep UI

| Field | Value |
|-------|-------|
| **Branch** | `feature/frontend-interview-ui` |
| **PR Title** | `feat(frontend): implement interview prep and cover letter UI` |
| **Target** | `develop` |
| **Est. Lines** | ~250-300 |
| **Depends On** | T6, Brandy's A9-A10 API (can use mock data first) |

### PR Description

```markdown
## Summary
- Implements InterviewPrep component with accordion Q&A display
- Questions grouped by category (behavioral, technical, situational) with difficulty badges
- STAR-format answers displayed with highlighted structure
- Implements cover letter generation UI with tone selection (formal/conversational/enthusiastic)
- Implements interview prep page linking from optimization session

## Motivation
Completes the frontend user journey. After optimization, users can generate
interview questions and cover letters — the final feature of the MVP.

## Changes
- `src/components/interview/InterviewPrep.tsx` — Accordion Q&A with category tabs and difficulty badges
- `src/app/(dashboard)/interview/page.tsx` — Interview prep page (or section within optimization result)
- `src/hooks/useInterview.ts` — generateQuestions, generateCoverLetter hooks
- `src/lib/api/types.ts` — Add InterviewPrepResponse, InterviewQuestionDTO, CoverLetterResponse types

## Testing
- [x] Questions displayed in categorized accordion format
- [x] STAR answers clearly structured (Situation/Task/Action/Result)
- [x] Cover letter tone selection works and generates appropriate content
- [x] Loading states during generation
- [x] Error handling for failed generation
```

### Files Touched

- `frontend/src/components/interview/InterviewPrep.tsx`
- `frontend/src/app/(dashboard)/interview/page.tsx`
- `frontend/src/hooks/useInterview.ts`
- `frontend/src/lib/api/types.ts`

---

# Summary Tables

## Brandy (Person A) — AI Workflow

| PR | Branch | Title | Est. Lines | Depends On |
|----|--------|-------|-----------|------------|
| A1 | `feature/optimization-domain-models` | `feat(optimization): add domain value objects, entities, and repository interface` | ~250-300 | shared/domain (done) |
| A2 | `feature/optimization-base-agent` | `feat(optimization): add BaseAgent template method and LangGraph state schema` | ~200-280 | A1 |
| A3 | `feature/optimization-jd-analyzer` | `feat(optimization): implement JD analyzer agent with structured extraction` | ~150-200 | A2 |
| A4 | `feature/optimization-rag-retriever` | `feat(optimization): implement RAG retriever agent with vector search` | ~150-200 | A2 |
| A5 | `feature/optimization-resume-rewriter` | `feat(optimization): implement resume rewriter agent for multi-section optimization` | ~200-300 | A3, A4 |
| A6 | `feature/optimization-ats-scorer` | `feat(optimization): implement ATS scorer with rule-based fast-path` | ~200-280 | A5 |
| A7 | `feature/optimization-gap-analyzer` | `feat(optimization): implement gap analyzer agent` | ~120-180 | A6 |
| A8 | `feature/optimization-pipeline` | `feat(optimization): wire full pipeline with application service, routes, and persistence` | ~350-400 | A3-A7, **T2** |
| A9 | `feature/interview-question-gen` | `feat(interview): implement question generator with STAR-format answers` | ~300-380 | A8 |
| A10 | `feature/interview-cover-letter` | `feat(interview): implement cover letter generator with tone selection` | ~150-200 | A9 |

**Brandy total**: ~2,070-2,720 lines across 10 PRs

## Tomie (Person B) — Platform & Infrastructure

| PR | Branch | Title | Est. Lines | Depends On | Blocks |
|----|--------|-------|-----------|------------|--------|
| T1 | `feature/billing-domain-models` | `feat(billing): add domain value objects, entities, and repository interfaces` | ~200-250 | shared/domain (done) | T2 |
| T2 | `feature/billing-quota-enforcement` | `feat(billing): implement quota enforcement service and persistence layer` | ~300-350 | T1 | **A8** |
| T3 | `feature/billing-api-routes` | `feat(billing): add billing API routes and Stripe gateway stub` | ~250-300 | T2 | — |
| T4 | `feature/shared-event-bus` | `feat(shared): implement in-process domain event bus` | ~120-150 | shared/domain (done) | T5 |
| T5 | `feature/billing-event-handler` | `feat(billing): add OptimizationCompleted event handler for token tracking` | ~100-150 | T2, T4 | — |
| T6 | `feature/frontend-api-auth` | `feat(frontend): implement API client, auth hooks, and login/register pages` | ~350-400 | identity API (done) | T7, T8, T9 |
| T7 | `feature/frontend-resume-ui` | `feat(frontend): implement resume upload, list, and management pages` | ~300-380 | T6 | — |
| T8 | `feature/frontend-optimization-ui` | `feat(frontend): implement optimization workflow with JD input, score card, and gap report` | ~350-400 | T6, T7, A8 API | — |
| T9 | `feature/frontend-interview-ui` | `feat(frontend): implement interview prep and cover letter UI` | ~250-300 | T6, A9-A10 API | — |

**Tomie total**: ~2,220-2,680 lines across 9 PRs

## Combined Project Total

| Developer | PRs | Est. Lines |
|---|---|---|
| Brandy (Person A) | 10 | ~2,070-2,720 |
| Tomie (Person B) | 9 | ~2,220-2,680 |
| **Total** | **19** | **~4,290-5,400** |

---

## Cross-Team Dependencies (Critical Path)

```
Tomie T1 → T2 ─────────────────► Brandy A8 (quota check)
                                     │
Brandy A8 (publishes event) ────► Tomie T5 (records token usage)
                                     │
Brandy A8 API ready ────────────► Tomie T8 (optimization UI wires to real API)
Brandy A9-A10 API ready ────────► Tomie T9 (interview UI wires to real API)
```

**Key takeaway**: Tomie must complete **T1 + T2** before Brandy reaches **A8**.
Given A8 is Brandy's 8th PR and T2 is Tomie's 2nd, there is ample buffer.
