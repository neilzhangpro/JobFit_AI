# JobFit AI — PR Feature Plan (AI Workflow)

This document defines the 10 Pull Requests required to implement the full AI Workflow
(Optimization Pipeline + Interview Preparation). Each PR follows the conventions in
[06-git-workflow-guide.md](../docs/06-git-workflow-guide.md) and implements a section of
[07-ai-workflow-architecture.md](../docs/07-ai-workflow-architecture.md).

**Rules applied to every PR:**

- Branch from `develop`, target `develop`.
- Branch naming: `feature/<bounded-context>-<description>`.
- PR title: Conventional Commits `feat(scope): description`.
- Size: < 400 lines of changed code.
- Tests included (test-first workflow).
- PR description includes Summary, Motivation, Changes, Testing.
- Squash and merge when approved.

---

## Dependency Graph

```
PR 1 (domain models)
  └── PR 2 (BaseAgent + state schema)
        ├── PR 3 (JD Analyzer)      ← can run in parallel
        ├── PR 4 (RAG Retriever)    ← can run in parallel
        │     └── PR 5 (Resume Rewriter)
        │           └── PR 6 (ATS Scorer)
        │                 └── PR 7 (Gap Analyzer)
        └────────────────── PR 8 (Full Pipeline Integration) ← depends on PRs 3-7
                              └── PR 9 (Interview Question Generator)
                                    └── PR 10 (Cover Letter Generator)
```

---

## PR 1 — Optimization Domain Models

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-domain-models` |
| **PR Title** | `feat(optimization): add domain value objects, entities, and repository interface` |
| **Target** | `develop` |
| **Est. Lines** | ~250-300 |

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

## PR 2 — BaseAgent + State Schema + Graph Skeleton

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-base-agent` |
| **PR Title** | `feat(optimization): add BaseAgent template method and LangGraph state schema` |
| **Target** | `develop` |
| **Est. Lines** | ~200-280 |

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

## PR 3 — JD Analyzer Agent

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-jd-analyzer` |
| **PR Title** | `feat(optimization): implement JD analyzer agent with structured extraction` |
| **Target** | `develop` |
| **Est. Lines** | ~150-200 |

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

## PR 4 — RAG Retriever Agent

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-rag-retriever` |
| **PR Title** | `feat(optimization): implement RAG retriever agent with vector search` |
| **Target** | `develop` |
| **Est. Lines** | ~150-200 |

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

## PR 5 — Resume Rewriter Agent

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-resume-rewriter` |
| **PR Title** | `feat(optimization): implement resume rewriter agent for multi-section optimization` |
| **Target** | `develop` |
| **Est. Lines** | ~200-300 |

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

## PR 6 — ATS Scorer Agent

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-ats-scorer` |
| **PR Title** | `feat(optimization): implement ATS scorer with rule-based fast-path` |
| **Target** | `develop` |
| **Est. Lines** | ~200-280 |

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

## PR 7 — Gap Analyzer Agent

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-gap-analyzer` |
| **PR Title** | `feat(optimization): implement gap analyzer agent` |
| **Target** | `develop` |
| **Est. Lines** | ~120-180 |

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

## PR 8 — Full Pipeline Integration

| Field | Value |
|-------|-------|
| **Branch** | `feature/optimization-pipeline` |
| **PR Title** | `feat(optimization): wire full pipeline with application service, routes, and persistence` |
| **Target** | `develop` |
| **Est. Lines** | ~350-400 |

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

## PR 9 — Interview Question Generator

| Field | Value |
|-------|-------|
| **Branch** | `feature/interview-question-gen` |
| **PR Title** | `feat(interview): implement question generator with STAR-format answers` |
| **Target** | `develop` |
| **Est. Lines** | ~300-380 |

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

## PR 10 — Cover Letter Generator

| Field | Value |
|-------|-------|
| **Branch** | `feature/interview-cover-letter` |
| **PR Title** | `feat(interview): implement cover letter generator with tone selection` |
| **Target** | `develop` |
| **Est. Lines** | ~150-200 |

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

## Summary Table

| PR | Branch | Title | Est. Lines | Depends On |
|----|--------|-------|-----------|------------|
| 1 | `feature/optimization-domain-models` | `feat(optimization): add domain value objects, entities, and repository interface` | ~250-300 | shared/domain (done) |
| 2 | `feature/optimization-base-agent` | `feat(optimization): add BaseAgent template method and LangGraph state schema` | ~200-280 | PR 1 |
| 3 | `feature/optimization-jd-analyzer` | `feat(optimization): implement JD analyzer agent with structured extraction` | ~150-200 | PR 2 |
| 4 | `feature/optimization-rag-retriever` | `feat(optimization): implement RAG retriever agent with vector search` | ~150-200 | PR 2 |
| 5 | `feature/optimization-resume-rewriter` | `feat(optimization): implement resume rewriter agent for multi-section optimization` | ~200-300 | PR 3, 4 |
| 6 | `feature/optimization-ats-scorer` | `feat(optimization): implement ATS scorer with rule-based fast-path` | ~200-280 | PR 5 |
| 7 | `feature/optimization-gap-analyzer` | `feat(optimization): implement gap analyzer agent` | ~120-180 | PR 6 |
| 8 | `feature/optimization-pipeline` | `feat(optimization): wire full pipeline with application service, routes, and persistence` | ~350-400 | PR 3-7 |
| 9 | `feature/interview-question-gen` | `feat(interview): implement question generator with STAR-format answers` | ~300-380 | PR 8 |
| 10 | `feature/interview-cover-letter` | `feat(interview): implement cover letter generator with tone selection` | ~150-200 | PR 9 |

**Total estimated lines**: ~2,070-2,720 across 10 PRs.
