# JobFit AI — System Architecture Design

## 1. Architecture Overview

### 1.1 Architecture Style

JobFit AI adopts a **layered architecture** guided by **Domain-Driven Design (DDD)** principles, with a clear separation of concerns across four layers: API (Interface), Application, Domain, and Infrastructure. The system is designed as a **multi-tenant SaaS** application with row-level tenant isolation.

### 1.2 High-Level Architecture Diagram

```mermaid
graph TB
    subgraph clients [Clients]
        WebApp["Web App (Next.js)"]
    end

    subgraph backend [Backend - FastAPI]
        subgraph apiLayer [API Layer]
            AuthRoutes[Auth Routes]
            ResumeRoutes[Resume Routes]
            OptimizeRoutes[Optimize Routes]
            InterviewRoutes[Interview Routes]
            BillingRoutes[Billing Routes]
        end

        subgraph middleware [Middleware]
            AuthMW[Auth Middleware]
            TenantMW[Tenant Middleware]
            RateLimitMW[Rate Limiter]
        end

        subgraph appLayer [Application Layer]
            AuthAppSvc[Auth App Service]
            ResumeAppSvc[Resume App Service]
            OptimizeAppSvc[Optimization App Service]
            InterviewAppSvc[Interview App Service]
            BillingAppSvc[Billing App Service]
        end

        subgraph domainLayer [Domain Layer]
            IdentityDomain[Identity Domain]
            ResumeDomain[Resume Domain]
            OptimizationDomain[Optimization Domain]
            InterviewDomain[Interview Domain]
            BillingDomain[Billing Domain]
        end

        subgraph infraLayer [Infrastructure Layer]
            Repos[Repository Implementations]
            AIAgents[AI Agents - LangGraph]
            PDFParser[PDF Parser]
            VectorStoreAdapter[Vector Store Adapter]
            FileStorage[File Storage Adapter]
            StripeGateway[Stripe Gateway]
        end
    end

    subgraph dataStores [Data Stores]
        PG["PostgreSQL"]
        Redis["Redis"]
        Chroma["ChromaDB"]
        S3["S3 / MinIO"]
    end

    subgraph external [External Services]
        LLM["LLM API (OpenAI / DeepSeek)"]
        Stripe["Stripe API"]
    end

    WebApp --> AuthMW
    AuthMW --> TenantMW
    TenantMW --> RateLimitMW
    RateLimitMW --> apiLayer

    apiLayer --> appLayer
    appLayer --> domainLayer
    appLayer --> infraLayer

    Repos --> PG
    VectorStoreAdapter --> Chroma
    FileStorage --> S3
    AIAgents --> LLM
    StripeGateway --> Stripe
    RateLimitMW --> Redis
    AuthMW --> Redis
```

---

## 2. Domain-Driven Design

### 2.1 Bounded Contexts

The system is decomposed into **five bounded contexts**, each representing an autonomous domain with its own models, rules, and language.

```mermaid
graph LR
    subgraph identity [Identity Context]
        direction TB
        Tenant[Tenant]
        User[User]
        AuthToken[Auth Token]
    end

    subgraph resume [Resume Context]
        direction TB
        Resume[Resume]
        ResumeSection[Resume Section]
        ParsedContent[Parsed Content]
    end

    subgraph optimization [Optimization Context - Core Domain]
        direction TB
        OptSession[Optimization Session]
        JDAnalysis[JD Analysis]
        ATSScore[ATS Score]
        GapReport[Gap Report]
    end

    subgraph interview [Interview Context]
        direction TB
        InterviewPrep[Interview Prep]
        Question[Question]
        CoverLetter[Cover Letter]
    end

    subgraph billing [Billing Context]
        direction TB
        Subscription[Subscription]
        UsageRecord[Usage Record]
        Quota[Quota]
    end

    identity -->|"authenticates"| resume
    identity -->|"authorizes"| optimization
    identity -->|"owns"| billing
    resume -->|"provides input"| optimization
    optimization -->|"provides context"| interview
    optimization -->|"triggers"| billing
```

### 2.2 Context Mapping

| Relationship | Upstream | Downstream | Pattern |
|-------------|----------|------------|---------|
| User identity for all contexts | Identity | Resume, Optimization, Billing | **Shared Kernel** (User ID, Tenant ID) |
| Resume provides data for optimization | Resume | Optimization | **Customer-Supplier** |
| Optimization results feed interview prep | Optimization | Interview | **Customer-Supplier** |
| Optimization triggers usage tracking | Optimization | Billing | **Published Language** (Domain Events) |

### 2.3 Aggregate Roots, Entities, and Value Objects

#### Identity Context

| Type | Name | Key Attributes | Invariants |
|------|------|---------------|------------|
| **Aggregate Root** | `Tenant` | id, name, plan, status, settings, created_at | Must have at least one admin user; plan must be valid. |
| **Entity** | `User` | id, tenant_id, email, password_hash, role, status | Email unique within tenant; role must be valid enum. |
| **Value Object** | `Email` | value | Must be valid email format; immutable. |
| **Value Object** | `TenantId` | value | UUID; immutable; used as foreign key across contexts. |
| **Value Object** | `Role` | value | Enum: `platform_admin`, `tenant_admin`, `member`. |

#### Resume Context

| Type | Name | Key Attributes | Invariants |
|------|------|---------------|------------|
| **Aggregate Root** | `Resume` | id, user_id, tenant_id, filename, storage_path, parsed_sections, created_at | Belongs to exactly one user; sections cannot exist without resume. |
| **Entity** | `ResumeSection` | id, resume_id, section_type, content, order | section_type must be valid enum; order >= 0. |
| **Value Object** | `ParsedContent` | raw_text, sections_json | Immutable snapshot of parsing result. |
| **Value Object** | `SectionType` | value | Enum: `education`, `experience`, `projects`, `skills`, `certifications`, `summary`. |

#### Optimization Context (Core Domain)

