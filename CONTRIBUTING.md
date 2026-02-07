# JobFit AI — Developer Onboarding Guide

Welcome to the JobFit AI project! This guide is written for **Brand (@brandyxie100)**, who is responsible for the **AI Workflow** part of the system (resume optimization pipeline and interview preparation). Follow this document step by step to get up and running.

---

## 1. Your Role and Responsibilities

You are **Person A (AI Workflow)**, responsible for:

| Context | Directory | What You Build |
|---------|-----------|----------------|
| **Optimization** | `backend/optimization/` | LangGraph agentic pipeline: JD analysis, RAG retrieval, resume rewriting, ATS scoring, gap analysis |
| **Interview** | `backend/interview/` | Interview question generation (behavioral/technical/situational with STAR answers), cover letter generation |

Your teammate **Tomie (@neilzhangpro)** handles everything else: auth, resume upload/parsing, billing, frontend, Docker, CI/CD.

**Shared areas** (both of you must approve changes): `backend/shared/domain/`, `backend/config.py`, `docs/`.

---

## 2. First-Time Setup

### 2.1 Prerequisites

Install these tools on your machine:

- **Docker Desktop** (24+): https://docs.docker.com/get-docker/
- **Git**: https://git-scm.com/
- **Python 3.11+**: https://www.python.org/ (for local development)
- **Make**: Pre-installed on macOS; `brew install make` if missing

### 2.2 Clone the Repository

```bash
git clone https://github.com/neilzhangpro/JobFit_AI.git
cd JobFit_AI
```

### 2.3 Configure Environment

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys:

```bash
# These are REQUIRED for your AI workflow work:
OPENAI_API_KEY=sk-your-real-key-here
DEEPSEEK_API_KEY=sk-your-real-key-here    # Optional if using OpenAI only
LLM_PROVIDER=openai                       # or "deepseek"
```

### 2.4 Start the Project

```bash
make dev-build
```

This starts 6 containers (frontend, backend, PostgreSQL, Redis, ChromaDB, MinIO). Wait until you see the backend startup message.

### 2.5 Verify It Works

| Check | URL / Command |
|-------|---------------|
| Backend health | http://localhost:8000/api/health |
| Swagger docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |

### 2.6 Configure Git (One-Time)

```bash
git config user.name "Brand"
git config user.email "your-email@example.com"
git config pull.rebase true
git config fetch.prune true
```

---

## 3. Your Files — What Goes Where

### 3.1 Optimization Context (Core Domain)

```
backend/optimization/
├── domain/                          # Pure business logic (NO framework imports!)
│   ├── entities.py                  # OptimizationSession (Aggregate Root)
│   ├── value_objects.py             # JDAnalysis, ATSScore, GapReport, SessionStatus
│   ├── repository.py               # IOptimizationRepository (interface)
│   ├── services.py                  # Scoring validation, status transition rules
│   └── factories.py                 # OptimizationSessionFactory
│
├── application/                     # Use case orchestration
│   ├── services.py                  # OptimizationApplicationService
│   ├── dto.py                       # OptimizationRequest, OptimizationResponse
│   └── commands.py                  # RunOptimizationCommand
│
├── infrastructure/                  # External integrations
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── repository_impl.py          # Repository with tenant_id scoping
│   └── agents/                      # <<< YOUR MAIN WORK AREA >>>
│       ├── base_agent.py            # BaseAgent (Template Method pattern)
│       ├── graph.py                 # LangGraph state machine
│       ├── jd_analyzer.py           # Step 1: Extract JD requirements
│       ├── rag_retriever.py         # Step 2: Vector search for relevant resume chunks
│       ├── resume_rewriter.py       # Step 3: Rewrite bullets with JD context
│       ├── ats_scorer.py            # Step 4: Score ATS compatibility
│       └── gap_analyzer.py          # Step 5: Identify missing skills
│
└── api/
    └── routes.py                    # POST /optimize, GET /sessions
```

### 3.2 Interview Context

```
backend/interview/
├── domain/
│   ├── entities.py                  # InterviewPrep (Aggregate Root)
│   ├── value_objects.py             # InterviewQuestion, CoverLetter
│   ├── repository.py               # IInterviewPrepRepository
│   └── factories.py                 # InterviewPrepFactory
│
├── application/
│   ├── services.py                  # InterviewApplicationService
│   └── dto.py                       # InterviewPrepResponse
│
├── infrastructure/
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── repository_impl.py          # Repository implementation
│   └── agents/                      # <<< YOUR WORK AREA >>>
│       ├── question_generator.py    # Generate interview Q&A
│       └── cover_letter_generator.py # Generate cover letters
│
└── api/
    └── routes.py                    # POST /interview-prep, POST /cover-letter
```

### 3.3 Test Files

```
backend/tests/
├── test_optimization.py             # Your optimization tests
└── test_interview.py                # Your interview tests
```

---

## 4. Architecture Rules (MUST Follow)

### 4.1 DDD Layer Rules

```
API Layer  →  Application Layer  →  Domain Layer
                    ↓
             Infrastructure Layer
```

