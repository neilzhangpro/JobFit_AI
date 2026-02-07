<div align="center">

# JobFit AI

**An Intelligent Resume Optimization Agent**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.x-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1+-1C3C3C?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6F00?style=for-the-badge)](https://www.trychroma.com/)
[![Docker](https://img.shields.io/badge/Docker-24+-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?style=for-the-badge&logo=amazonec2&logoColor=white)](https://aws.amazon.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI/CD-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/features/actions)

---

*A SaaS platform that leverages LLMs and RAG to help job seekers tailor resumes to specific job descriptions, maximize ATS compatibility, and prepare for interviews.*

</div>

---

## Overview

In the competitive job market, candidates struggle to tailor resumes to specific Job Descriptions (JDs) and Applicant Tracking Systems (ATS). **JobFit AI** automates this process using an agentic AI workflow:

1. **Upload** your existing resume (PDF).
2. **Paste** the target job description.
3. **Receive** an optimized resume with JD-aligned keywords, an ATS match score, a gap analysis report, and interview preparation Q&A.

Unlike generic rewriting tools, JobFit AI uses **Retrieval-Augmented Generation (RAG)** to match your most relevant experiences to each JD requirement, producing context-aware optimizations.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Resume Optimization** | AI rewrites bullet points to embed JD keywords, optimize action verbs, and quantify achievements |
| **ATS Scoring** | Calculates an ATS compatibility score (0-100%) with category-level breakdown |
| **Gap Analysis** | Identifies JD-required skills missing from your resume with actionable recommendations |
| **Interview Prep** | Generates 8-10 behavioral, technical, and situational interview questions with STAR-format answer suggestions |
| **Cover Letter** | Auto-generates a tailored cover letter based on JD and optimized resume |
| **Side-by-Side Diff** | Visual comparison of original vs. optimized resume with highlighted changes |
| **Multi-Tenant SaaS** | Row-level data isolation; supports individual users and organizations |

---

## Architecture

The project follows **Domain-Driven Design (DDD)** with a clean layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
├─────────────────────────────────────────────────────────┤
│                   API Layer (FastAPI)                    │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ Identity │  Resume  │Optimiza- │Interview │   Billing   │
│ Context  │  Context │  tion    │ Context  │   Context   │
│          │          │ Context  │          │             │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│              AI Pipeline (LangChain + LangGraph)         │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│PostgreSQL│  Redis   │ ChromaDB │  MinIO   │  LLM API   │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
```

Each bounded context follows a strict 4-layer structure:

```
context/
├── domain/           # Pure business logic (zero external dependencies)
├── application/      # Use case orchestration, DTOs, commands
├── infrastructure/   # SQLAlchemy, external APIs, AI agents
└── api/              # FastAPI routes
```

> See [System Architecture](docs/02-system-architecture.md) for detailed diagrams and data flow.

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14, TypeScript 5, Tailwind CSS 3 |
| **Backend** | Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2 (async) |
| **AI/ML** | LangChain, LangGraph, OpenAI GPT-4o / DeepSeek |
| **Database** | PostgreSQL 16, Redis 7, ChromaDB (vector store) |
| **Storage** | MinIO / AWS S3 |
| **Auth** | JWT (python-jose + passlib/bcrypt) |
| **DevOps** | Docker, Docker Compose, GitHub Actions, AWS EC2 |
| **Quality** | Ruff, mypy, ESLint, Prettier, pytest, Jest |

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Git](https://git-scm.com/)
- [Make](https://www.gnu.org/software/make/) (pre-installed on macOS/Linux)

### 1. Clone & Configure

```bash
git clone <repository-url>
cd AS2

# Create environment file
cp .env.example .env

# Edit .env and set your OPENAI_API_KEY (required for AI features)
```

### 2. Start

```bash
make dev-build
```

### 3. Verify

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/health |
| API Docs (Swagger) | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |

> For detailed setup instructions, local development without Docker, and production deployment, see the [Operations Manual](docs/05-operations-manual.md).

---

## Project Structure

```
AS2/
├── backend/                # Python FastAPI backend (DDD)
│   ├── shared/             #   Shared kernel (base classes, middleware)
│   ├── identity/           #   Auth & tenant management
│   ├── resume/             #   Resume upload & parsing
│   ├── optimization/       #   AI optimization pipeline (core domain)
│   ├── interview/          #   Interview prep & cover letter
│   ├── billing/            #   Subscription & quotas
│   └── tests/              #   Test suite
├── frontend/               # Next.js React frontend
│   └── src/
│       ├── app/            #   Pages (App Router)
│       ├── components/     #   UI components
│       ├── hooks/          #   Custom React hooks
│       └── providers/      #   Context providers
├── docs/                   # Documentation
├── docker-compose.yml      # Base Docker services
├── docker-compose.dev.yml  # Development overrides
├── docker-compose.prod.yml # Production overrides
└── Makefile                # Command shortcuts
```

---

## Development

### Common Commands

```bash
make dev            # Start all services
make dev-build      # Start with fresh build
make down           # Stop all services
make test           # Run all tests
make lint           # Run linters + type checks
make migrate        # Apply database migrations
make logs           # Tail container logs
make clean          # Full reset (delete volumes + images)
```

### Workflow

This project enforces a **test-first development workflow**:

1. **Understand** — Read relevant docs, identify the bounded context.
2. **Test First** — Write failing tests before implementation.
3. **Implement** — Write the simplest code to pass the tests.
4. **Verify** — Run linters, type checks, and ensure coverage >= 80%.
5. **Commit** — Use [Conventional Commits](https://www.conventionalcommits.org/): `feat(optimization): add ATS scoring agent`.

### Git Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready; protected; PRs only |
| `develop` | Integration branch |
| `feature/<name>` | Feature development |
| `fix/<name>` | Bug fixes |

---

## Team

| Member | Role | Ownership |
|--------|------|-----------|
| **Person A** | AI Workflow | `optimization/`, `interview/` — LangGraph agents, RAG pipeline, ATS scoring, interview Q&A |
| **Person B** | Platform | `shared/`, `identity/`, `resume/`, `billing/`, `frontend/`, Docker, CI/CD |

---

## Documentation

| Document | Description |
|----------|-------------|
| [Requirements Analysis](docs/01-requirements-analysis.md) | User personas, user stories, functional requirements |
| [System Architecture](docs/02-system-architecture.md) | DDD design, data flow diagrams, API design, multi-tenant isolation |
| [Technology Selection](docs/03-technology-selection.md) | Tech stack justification and comparisons |
| [Technical Standards](docs/04-technical-standards.md) | Coding conventions, testing rules, CI/CD gates |
| [Operations Manual](docs/05-operations-manual.md) | Setup, deployment, troubleshooting guide |

---

## License

This project is developed as an academic group assignment. All rights reserved.