| Type | Name | Key Attributes | Invariants |
|------|------|---------------|------------|
| **Aggregate Root** | `OptimizationSession` | id, resume_id, tenant_id, user_id, jd_text, status, created_at | Must reference a valid resume; status transitions are validated. |
| **Entity** | `OptimizationResult` | id, session_id, optimized_content, ats_score, gap_report | Belongs to exactly one session. |
| **Value Object** | `JDAnalysis` | hard_skills, soft_skills, responsibilities, qualifications | Immutable; produced by JD Analyzer agent. |
| **Value Object** | `ATSScore` | overall, keywords, skills, experience, formatting | All scores 0.0 - 1.0; immutable. |
| **Value Object** | `GapReport` | missing_skills, recommendations | Immutable; list of identified gaps. |
| **Value Object** | `SessionStatus` | value | Enum: `pending`, `processing`, `completed`, `failed`. |

#### Interview Context

| Type | Name | Key Attributes | Invariants |
|------|------|---------------|------------|
| **Aggregate Root** | `InterviewPrep` | id, session_id, tenant_id, questions, created_at | Must reference a completed optimization session. |
| **Value Object** | `InterviewQuestion` | category, question_text, suggested_answer | Category must be valid enum. |
| **Value Object** | `CoverLetter` | content, tone | Tone must be valid enum. |

#### Billing Context

| Type | Name | Key Attributes | Invariants |
|------|------|---------------|------------|
| **Aggregate Root** | `Subscription` | id, tenant_id, plan, status, started_at, expires_at | One active subscription per tenant. |
| **Entity** | `UsageRecord` | id, tenant_id, user_id, action_type, tokens_used, created_at | Must reference valid tenant and user. |
| **Value Object** | `Plan` | name, limits | Enum: `free`, `pro`, `enterprise`; each with defined quotas. |
| **Value Object** | `Quota` | max_optimizations_per_month, max_tokens_per_month | Immutable per plan level. |

### 2.4 Domain Events

| Event | Published By | Consumed By | Payload |
|-------|-------------|-------------|---------|
| `UserRegistered` | Identity | Billing | `{ tenant_id, user_id }` |
| `TenantCreated` | Identity | Billing | `{ tenant_id, plan }` |
| `ResumeUploaded` | Resume | — | `{ tenant_id, user_id, resume_id }` |
| `OptimizationStarted` | Optimization | Billing | `{ tenant_id, user_id, session_id }` |
| `OptimizationCompleted` | Optimization | Billing, Interview | `{ tenant_id, session_id, tokens_used }` |
| `QuotaExceeded` | Billing | Optimization | `{ tenant_id, user_id }` |

---

## 3. Software Design Patterns

### 3.1 Backend Design Patterns

| Pattern | Where Applied | Purpose |
|---------|--------------|---------|
| **Repository Pattern** | All bounded contexts | Abstract data access behind interfaces; domain layer depends on repository interfaces, infrastructure layer provides implementations. Enables testability via mock repositories. |
| **Factory Pattern** | Entity/Aggregate creation | `OptimizationSessionFactory` creates `OptimizationSession` aggregates with proper initialization and validation. `UserFactory` handles user creation with password hashing. Centralizes complex creation logic. |
| **Strategy Pattern** | LLM provider selection | `LLMProviderStrategy` interface with `OpenAIStrategy` and `DeepSeekStrategy` implementations. Provider selected at runtime based on tenant configuration. |
| **Observer Pattern (Domain Events)** | Cross-context communication | When `OptimizationCompleted` event fires, the Billing context records usage asynchronously. Decouples contexts while maintaining consistency. |
| **Unit of Work** | Transaction management | Ensures all database operations within a use case are committed or rolled back together. Wraps SQLAlchemy session lifecycle. |
| **Singleton Pattern** | Configuration, DB connection pool | `Settings` configuration object and `DatabaseEngine` connection pool are initialized once and shared across the application lifecycle. |
| **Dependency Injection** | All layers | FastAPI's `Depends()` mechanism injects services, repositories, and the current user/tenant context. Promotes loose coupling and testability. |
| **Template Method Pattern** | AI Agent base class | `BaseAgent` defines the skeleton algorithm (`prepare -> execute -> parse_output`); concrete agents (`JDAnalyzerAgent`, `RewriterAgent`) override specific steps. |
| **Adapter Pattern** | External service integration | `VectorStoreAdapter` wraps ChromaDB client; `FileStorageAdapter` wraps S3/MinIO client; `PaymentGateway` wraps Stripe. Isolates external dependencies. |

### 3.2 Frontend Design Patterns

| Pattern | Where Applied | Purpose |
|---------|--------------|---------|
| **Container/Presenter Pattern** | React components | Container components handle state and data fetching; Presenter components are pure UI. Example: `OptimizationContainer` (fetches data) + `OptimizationView` (renders UI). |
| **Custom Hook Pattern** | Reusable logic | `useAuth()`, `useResume()`, `useOptimization()` hooks encapsulate API calls, state management, and error handling. Promotes DRY code. |
| **Provider Pattern** | Global state / context | `AuthProvider`, `TenantProvider`, `ThemeProvider` wrap the component tree to provide shared context via React Context API. |
| **Compound Component Pattern** | Complex UI components | `InterviewPrep` component composed of `InterviewPrep.QuestionList`, `InterviewPrep.QuestionItem`, `InterviewPrep.AnswerPanel`. Enables flexible composition. |
| **Factory Pattern** | API client creation | `createApiClient(baseUrl, token)` factory function produces configured Axios/Fetch instances per tenant context. |
| **Strategy Pattern** | Export formats | `ExportStrategy` interface with `PDFExporter` and `DocxExporter` implementations, selected by user choice at runtime. |

### 3.3 Pattern Application Map

```mermaid
graph TB
    subgraph api [API Layer]
        DI["Dependency Injection (FastAPI Depends)"]
    end

    subgraph app [Application Layer]
        UoW["Unit of Work"]
        AppSvc["Application Services"]
    end

    subgraph domain [Domain Layer]
        Factory["Factory (create aggregates)"]
        DomainEvt["Observer (domain events)"]
        Entity["Entities + Value Objects"]
    end

    subgraph infra [Infrastructure Layer]
        Repo["Repository (data access)"]
        Strategy["Strategy (LLM provider)"]
        Adapter["Adapter (external APIs)"]
        Singleton["Singleton (config, DB pool)"]
        Template["Template Method (AI agents)"]
    end

    DI --> AppSvc
    AppSvc --> UoW
    AppSvc --> Factory
    AppSvc --> Entity
    Entity --> DomainEvt
    UoW --> Repo
    Repo --> Singleton
    AppSvc --> Strategy
    AppSvc --> Template
    Strategy --> Adapter
```