| Layer | What to Import | What NOT to Import |
|-------|---------------|-------------------|
| **domain/** | Only Python stdlib | NO FastAPI, SQLAlchemy, LangChain, Pydantic |
| **application/** | From domain/ only | NO infrastructure/ (use interfaces + DI) |
| **infrastructure/** | From domain/ + external libs | Implement domain interfaces here |
| **api/** | From application/ only | NO domain entities (use DTOs) |

**The #1 rule**: Your `domain/` layer must have ZERO framework imports. If you see `from sqlalchemy import ...` or `from langchain import ...` in a domain file, that's a violation.

### 4.2 Multi-Tenant Isolation

Every database query MUST include `tenant_id` filtering. This is a security requirement.

```python
# GOOD
stmt = select(Model).where(
    Model.id == session_id,
    Model.tenant_id == self._tenant_id,  # ALWAYS filter by tenant
)

# BAD (SECURITY BUG)
stmt = select(Model).where(Model.id == session_id)
```

### 4.3 AI Agent Pattern (Template Method)

All agents must inherit from `BaseAgent` and follow this skeleton:

```python
class JDAnalyzerAgent(BaseAgent):
    """Extracts structured requirements from JD text."""

    def prepare(self, state: OptimizationState) -> str:
        """Build the LLM prompt from current state."""
        ...

    def execute(self, prompt: str) -> str:
        """Call LLM with the prompt."""
        ...

    def parse_output(self, raw_output: str) -> dict:
        """Parse LLM response into structured data."""
        ...
```

---

## 5. Development Workflow

### 5.1 The Golden Rule: Test First

Every feature you build follows this order:

```
1. Create branch  →  2. Write tests  →  3. Implement  →  4. Verify  →  5. Push + PR
```

### 5.2 Step-by-Step Example

Let's say you're implementing the JD Analyzer agent:

```bash
# 1. Make sure you're on develop and up to date
git checkout develop
git pull origin develop

# 2. Create a feature branch
git checkout -b feature/optimization-jd-analyzer

# 3. Write tests FIRST (in tests/test_optimization.py)
#    - test_jd_analyzer_extracts_hard_skills
#    - test_jd_analyzer_extracts_soft_skills
#    - test_jd_analyzer_handles_empty_jd

# 4. Implement the agent (in optimization/infrastructure/agents/jd_analyzer.py)
#    Write the simplest code that makes your tests pass.

# 5. Run linter and tests locally
make lint
make test-backend

# 6. Commit with Conventional Commits format
git add .
git commit -m "feat(optimization): implement JD analyzer agent

Extracts hard skills, soft skills, responsibilities, and
qualifications from raw JD text using GPT-4o structured output.

Closes #12"

# 7. Push and create PR
git push -u origin feature/optimization-jd-analyzer
```

Then go to GitHub and create a PR: **develop** <- **feature/optimization-jd-analyzer**

### 5.3 Suggested Implementation Order

| Order | Task | Branch Name | Files |
|-------|------|-------------|-------|
| 1 | BaseAgent + LangGraph state schema | `feature/optimization-base-agent` | `base_agent.py`, `graph.py`, `value_objects.py` |
| 2 | JD Analyzer agent | `feature/optimization-jd-analyzer` | `jd_analyzer.py` |
| 3 | RAG Retriever agent | `feature/optimization-rag-retriever` | `rag_retriever.py` |
| 4 | Resume Rewriter agent | `feature/optimization-resume-rewriter` | `resume_rewriter.py` |
| 5 | ATS Scorer agent | `feature/optimization-ats-scorer` | `ats_scorer.py` |
| 6 | Gap Analyzer agent | `feature/optimization-gap-analyzer` | `gap_analyzer.py` |
| 7 | Full pipeline integration | `feature/optimization-pipeline` | `graph.py`, `services.py` |
| 8 | Interview question generator | `feature/interview-question-gen` | `question_generator.py` |
| 9 | Cover letter generator | `feature/interview-cover-letter` | `cover_letter_generator.py` |

Each task = one branch = one PR. Keep PRs small (< 400 lines).

---

## 6. Commit Message Format

All commits must use **Conventional Commits**:

```
<type>(<scope>): <short description>
```

### Your Common Types and Scopes

```bash
# New feature
git commit -m "feat(optimization): add ATS scoring agent"

# Bug fix
git commit -m "fix(optimization): handle empty JD text gracefully"

# Tests only
git commit -m "test(optimization): add unit tests for gap analyzer"

# Refactor (no feature change)
git commit -m "refactor(optimization): extract prompt templates to constants"

# Interview context
git commit -m "feat(interview): implement STAR-format answer generator"
```

**Your scopes**: `optimization`, `interview` (these are the only two you should use).

---

## 7. Pull Request Process

### 7.1 Creating a PR

1. Push your branch: `git push -u origin feature/optimization-xxx`
2. Go to GitHub, click **"Compare & pull request"**
3. Set **base: develop** (NEVER target main directly)
4. Fill in the description using this template:

```markdown
## Summary
- Implements the JDAnalyzerAgent that extracts structured requirements from JD text
- Adds 5 unit tests covering edge cases

## Motivation
First agent in the optimization pipeline. Required before RAG retriever can work.
Closes #12

## Changes
- `optimization/infrastructure/agents/jd_analyzer.py` — New agent
- `optimization/domain/value_objects.py` — Added JDAnalysis value object
- `tests/test_optimization.py` — Added 5 test cases

## Testing
- [x] Unit tests pass locally
- [x] `make lint` passes
- [x] Tested with a real JD from LinkedIn
```

### 7.2 What Happens After You Create a PR

1. **CI Pipeline** runs automatically (6 checks: lint, type check, tests, coverage, secret scan, docker build)
2. **CodeRabbit AI** posts a review comment with suggestions
3. **Tomie (@neilzhangpro)** gets notified as reviewer for shared files
4. Fix any issues, push new commits to the same branch
5. Once approved and CI is green, click **"Squash and merge"**
6. Delete the feature branch

### 7.3 Keep Your Branch in Sync (Do This Daily!)

```bash
git fetch origin
git rebase origin/develop
```

If there are conflicts:
```bash
# Resolve conflicts in your editor, then:
git add .
git rebase --continue
git push --force-with-lease
```

---

## 8. Useful Commands

| Command | What It Does |
|---------|-------------|
| `make dev` | Start all services |
| `make dev-build` | Start with fresh image build |
| `make down` | Stop all services |
| `make test` | Run all tests |
| `make test-backend` | Run backend tests only |
| `make lint` | Run all linters + type checks |
| `make logs` | Tail all container logs |
| `make clean` | Full reset (delete volumes + images) |

---

## 9. Key Documents to Read

Before you start coding, read these documents (in this order):

| # | Document | Why |
|---|----------|-----|
| 1 | [System Architecture](docs/02-system-architecture.md) Section 9 | LangGraph state machine design — your blueprint |
| 2 | [Technical Standards](docs/04-technical-standards.md) Sections 3-5 | DDD layer rules, testing standards, design patterns |
| 3 | [Technology Selection](docs/03-technology-selection.md) Section 4 | LangChain, LangGraph, LLM provider details |
| 4 | [Requirements Analysis](docs/01-requirements-analysis.md) Section 4.4-4.5 | Functional requirements for optimization and interview |
| 5 | [Operations Manual](docs/05-operations-manual.md) | How to run, test, and troubleshoot |
| 6 | [Git Workflow Guide](docs/06-git-workflow-guide.md) | Full git conventions reference |

---

## 10. FAQ

**Q: I need to change a file in `backend/shared/domain/`. Can I?**
A: Yes, but the PR will require approval from both you AND Tomie. Coordinate via chat first.

**Q: I need to add a new Python dependency (e.g., a LangChain plugin).**
A: Add it to `backend/requirements.txt` and commit. The Docker image will pick it up on next build.

**Q: My tests need a database. How do I set up test fixtures?**
A: Use `factory_boy` and pytest fixtures. See `backend/tests/conftest.py` for shared fixtures. Mark DB tests with `@pytest.mark.integration`.

**Q: How do I test my LangGraph agents locally without Docker?**
A: Start only the data services, then run Python directly:
```bash
# Terminal 1: Start data services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up postgres redis chromadb minio

# Terminal 2: Run backend locally
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/jobfit_dev"
export CHROMA_HOST="localhost"
export OPENAI_API_KEY="sk-your-key"
uvicorn main:app --reload
```

**Q: The CI failed on my PR. What do I do?**
A: Click the failed check on GitHub to see the error log. Common issues:
- `ruff check` — Line too long or import order. Run `make lint` locally first.
- `mypy` — Missing type annotations. Add them.
- `prettier` — Frontend formatting. Run `cd frontend && npx prettier --write src/`.
- Tests — Check the test output for assertion errors.

**Q: How do I handle merge conflicts?**
A: See [Git Workflow Guide](docs/06-git-workflow-guide.md) Section 7. Short version:
```bash
git fetch origin && git rebase origin/develop
# Fix conflicts, then: git add . && git rebase --continue
# Push: git push --force-with-lease
```

---

## 11. Quick Reference Card

```
Daily routine:
  git checkout develop && git pull
  git checkout -b feature/optimization-<task>
  ... write tests first, then implement ...
  make lint && make test-backend
  git add . && git commit -m "feat(optimization): ..."
  git push -u origin feature/optimization-<task>
  → Create PR on GitHub (target: develop)
  → Wait for CI + review → Squash and merge → Delete branch

Commit format:
  feat(optimization): add JD analyzer agent
  fix(interview): handle empty question list
  test(optimization): add ATS scorer edge cases

Your directories:
  backend/optimization/    ← Resume optimization pipeline
  backend/interview/       ← Interview prep + cover letter
  backend/tests/test_optimization.py
  backend/tests/test_interview.py
```

---

If you have any questions, reach out to Tomie (@neilzhangpro) or check the docs in the `docs/` folder. Happy coding!