---

## 4. Multi-Tenant Architecture

### 4.1 Isolation Strategy: Row-Level Isolation

All database tables include a `tenant_id` column. Data isolation is enforced at **two levels**:

1. **Application Level** — Middleware extracts `tenant_id` from JWT token and injects it into a `ContextVar`. All repository methods automatically filter by this tenant context.
2. **Database Level** — PostgreSQL Row-Level Security (RLS) policies provide a defense-in-depth safeguard.

### 4.2 Tenant Context Flow

```mermaid
sequenceDiagram
    participant Client
    participant AuthMW as Auth Middleware
    participant TenantMW as Tenant Middleware
    participant Route as API Route
    participant AppSvc as App Service
    participant Repo as Repository
    participant DB as PostgreSQL

    Client->>AuthMW: Request with JWT
    AuthMW->>AuthMW: Validate JWT, extract user_id + tenant_id
    AuthMW->>TenantMW: Pass authenticated request
    TenantMW->>TenantMW: Set tenant_id in ContextVar
    TenantMW->>Route: Forward request
    Route->>AppSvc: Call application service
    AppSvc->>Repo: Query data
    Repo->>Repo: Read tenant_id from ContextVar
    Repo->>DB: SELECT ... WHERE tenant_id = ?
    DB-->>Repo: Tenant-scoped results
    Repo-->>AppSvc: Domain entities
    AppSvc-->>Route: Response DTO
    Route-->>Client: JSON response
```

### 4.3 Isolation by Data Store

| Data Store | Isolation Mechanism | Details |
|-----------|---------------------|---------|
| **PostgreSQL** | `tenant_id` column + RLS policies | Every table has `tenant_id NOT NULL`; RLS policy: `USING (tenant_id = current_setting('app.current_tenant'))`. |
| **ChromaDB** | Collection per tenant | Collection name: `tenant_{tenant_id}`; each tenant's vectors are in a separate collection. |
| **S3 / MinIO** | Path-based isolation | Object key prefix: `/{tenant_id}/{user_id}/{filename}`. |
| **Redis** | Key prefix | Key pattern: `tenant:{tenant_id}:*` (e.g., `tenant:abc123:rate_limit:user456`). |

### 4.4 Database Schema Overview

```mermaid
erDiagram
    TENANT ||--o{ USER : has
    TENANT ||--o| SUBSCRIPTION : has
    USER ||--o{ RESUME : owns
    RESUME ||--o{ RESUME_SECTION : contains
    USER ||--o{ OPTIMIZATION_SESSION : creates
    OPTIMIZATION_SESSION ||--o| OPTIMIZATION_RESULT : produces
    OPTIMIZATION_SESSION ||--o| INTERVIEW_PREP : generates
    TENANT ||--o{ USAGE_RECORD : tracks

    TENANT {
        uuid id PK
        string name
        string plan
        string status
        json settings
        timestamp created_at
        timestamp updated_at
    }

    USER {
        uuid id PK
        uuid tenant_id FK
        string email
        string password_hash
        string role
        string status
        timestamp created_at
    }

    SUBSCRIPTION {
        uuid id PK
        uuid tenant_id FK
        string plan
        string status
        string stripe_subscription_id
        timestamp started_at
        timestamp expires_at
    }

    RESUME {
        uuid id PK
        uuid user_id FK
        uuid tenant_id FK
        string filename
        string storage_path
        json parsed_data
        timestamp created_at
    }

    RESUME_SECTION {
        uuid id PK
        uuid resume_id FK
        string section_type
        text content
        int order_index
    }

    OPTIMIZATION_SESSION {
        uuid id PK
        uuid resume_id FK
        uuid user_id FK
        uuid tenant_id FK
        text jd_text
        json jd_analysis
        string status
        timestamp created_at
    }

    OPTIMIZATION_RESULT {
        uuid id PK
        uuid session_id FK
        json optimized_content
        json ats_score
        json gap_report
        int tokens_used
        timestamp created_at
    }

    INTERVIEW_PREP {
        uuid id PK
        uuid session_id FK
        uuid tenant_id FK
        json questions
        text cover_letter
        timestamp created_at
    }

    USAGE_RECORD {
        uuid id PK
        uuid tenant_id FK
        uuid user_id FK
        string action_type
        int tokens_used
        timestamp created_at
    }
```

---

## 5. Backend Project Structure (DDD)

```
backend/
├── main.py                              # FastAPI application entry point
├── config.py                            # Global settings (Singleton pattern)
│
├── shared/                              # Shared Kernel
│   ├── domain/
│   │   ├── base_entity.py               # Base Entity class (id, created_at, updated_at)
│   │   ├── base_value_object.py         # Base Value Object class (immutable, equality by value)
│   │   ├── aggregate_root.py            # Base Aggregate Root class
│   │   ├── domain_event.py              # Domain Event base class + event bus
│   │   └── exceptions.py               # Domain exception hierarchy
│   ├── application/
│   │   └── unit_of_work.py              # Unit of Work interface
│   ├── infrastructure/
│   │   ├── database.py                  # SQLAlchemy engine + session factory (Singleton)
│   │   ├── unit_of_work_impl.py         # SQLAlchemy Unit of Work implementation
│   │   ├── tenant_context.py            # ContextVar-based tenant context
│   │   └── event_bus_impl.py            # In-process event bus implementation
│   └── middleware/
│       ├── auth_middleware.py            # JWT validation + user injection
│       ├── tenant_middleware.py          # Tenant context injection
│       └── rate_limit_middleware.py      # Redis-based rate limiting
│
├── identity/                            # Bounded Context: Identity & Access
│   ├── domain/
│   │   ├── entities.py                  # Tenant (Aggregate Root), User (Entity)
│   │   ├── value_objects.py             # Email, Role, TenantId
│   │   ├── repository.py               # IUserRepository, ITenantRepository (interfaces)
│   │   ├── services.py                  # PasswordHashingService (Domain Service)
│   │   └── factories.py                 # UserFactory, TenantFactory (Factory pattern)
│   ├── application/
│   │   ├── services.py                  # AuthApplicationService, TenantApplicationService
│   │   ├── dto.py                       # RegisterRequest, LoginRequest, TokenResponse
│   │   └── commands.py                  # RegisterUserCommand, CreateTenantCommand
│   ├── infrastructure/
│   │   ├── models.py                    # SQLAlchemy ORM models
│   │   ├── repository_impl.py           # UserRepository, TenantRepository (implementations)
│   │   └── jwt_service.py               # JWT token generation/validation
│   └── api/
│       └── routes.py                    # POST /auth/register, /auth/login, /tenants
│
├── resume/                              # Bounded Context: Resume Management
│   ├── domain/
│   │   ├── entities.py                  # Resume (Aggregate Root), ResumeSection (Entity)
│   │   ├── value_objects.py             # ParsedContent, SectionType
│   │   ├── repository.py               # IResumeRepository (interface)
│   │   ├── services.py                  # ResumeParsingDomainService
│   │   └── factories.py                 # ResumeFactory
│   ├── application/
│   │   ├── services.py                  # ResumeApplicationService
│   │   ├── dto.py                       # UploadResumeResponse, ResumeDetailDTO
│   │   └── commands.py                  # UploadResumeCommand
│   ├── infrastructure/
│   │   ├── models.py                    # SQLAlchemy ORM models
│   │   ├── repository_impl.py           # ResumeRepository implementation
│   │   ├── pdf_parser.py                # PyPDF2 adapter (Adapter pattern)
│   │   ├── vector_store.py              # ChromaDB adapter (Adapter pattern)
│   │   └── file_storage.py              # S3/MinIO adapter (Adapter pattern)
│   └── api/
│       └── routes.py                    # POST /resumes/upload, GET /resumes
│
├── optimization/                        # Bounded Context: Resume Optimization (Core Domain)
│   ├── domain/
│   │   ├── entities.py                  # OptimizationSession (Aggregate Root), OptimizationResult
│   │   ├── value_objects.py             # JDAnalysis, ATSScore, GapReport, SessionStatus
│   │   ├── repository.py               # IOptimizationRepository (interface)
│   │   ├── services.py                  # OptimizationDomainService (scoring validation, status transitions)
│   │   └── factories.py                 # OptimizationSessionFactory
│   ├── application/
│   │   ├── services.py                  # OptimizationApplicationService (orchestrator)
│   │   ├── dto.py                       # OptimizationRequest, OptimizationResponse
│   │   └── commands.py                  # RunOptimizationCommand
│   ├── infrastructure/
│   │   ├── models.py                    # SQLAlchemy ORM models
│   │   ├── repository_impl.py           # OptimizationRepository implementation
│   │   └── agents/                      # LangGraph AI agents (Template Method pattern)
│   │       ├── base_agent.py            # BaseAgent with prepare -> execute -> parse skeleton
│   │       ├── graph.py                 # LangGraph state machine definition
│   │       ├── jd_analyzer.py           # JD Analyzer agent node
│   │       ├── rag_retriever.py         # RAG Retriever agent node
│   │       ├── resume_rewriter.py       # Resume Rewriter agent node
│   │       ├── ats_scorer.py            # ATS Scorer agent node
│   │       └── gap_analyzer.py          # Gap Analyzer agent node
│   └── api/
│       └── routes.py                    # POST /optimize, GET /sessions
│
├── interview/                           # Bounded Context: Interview Preparation
│   ├── domain/
│   │   ├── entities.py                  # InterviewPrep (Aggregate Root)
│   │   ├── value_objects.py             # InterviewQuestion, CoverLetter
│   │   ├── repository.py               # IInterviewPrepRepository (interface)
│   │   └── factories.py                 # InterviewPrepFactory
│   ├── application/
│   │   ├── services.py                  # InterviewApplicationService
│   │   └── dto.py                       # InterviewPrepResponse
│   ├── infrastructure/
│   │   ├── models.py                    # SQLAlchemy ORM models
│   │   ├── repository_impl.py           # InterviewPrepRepository implementation
│   │   └── agents/
│   │       ├── question_generator.py    # Interview question generator agent
│   │       └── cover_letter_generator.py # Cover letter generator agent
│   └── api/
│       └── routes.py                    # POST /interview-prep, POST /cover-letter
│
└── billing/                             # Bounded Context: Billing & Quotas
    ├── domain/
    │   ├── entities.py                  # Subscription (Aggregate Root), UsageRecord (Entity)
    │   ├── value_objects.py             # Plan, Quota
    │   ├── repository.py               # ISubscriptionRepository, IUsageRepository (interfaces)
    │   ├── services.py                  # QuotaEnforcementService (Domain Service)
    │   └── factories.py                 # SubscriptionFactory
    ├── application/
    │   ├── services.py                  # BillingApplicationService
    │   ├── dto.py                       # SubscriptionDTO, UsageSummaryDTO
    │   └── event_handlers.py            # Handle OptimizationCompleted events (Observer)
    ├── infrastructure/
    │   ├── models.py                    # SQLAlchemy ORM models
    │   ├── repository_impl.py           # Subscription/Usage repository implementations
    │   └── stripe_gateway.py            # Stripe API adapter (Adapter pattern)
    └── api/
        └── routes.py                    # GET /billing/usage, POST /billing/subscribe
```

---

## 6. Frontend Project Structure

```
frontend/
├── src/
│   ├── app/                             # Next.js App Router
│   │   ├── (auth)/                      # Auth route group
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (dashboard)/                 # Authenticated route group
│   │   │   ├── layout.tsx               # Dashboard layout with sidebar
│   │   │   ├── resumes/page.tsx         # Resume list page
│   │   │   ├── optimize/page.tsx        # Optimization workspace
│   │   │   ├── history/page.tsx         # Optimization history
│   │   │   └── settings/page.tsx        # User/tenant settings
│   │   ├── layout.tsx                   # Root layout
│   │   └── page.tsx                     # Landing page
│   │
│   ├── components/                      # Reusable UI components
│   │   ├── ui/                          # Base UI primitives (Button, Input, Card, etc.)
│   │   ├── resume/                      # Resume-related components
│   │   │   ├── ResumeUploader.tsx       # Upload widget (Presenter)
│   │   │   └── ResumeViewer.tsx         # Resume content display
│   │   ├── optimization/               # Optimization-related components
│   │   │   ├── JDInputPanel.tsx         # JD text area (Presenter)
│   │   │   ├── OptimizationView.tsx     # Side-by-side diff (Presenter)
│   │   │   ├── ScoreCard.tsx            # ATS score gauge (Presenter)
│   │   │   └── GapReport.tsx            # Gap analysis display (Presenter)
│   │   ├── interview/                   # Interview prep components
│   │   │   └── InterviewPrep.tsx        # Q&A accordion (Compound Component)
│   │   └── layout/                      # Layout components
│   │       ├── Sidebar.tsx
│   │       ├── Header.tsx
│   │       └── ProgressTracker.tsx
│   │
│   ├── containers/                      # Container components (data + logic)
│   │   ├── OptimizationContainer.tsx    # Orchestrates optimization workflow
│   │   ├── ResumeContainer.tsx          # Manages resume upload + parsing
│   │   └── InterviewContainer.tsx       # Manages interview prep flow
│   │
│   ├── hooks/                           # Custom React hooks
│   │   ├── useAuth.ts                   # Auth state and actions
│   │   ├── useResume.ts                 # Resume CRUD operations
│   │   ├── useOptimization.ts           # Optimization workflow
│   │   └── useTenant.ts                 # Tenant context
│   │
│   ├── providers/                       # React Context providers (Provider pattern)
│   │   ├── AuthProvider.tsx             # JWT + user state
│   │   ├── TenantProvider.tsx           # Tenant context
│   │   └── ThemeProvider.tsx            # Theme / dark mode
│   │
│   ├── lib/                             # Utilities and configs
│   │   ├── api/
│   │   │   ├── client.ts               # API client factory (Factory pattern)
│   │   │   ├── endpoints.ts            # API endpoint constants
│   │   │   └── types.ts                # Shared API response types
│   │   ├── utils/
│   │   │   └── format.ts               # Formatting helpers
│   │   └── constants.ts                # App constants
│   │
│   └── types/                           # Global TypeScript type definitions
│       ├── resume.ts
│       ├── optimization.ts
│       ├── interview.ts
│       └── auth.ts
│
├── public/                              # Static assets
├── tailwind.config.ts
├── tsconfig.json
├── next.config.js
└── package.json
```

---

## 7. Data Flow Diagrams

### 7.1 Flow 1: User Registration and Tenant Setup

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API as FastAPI
    participant AuthSvc as AuthAppService
    participant UserFactory as UserFactory
    participant Repo as UserRepository
    participant DB as PostgreSQL

    User->>Frontend: Fill registration form
    Frontend->>API: POST /api/auth/register
    API->>AuthSvc: RegisterUserCommand
    AuthSvc->>UserFactory: create(email, password, tenant_name)
    UserFactory->>UserFactory: Hash password, validate email
    UserFactory-->>AuthSvc: Tenant + User aggregates
    AuthSvc->>Repo: save(tenant, user)
    Repo->>DB: INSERT INTO tenants, users
    DB-->>Repo: Confirm
    AuthSvc-->>API: TokenResponse (JWT)
    API-->>Frontend: { access_token, refresh_token, user }
    Frontend-->>User: Redirect to dashboard
```

### 7.2 Flow 2: Resume Upload and Parse

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API as FastAPI
    participant AppSvc as ResumeAppService
    participant Factory as ResumeFactory
    participant Parser as PDFParser
    participant Storage as FileStorage
    participant VS as VectorStore
    participant DB as PostgreSQL

    User->>Frontend: Upload PDF resume
    Frontend->>API: POST /api/resumes/upload (JWT + file)
    API->>AppSvc: UploadResumeCommand (tenant_id from context)
    AppSvc->>Storage: store(tenant_id, user_id, file)
    Storage-->>AppSvc: storage_path
    AppSvc->>Parser: extract_text(file)
    Parser-->>AppSvc: raw_text
    AppSvc->>Factory: create(user_id, tenant_id, filename, raw_text)
    Factory->>Factory: Parse into sections
    Factory-->>AppSvc: Resume aggregate
    AppSvc->>VS: store_embeddings(tenant_id, sections)
    VS-->>AppSvc: Confirm
    AppSvc->>DB: save(resume)
    DB-->>AppSvc: Confirm
    AppSvc-->>API: ResumeDetailDTO
    API-->>Frontend: Resume JSON
    Frontend-->>User: Display parsed resume
```

### 7.3 Flow 3: Resume Optimization (Core RAG Pipeline)

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API as FastAPI
    participant AppSvc as OptimizationAppService
    participant QuotaSvc as QuotaEnforcementService
    participant Factory as SessionFactory
    participant Graph as LangGraph Pipeline
    participant LLM as LLM API
    participant VS as VectorStore
    participant DB as PostgreSQL
    participant EventBus as Event Bus

    User->>Frontend: Paste JD + Click Optimize
    Frontend->>API: POST /api/optimize (JWT)
    API->>AppSvc: RunOptimizationCommand

    AppSvc->>QuotaSvc: check_quota(tenant_id)
    QuotaSvc-->>AppSvc: Quota OK

    AppSvc->>Factory: create_session(resume_id, jd_text, tenant_id)
    Factory-->>AppSvc: OptimizationSession (status=processing)
    AppSvc->>DB: save(session)

    AppSvc->>Graph: run(jd_text, resume_sections)

    Graph->>LLM: Analyze JD
    LLM-->>Graph: JD Analysis
    Graph->>VS: Retrieve relevant chunks
    VS-->>Graph: Matching sections
    Graph->>LLM: Rewrite bullets
    LLM-->>Graph: Optimized content
    Graph->>LLM: Score ATS
    LLM-->>Graph: ATS Score
    Graph->>LLM: Analyze gaps
    LLM-->>Graph: Gap Report

    Graph-->>AppSvc: OptimizationResult

    AppSvc->>DB: save(result), update session status=completed
    AppSvc->>EventBus: publish(OptimizationCompleted)
    EventBus->>DB: INSERT usage_record

    AppSvc-->>API: OptimizationResponse
    API-->>Frontend: Optimized resume + score + gaps
    Frontend-->>User: Side-by-side comparison
```

### 7.4 Flow 4: Interview Preparation

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API as FastAPI
    participant AppSvc as InterviewAppService
    participant Factory as InterviewPrepFactory
    participant Agent as QuestionGenerator
    participant LLM as LLM API
    participant DB as PostgreSQL

    User->>Frontend: Click "Generate Interview Prep"
    Frontend->>API: POST /api/interview-prep (JWT)
    API->>AppSvc: GenerateInterviewPrepCommand
    AppSvc->>DB: Load optimization session + result
    AppSvc->>Agent: generate(jd_analysis, resume_content)
    Agent->>LLM: Generate categorized Q&A
    LLM-->>Agent: Question list
    Agent-->>AppSvc: Raw Q&A
    AppSvc->>Factory: create(session_id, tenant_id, questions)
    Factory-->>AppSvc: InterviewPrep aggregate
    AppSvc->>DB: save(interview_prep)
    AppSvc-->>API: InterviewPrepResponse
    API-->>Frontend: Q&A JSON
    Frontend-->>User: Display interview questions
```

---

## 8. API Design

### 8.1 API Endpoints

#### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|--------------|
| `POST` | `/api/auth/register` | Register new user + create tenant | No |
| `POST` | `/api/auth/login` | Login and receive JWT tokens | No |
| `POST` | `/api/auth/refresh` | Refresh access token | Refresh token |
| `POST` | `/api/auth/logout` | Invalidate refresh token | Yes |

#### Resume Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|--------------|
| `POST` | `/api/resumes/upload` | Upload and parse a PDF resume | Yes |
| `GET` | `/api/resumes` | List user's resumes | Yes |
| `GET` | `/api/resumes/{id}` | Get resume detail | Yes |
| `DELETE` | `/api/resumes/{id}` | Delete a resume | Yes |

#### Optimization

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|--------------|
| `POST` | `/api/optimize` | Run optimization pipeline | Yes |
| `GET` | `/api/sessions` | List optimization sessions | Yes |
| `GET` | `/api/sessions/{id}` | Get session detail with result | Yes |

#### Interview Preparation

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|--------------|
| `POST` | `/api/interview-prep` | Generate interview Q&A | Yes |
| `POST` | `/api/cover-letter` | Generate cover letter | Yes |

#### Export

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|--------------|
| `GET` | `/api/export/resume/{session_id}` | Download optimized resume PDF | Yes |
| `GET` | `/api/export/interview/{session_id}` | Download interview prep sheet | Yes |

#### Billing

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|--------------|
| `GET` | `/api/billing/usage` | Get usage summary for current tenant | Yes (admin) |
| `GET` | `/api/billing/subscription` | Get current subscription details | Yes (admin) |
| `POST` | `/api/billing/subscribe` | Create/update subscription | Yes (admin) |

#### System

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|--------------|
| `GET` | `/api/health` | Health check | No |

### 8.2 Response Format

All API responses follow a consistent envelope format:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO-8601"
  }
}
```

### 8.3 Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `INVALID_PDF` | 400 | Uploaded file is not a valid PDF. |
| `FILE_TOO_LARGE` | 413 | File exceeds the 10MB limit. |
| `INVALID_CREDENTIALS` | 401 | Email or password is incorrect. |
| `TOKEN_EXPIRED` | 401 | JWT access token has expired. |
| `FORBIDDEN` | 403 | User does not have permission for this action. |
| `NOT_FOUND` | 404 | Requested resource does not exist. |
| `JD_TOO_SHORT` | 400 | Job description text is too short to analyze. |
| `QUOTA_EXCEEDED` | 429 | Tenant has exceeded usage quota for current billing period. |
| `RATE_LIMITED` | 429 | Too many requests from this client. |
| `LLM_TIMEOUT` | 504 | LLM provider did not respond in time. |

---

## 9. Agentic Workflow Design (LangGraph)

The core optimization pipeline is implemented as a **LangGraph state machine**. Each node represents an agent (built using the **Template Method** pattern) that processes part of the task.

### 9.1 State Graph

```mermaid
stateDiagram-v2
    [*] --> JDAnalysis
    JDAnalysis --> ResumeRetrieval
    ResumeRetrieval --> BulletRewriting
    BulletRewriting --> ATSScoring
    ATSScoring --> ScoreCheck
    ScoreCheck --> GapAnalysis: score >= threshold
    ScoreCheck --> BulletRewriting: score < threshold
    GapAnalysis --> ResultAggregation
    ResultAggregation --> [*]
```

### 9.2 State Schema

```python
class OptimizationState(TypedDict):
    """Shared state passed through the LangGraph state machine."""

    # Inputs
    tenant_id: str
    user_id: str
    session_id: str
    jd_text: str
    parsed_resume: dict

    # JD Analysis output
    jd_analysis: dict        # { hard_skills, soft_skills, responsibilities, qualifications }

    # Retrieval output
    relevant_chunks: list     # Retrieved resume sections matching JD requirements

    # Rewriting output
    optimized_bullets: list   # Rewritten bullet points
    rewrite_attempts: int     # Number of rewrite iterations (max 2)

    # Scoring output
    ats_score: float          # 0.0 - 1.0
    score_breakdown: dict     # { keywords, skills, experience, formatting }

    # Gap Analysis output
    gap_report: dict          # { missing_skills, recommendations }

    # Token tracking
    total_tokens_used: int    # Accumulated token usage for billing

    # Final output
    final_result: dict        # Aggregated result for API response
```

### 9.3 Agent Base Class (Template Method Pattern)

```python
class BaseAgent(ABC):
    """Base agent class implementing the Template Method pattern.

    Subclasses override prepare(), execute(), and parse_output() to define
    specific agent behavior while inheriting the common workflow skeleton.
    """

    def run(self, state: OptimizationState) -> dict:
        """Template method: defines the skeleton algorithm."""
        prompt = self.prepare(state)         # Step 1: Build prompt
        raw_output = self.execute(prompt)    # Step 2: Call LLM
        result = self.parse_output(raw_output)  # Step 3: Parse response
        return result

    @abstractmethod
    def prepare(self, state: OptimizationState) -> str:
        """Prepare the prompt from current state. Override in subclass."""
        ...

    @abstractmethod
    def execute(self, prompt: str) -> str:
        """Execute the LLM call. Override to customize provider/model."""
        ...

    @abstractmethod
    def parse_output(self, raw_output: str) -> dict:
        """Parse raw LLM output into structured data. Override in subclass."""
        ...
```

---

## 10. Deployment Architecture

### 10.1 Docker Compose Multi-File Strategy

The project uses a **multi-file Docker Compose** approach to separate shared service definitions from environment-specific configurations. This avoids duplication while maintaining clear differences between development and production.

**File structure:**

```
project-root/
├── docker-compose.yml            # Base services (shared definitions)
├── docker-compose.dev.yml        # Development overrides
├── docker-compose.prod.yml       # Production overrides
├── .env.example                  # Environment variable template
├── backend/
│   ├── Dockerfile                # Multi-stage Dockerfile
│   └── .dockerignore
└── frontend/
    ├── Dockerfile                # Multi-stage Dockerfile
    └── .dockerignore
```

**Usage commands:**

```bash
# Development (local)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production (EC2)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 10.2 Development Environment Architecture

```mermaid
graph LR
    subgraph devMachine [Developer Machine]
        subgraph dockerDev [docker-compose.yml + docker-compose.dev.yml]
            FE_DEV["Frontend :3000 (hot reload)"]
            BE_DEV["Backend :8000 (auto reload)"]
            PG_DEV["PostgreSQL :5432"]
            RD_DEV["Redis :6379"]
            CH_DEV["ChromaDB :8200"]
            MINIO_DEV["MinIO :9000 + Console :9001"]
        end
    end

    subgraph extDev [External Services]
        LLM_DEV["LLM API (OpenAI / DeepSeek)"]
    end

    FE_DEV -->|HTTP| BE_DEV
    BE_DEV --> PG_DEV
    BE_DEV --> RD_DEV
    BE_DEV --> CH_DEV
    BE_DEV --> MINIO_DEV
    BE_DEV -->|HTTPS| LLM_DEV
```

**Development characteristics:**

| Aspect | Configuration |
|--------|--------------|
| **Source code** | Mounted as volumes for hot-reload (`./backend:/app`, `./frontend:/app`) |
| **Frontend** | Next.js dev server with HMR (Hot Module Replacement) |
| **Backend** | Uvicorn with `--reload` flag for auto-restart on file changes |
| **Ports** | All service ports exposed to host for debugging and direct access |
| **Database** | PostgreSQL with simple password; data persisted in named Docker volume |
| **MinIO** | Console UI accessible at port 9001 for visual file browsing |
| **Debug** | Python debugger port exposed (5678); verbose logging enabled |
| **Resource limits** | None (use all available local resources) |
| **Restart policy** | `no` (manual restart for debugging) |
| **HTTPS** | Not required; plain HTTP for local development |

### 10.3 Production Environment Architecture

```mermaid
graph LR
    subgraph client [Client]
        Browser[Web Browser]
    end

    subgraph cloud [AWS EC2]
        subgraph dockerProd [docker-compose.yml + docker-compose.prod.yml]
            FE_PROD["Frontend :3000 (built)"]
            BE_PROD["Backend :8000 (optimized)"]
            PG_PROD["PostgreSQL :5432"]
            RD_PROD["Redis :6379"]
            CH_PROD["ChromaDB :8200"]
            MINIO_PROD["MinIO :9000"]
        end
    end

    subgraph extProd [External Services]
        LLM_PROD["LLM API"]
        StripeProd["Stripe API"]
    end

    Browser -->|HTTPS| FE_PROD
    FE_PROD -->|HTTP internal| BE_PROD
    BE_PROD --> PG_PROD
    BE_PROD --> RD_PROD
    BE_PROD --> CH_PROD
    BE_PROD --> MINIO_PROD
    BE_PROD -->|HTTPS| LLM_PROD
    BE_PROD -->|HTTPS| StripeProd
```

**Production characteristics:**

| Aspect | Configuration |
|--------|--------------|
| **Source code** | Baked into Docker images at build time; no volume mounts |
| **Frontend** | Next.js production build (`next build && next start`); optimized and minified |
| **Backend** | Uvicorn with multiple workers (`--workers 4`); no reload flag |
| **Ports** | Only frontend (3000) exposed to the host; all other services on internal Docker network only |
| **Database** | PostgreSQL with strong password; data on persistent EBS volume |
| **MinIO** | Console port (9001) NOT exposed; access via API only |
| **Debug** | No debug ports; production log level (`WARNING`); structured JSON logging |
| **Resource limits** | CPU and memory limits defined per container |
| **Restart policy** | `unless-stopped` for all services |
| **Health checks** | Configured for all services; Docker auto-restarts unhealthy containers |
| **HTTPS** | Enforced via reverse proxy (Nginx or AWS ALB) |

### 10.4 Container Layout

| Container | Base Image | Dev Port | Prod Port | Description |
|-----------|-----------|----------|-----------|-------------|
| `jobfit-frontend` | `node:20-alpine` | 3000 (host) | 3000 (internal) | Next.js web application |
| `jobfit-backend` | `python:3.11-slim` | 8000 (host) | 8000 (internal) | FastAPI application with AI pipeline |
| `jobfit-postgres` | `postgres:16-alpine` | 5432 (host) | 5432 (internal only) | PostgreSQL relational database |
| `jobfit-redis` | `redis:7-alpine` | 6379 (host) | 6379 (internal only) | Redis cache and rate limiting |
| `jobfit-chromadb` | `chromadb/chroma` | 8200 (host) | 8200 (internal only) | ChromaDB vector database |
| `jobfit-minio` | `minio/minio` | 9000+9001 (host) | 9000 (internal only) | MinIO S3-compatible object storage |

### 10.5 Development vs Production Comparison

| Concern | Development | Production |
|---------|-------------|------------|
| **`APP_ENV`** | `development` | `production` |
| **Source mounting** | Yes (`volumes: ./src:/app`) | No (code baked in image) |
| **Hot reload** | Yes (uvicorn `--reload`, Next.js HMR) | No |
| **Debug ports** | Exposed (5678 for Python debugger) | Not exposed |
| **DB port exposed** | Yes (5432 on host for DB tools) | No (internal network only) |
| **MinIO Console** | Yes (port 9001) | No |
| **Log level** | `DEBUG` | `WARNING` |
| **Log format** | Human-readable text | Structured JSON |
| **Workers** | 1 (for debugger compatibility) | 4 (or `2 * CPU + 1`) |
| **Resource limits** | None | CPU + memory per container |
| **Restart policy** | `no` | `unless-stopped` |
| **Health checks** | Optional | Required for all services |
| **Secrets source** | `.env` file (local) | `.env` file (server, `chmod 600`) |
| **HTTPS** | No (HTTP only) | Yes (via reverse proxy) |
| **`docker compose` command** | `-f docker-compose.yml -f docker-compose.dev.yml up` | `-f docker-compose.yml -f docker-compose.prod.yml up -d` |

### 10.6 Multi-Stage Dockerfile Strategy

Both frontend and backend use **multi-stage Dockerfiles** to keep production images small while supporting development workflows.

**Backend Dockerfile stages:**

| Stage | Purpose | Used In |
|-------|---------|---------|
| `base` | Install system dependencies and Python base | Both |
| `dev` | Install dev dependencies (pytest, ruff, mypy); expose debug port | Development |
| `prod` | Install only production dependencies; copy built source; run with gunicorn/uvicorn workers | Production |

**Frontend Dockerfile stages:**

| Stage | Purpose | Used In |
|-------|---------|---------|
| `base` | Install Node.js dependencies | Both |
| `dev` | Run `next dev` with HMR | Development |
| `builder` | Run `next build` to produce optimized output | Production build |
| `prod` | Copy build output from `builder`; run `next start` with minimal image | Production |

### 10.7 Environment Variables

| Variable | Service | Dev Default | Prod Value |
|----------|---------|-------------|------------|
| `APP_ENV` | Both | `development` | `production` |
| `DATABASE_URL` | Backend | `postgresql+asyncpg://postgres:postgres@postgres:5432/jobfit_dev` | `postgresql+asyncpg://<user>:<pass>@postgres:5432/jobfit_prod` |
| `REDIS_URL` | Backend | `redis://redis:6379/0` | `redis://redis:6379/0` |
| `JWT_SECRET_KEY` | Backend | `dev-secret-key-not-for-production` | (strong random 64-char string) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | `60` (longer for dev convenience) | `15` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Backend | `30` | `7` |
| `OPENAI_API_KEY` | Backend | (personal dev key) | (production key) |
| `DEEPSEEK_API_KEY` | Backend | (personal dev key) | (production key) |
| `LLM_PROVIDER` | Backend | `openai` | `openai` |
| `CHROMA_HOST` | Backend | `chromadb` | `chromadb` |
| `CHROMA_PORT` | Backend | `8200` | `8200` |
| `S3_ENDPOINT` | Backend | `http://minio:9000` | `http://minio:9000` (or AWS S3 URL) |
| `S3_ACCESS_KEY` | Backend | `minioadmin` | (strong access key) |
| `S3_SECRET_KEY` | Backend | `minioadmin` | (strong secret key) |
| `S3_BUCKET_NAME` | Backend | `jobfit-uploads-dev` | `jobfit-uploads` |
| `STRIPE_SECRET_KEY` | Backend | `sk_test_xxx` (test mode) | `sk_live_xxx` (live mode) |
| `STRIPE_WEBHOOK_SECRET` | Backend | `whsec_test_xxx` | `whsec_live_xxx` |
| `NEXT_PUBLIC_API_URL` | Frontend | `http://localhost:8000` | `https://api.jobfit.ai` |
| `LOG_LEVEL` | Backend | `DEBUG` | `WARNING` |
| `UVICORN_WORKERS` | Backend | `1` | `4` |
| `MAX_UPLOAD_SIZE_MB` | Backend | `10` | `10` |

### 10.8 Docker Network and Volume Strategy

**Networks:**

| Network | Purpose | Environment |
|---------|---------|-------------|
| `jobfit-network` | Internal communication between all containers | Both |

**Volumes:**

| Volume | Purpose | Dev | Prod |
|--------|---------|-----|------|
| `postgres-data` | PostgreSQL data persistence | Named volume | Named volume (backed by EBS) |
| `redis-data` | Redis data persistence (AOF) | Named volume | Named volume |
| `chroma-data` | ChromaDB vector data persistence | Named volume | Named volume |
| `minio-data` | MinIO object storage persistence | Named volume | Named volume (backed by EBS) |
| Source code mounts | Hot reload for development | Bind mounts (`./backend:/app`) | Not used |

### 10.9 CI/CD Pipeline

```mermaid
graph LR
    subgraph prPhase [On Pull Request]
        Lint[Lint + Type Check]
        Test[Unit + Integration Tests]
        Coverage[Coverage >= 80%]
        SecretScan[Secret Scan]
    end

    subgraph mergePhase [On Merge to main]
        BuildDev[Build Dev Images]
        TestE2E[E2E Smoke Tests]
        BuildProd[Build Prod Images]
        Deploy[Deploy to EC2]
    end

    Lint --> Test
    Test --> Coverage
    Coverage --> SecretScan

    SecretScan -.->|approved| BuildDev
    BuildDev --> TestE2E
    TestE2E --> BuildProd
    BuildProd --> Deploy
```

**Deployment steps:**

1. CI builds production Docker images (`docker compose -f docker-compose.yml -f docker-compose.prod.yml build`).
2. Images are pushed to a container registry (GitHub Container Registry or AWS ECR).
3. CI SSHs into EC2, pulls latest images, and runs `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`.
4. Health check endpoints are polled to verify successful deployment.
5. On failure, automatic rollback to previous image tag.
