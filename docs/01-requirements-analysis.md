# JobFit AI — Requirements Analysis

## 1. Project Overview

### 1.1 Project Name

**JobFit AI: An Intelligent Resume Optimization Agent**

### 1.2 Product Vision

JobFit AI is a **SaaS (Software as a Service)** platform that provides AI-powered resume optimization for job seekers. The system is designed as a **multi-tenant** application from the ground up, enabling organizations (recruitment agencies, career centers, universities) and individual users to use the platform under isolated data environments.

### 1.3 Problem Statement

In the competitive job market, candidates face two critical challenges:

1. **ATS (Applicant Tracking System) barriers** — Most large companies use ATS software to automatically filter resumes before a human ever reads them. Resumes that lack the right keywords or formatting are rejected outright, regardless of the candidate's actual qualifications.
2. **Time-consuming manual tailoring** — Customizing a resume for each job description is tedious and error-prone. Candidates often struggle to identify which of their experiences are most relevant and how to phrase them to match the JD's language.

These problems disproportionately affect fresh graduates, career switchers, and international job seekers who may lack expertise in resume optimization.

### 1.4 Project Summary

JobFit AI is a web-based SaaS application that leverages Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) to automate resume customization. Users upload their existing resume (PDF) and paste a target job description. The system then:

- Parses and analyzes the JD for key technical and soft skills.
- Retrieves the most relevant experiences from the user's resume via vector similarity search.
- Rewrites bullet points to align with the JD's keywords and tone, maximizing ATS compatibility.
- Provides a gap analysis report highlighting missing skills.
- Generates potential interview questions and suggested answers based on the JD and the user's background.

Unlike generic rewriting tools, JobFit AI focuses on **context-aware optimization**, helping users present their most relevant qualifications effectively.

---

## 2. Target Users

### 2.1 End-User Personas

| Persona | Description | Key Pain Points |
|---------|-------------|-----------------|
| **Fresh Graduates / Interns** | Students or recent graduates with limited work experience entering the job market for the first time. | Lack resume optimization experience; unfamiliar with ATS rules; unsure how to match limited experience to JD requirements. |
| **Career Switchers** | Professionals transitioning to a new industry or role who need to repackage existing experience. | Difficulty mapping past experience to new-domain JD keywords; need to highlight transferable skills effectively. |
| **International Job Seekers** | Candidates applying for jobs in English-speaking markets where English may not be their first language. | Language polishing needs; unfamiliarity with Western resume conventions and ATS keyword expectations. |
| **High-Frequency Applicants** | Active job seekers applying to many positions simultaneously who need efficiency. | Manually customizing a resume for each application is extremely time-consuming; risk of generic, untailored submissions. |

### 2.2 Tenant-Level Personas (SaaS)

| Persona | Description | Key Needs |
|---------|-------------|-----------|
| **Individual User** | A single job seeker using the platform directly. | Self-service signup; free or personal subscription plan; manage own resumes and history. |
| **Career Center / University** | An educational institution offering the tool to students and alumni. | Manage multiple user accounts under one organization; usage analytics dashboard; bulk subscription. |
| **Recruitment Agency** | A staffing firm helping candidates optimize resumes for client roles. | Multi-user access; shared resource pools; usage quotas per consultant. |
| **Platform Administrator** | Internal team managing the SaaS platform. | Tenant provisioning; system health monitoring; global configuration; billing management. |

### 2.3 Core User Needs

- Quickly generate a JD-tailored resume from an existing base resume.
- Understand what the target JD values most (skills, keywords, qualifications).
- Receive actionable feedback on skill gaps.
- Prepare for interviews with JD-specific questions and answer suggestions.
- Maintain a persistent history of all optimization sessions for future reference.

---

## 3. User Stories

### 3.1 Core Resume Optimization Features (P0 — Must Have for MVP)

| ID | User Story | Acceptance Criteria |
|----|-----------|---------------------|
| US-01 | As a job seeker, I want to **upload my resume as a PDF** so that the system can parse my existing experience and skills. | System accepts PDF files up to 10MB; extracted text is displayed for user confirmation. |
| US-02 | As a job seeker, I want to **paste a target job description** so that the system understands the role's requirements. | Free-text input field accepts JD text; system confirms successful parsing. |
| US-03 | As a job seeker, I want the AI to **automatically analyze the JD for key skills and requirements** so that I understand what the role prioritizes. | System extracts and displays categorized lists of hard skills, soft skills, and qualifications from the JD. |
| US-04 | As a job seeker, I want the AI to **rewrite my resume bullet points** to align with the JD's keywords and tone, improving ATS compatibility. | Each rewritten bullet point incorporates relevant JD keywords; action verbs and quantified achievements are used. |
| US-05 | As a job seeker, I want to **compare the original and optimized resume side by side** so that I can clearly see what changed. | UI displays a two-column diff view with modifications highlighted. |
| US-06 | As a job seeker, I want a **gap analysis report** that tells me which JD-required skills are missing from my resume. | Report lists missing skills categorized by importance; suggests ways to address gaps. |
| US-07 | As a job seeker, I want the AI to **generate potential interview questions and answer suggestions** based on the JD and my resume. | System generates at least 8-10 questions covering behavioral, technical, and situational categories, each with a tailored answer suggestion using the STAR format where applicable. |

### 3.2 Authentication and Tenant Management (P0 — Must Have for MVP)

| ID | User Story | Acceptance Criteria |
|----|-----------|---------------------|
| US-14 | As a new user, I want to **register an account with email and password** so that I can access the platform. | Registration form validates email uniqueness; password meets strength requirements; confirmation email sent. |
| US-15 | As a registered user, I want to **log in and log out securely** so that my data is protected. | JWT-based authentication; tokens expire after configurable timeout; refresh token mechanism available. |
| US-16 | As a platform admin, I want to **create and manage tenants** so that organizations can be onboarded. | Admin can create tenants, assign plans, activate/deactivate tenants. |
| US-17 | As a tenant admin, I want to **invite and manage users within my organization** so that my team can use the platform. | Invite via email; assign roles (admin, member); revoke access. |
| US-18 | As a user, I want to be **confident that my data is isolated from other tenants** so that my information stays private. | All queries are scoped by tenant_id; no cross-tenant data leakage; verified by integration tests. |

### 3.3 Important Features (P1 — Should Have)

| ID | User Story | Acceptance Criteria |
|----|-----------|---------------------|
| US-08 | As a job seeker, I want to **download the optimized resume as a PDF** so that I can submit it directly to employers. | One-click download produces a clean, ATS-friendly PDF. |
| US-09 | As a job seeker, I want to see an **ATS match score** so that I can gauge how well my resume fits the JD. | Score displayed as a percentage (0-100%) with a breakdown by category (keywords, skills, experience relevance). |
| US-11 | As a job seeker, I want the AI to **generate a customized Cover Letter** based on the JD and my optimized resume. | Cover letter is professional, addresses key JD requirements, and can be downloaded. |
| US-12 | As a job seeker, I want the system to **save my optimization history** so that I can reuse and review past results. | User can view a list of past optimization sessions with dates and JD titles; data persists across sessions. |
| US-19 | As a tenant admin, I want to **view usage analytics** for my organization so that I can track consumption and ROI. | Dashboard shows optimization count, token usage, and active users per time period. |

### 3.4 Subscription and Billing (P1 — Should Have)

| ID | User Story | Acceptance Criteria |
|----|-----------|---------------------|
| US-20 | As a user, I want to **choose a subscription plan** (Free / Pro / Enterprise) so that I can access features appropriate to my needs. | Plan comparison page; upgrade/downgrade flow; feature gating based on plan. |
| US-21 | As a user, I want to be **notified when I approach my usage quota** so that I can manage my consumption. | Warning at 80% usage; hard block at 100% with upgrade prompt. |
| US-22 | As a tenant admin, I want to **manage billing and payment methods** so that my organization's subscription stays active. | Stripe integration; invoice history; payment method management. |

### 3.5 Nice-to-Have Features (P2 — Could Have)

| ID | User Story | Acceptance Criteria |
|----|-----------|---------------------|
| US-10 | As a job seeker, I want to **accept or reject each AI modification individually** so that I retain full control over the final content. | Each bullet-point change has accept/reject/edit controls; final resume reflects user choices. |
| US-13 | As a job seeker, I want to **choose different optimization styles** (e.g., conservative vs. aggressive) to match my preferences. | At least two style presets are available; output tone and degree of rewriting differ accordingly. |
| US-23 | As a platform admin, I want to **configure LLM provider and model settings per tenant** so that costs and quality can be tuned. | Admin panel allows selecting LLM provider and model per tenant. |

---

## 4. Functional Requirements

### 4.1 Module 1: Identity and Access Management

| Req ID | Requirement | Details |
|--------|-------------|---------|
| FR-22 | User Registration | Email + password registration with email verification. |
| FR-23 | User Authentication | JWT-based login/logout; access token + refresh token; configurable expiry. |
| FR-24 | Role-Based Access Control | Roles: `platform_admin`, `tenant_admin`, `member`. Permission matrix per role. |
| FR-25 | Tenant Provisioning | Create tenant with name, plan, and initial admin user. |
| FR-26 | User Management | Tenant admins can invite users, assign roles, and deactivate accounts within their tenant. |

### 4.2 Module 2: Resume Parsing Engine

| Req ID | Requirement | Details |
|--------|-------------|---------|
| FR-01 | PDF Upload | Accept PDF resume uploads (max 10MB); store in tenant-scoped object storage. |
| FR-02 | Text Extraction | Extract raw text from uploaded PDF using PyPDF2 or equivalent. |
| FR-03 | Structured Parsing | Identify and segment resume into sections: Education, Work Experience, Projects, Skills, Certifications, Summary. |
| FR-04 | Vectorization | Convert parsed resume sections into vector embeddings and store in a tenant-isolated vector collection. |

### 4.3 Module 3: JD Analysis Engine

| Req ID | Requirement | Details |
|--------|-------------|---------|
| FR-05 | JD Text Input | Accept plain-text JD input via a text area. |
| FR-06 | Entity Extraction | Extract hard skills, soft skills, responsibilities, qualifications, and preferred attributes from JD text using LLM. |
| FR-07 | Keyword Weighting | Assign importance weights to extracted keywords based on frequency and position in the JD. |
| FR-08 | Structured Summary | Output a structured JD requirements summary for downstream modules. |

### 4.4 Module 4: Resume Optimizer (Core)

| Req ID | Requirement | Details |
|--------|-------------|---------|
| FR-09 | RAG Retrieval | Use vector similarity search to find the most relevant resume sections for each JD requirement. |
| FR-10 | Bullet Point Rewriting | Use LLM to rewrite experience bullet points, embedding JD keywords, quantifying achievements, and optimizing action verbs. |
| FR-11 | ATS Optimization | Ensure output formatting and keyword density meet ATS best practices. |
| FR-12 | ATS Match Scoring | Calculate and display an ATS compatibility score (before vs. after optimization). |
| FR-13 | Gap Analysis | Generate a report listing JD-required skills/experiences not found in the resume, with recommendations. |

### 4.5 Module 5: Interview Preparation Assistant

| Req ID | Requirement | Details |
|--------|-------------|---------|
| FR-14 | Question Generation | Generate behavioral, technical, and situational interview questions based on JD requirements. |
| FR-15 | Answer Suggestions | Provide personalized answer suggestions based on the user's actual resume content, using the STAR format for behavioral questions. |
| FR-16 | Question Categorization | Categorize questions by type (behavioral, technical, project deep-dive, situational). |

### 4.6 Module 6: Cover Letter Generator

| Req ID | Requirement | Details |
|--------|-------------|---------|
| FR-17 | Auto-Generation | Generate a tailored cover letter based on the JD analysis and optimized resume content. |
| FR-18 | Tone Selection | Support different tone options (formal, conversational, enthusiastic). |

### 4.7 Module 7: Result Display and Export

| Req ID | Requirement | Details |
|--------|-------------|---------|
| FR-19 | Side-by-Side Comparison | Display original and optimized resume in a two-column diff view with highlighted changes. |
| FR-20 | PDF Export | Generate and download the optimized resume as a clean PDF. |
| FR-21 | Interview Prep Export | Export interview questions and answer suggestions as a downloadable document. |

### 4.8 Module 8: Subscription and Billing

| Req ID | Requirement | Details |
|--------|-------------|---------|
| FR-27 | Plan Management | Define subscription plans (Free / Pro / Enterprise) with feature and quota limits. |
| FR-28 | Usage Tracking | Track per-tenant and per-user API calls, LLM token consumption, and optimization count. |
| FR-29 | Quota Enforcement | Enforce usage limits based on subscription plan; return `429 QUOTA_EXCEEDED` when limits are reached. |
| FR-30 | Payment Integration | Integrate with Stripe for subscription billing and invoice generation. |

### 4.9 Module 9: Multi-Tenant Data Management

| Req ID | Requirement | Details |
|--------|-------------|---------|
| FR-31 | Tenant Data Isolation | All database queries must be scoped by `tenant_id`; enforced at the repository layer. |
| FR-32 | Vector Store Isolation | Each tenant has an isolated ChromaDB collection (`tenant_{id}`); metadata filtering as secondary safeguard. |
| FR-33 | File Storage Isolation | Uploaded files stored under tenant-scoped paths (`/{tenant_id}/{user_id}/`). |
| FR-34 | Tenant Configuration | Per-tenant settings: LLM provider preference, model selection, usage quotas. |

---

## 5. Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| **Performance** | Resume optimization pipeline should complete within a reasonable time. | < 60 seconds for full optimization cycle. |
| **Performance** | Frontend should feel responsive during processing. | Real-time progress indicators; streaming LLM responses where possible. |
| **Scalability** | System should handle concurrent users across multiple tenants. | Support at least 50 concurrent optimization sessions in production. |
| **Security** | User authentication must be secure. | JWT with short-lived access tokens (15min) + refresh tokens (7d); bcrypt password hashing. |
| **Security** | User-uploaded resumes contain sensitive personal data. | Encrypted at rest (AES-256); encrypted in transit (TLS 1.3); tenant-isolated storage. |
| **Security** | API endpoints must be protected. | Rate limiting per tenant; input validation and sanitization; CORS whitelist. |
| **Security** | Multi-tenant isolation must be verifiable. | Automated integration tests verify no cross-tenant data access is possible. |
| **Usability** | Interface should be intuitive for non-technical users. | Clean, modern UI; clear step-by-step workflow; mobile-responsive design. |
| **Reliability** | Graceful error handling. | Meaningful error messages for upload failures, LLM timeouts, or parsing errors. |
| **Maintainability** | Codebase follows DDD principles. | Clear bounded contexts; layered architecture (Domain, Application, Infrastructure, API). |
| **Maintainability** | Test coverage gate. | Minimum 80% unit test coverage for domain and application layers. |

---

## 6. Acceptance Criteria for MVP

The Minimum Viable Product (MVP) will be considered complete when:

1. **User Authentication**: Users can register, log in, and manage their sessions securely.
2. **Tenant Isolation**: Data is provably isolated between tenants (verified by tests).
3. **Resume Upload**: Users can successfully upload a PDF resume and see the extracted content.
4. **JD Input**: Users can paste a job description and see the extracted key requirements.
5. **Resume Optimization**: The system produces a rewritten resume with JD-aligned keywords and improved ATS compatibility.
6. **Side-by-Side Comparison**: Users can visually compare the original and optimized versions.
7. **Gap Analysis**: A clear report highlights missing skills and improvement suggestions.
8. **Interview Preparation**: At least 8 relevant interview questions with answer suggestions are generated.
9. **PDF Download**: Users can download the optimized resume as a PDF.
10. **History Persistence**: Optimization results are saved and retrievable across user sessions.
11. **Deployment**: The application is deployed and accessible via a public URL.

---

## 7. Scope and Constraints

### 7.1 In Scope (MVP)

- User registration and JWT-based authentication.
- Basic multi-tenant data isolation (row-level with `tenant_id`).
- Single resume upload (PDF only) per optimization session.
- English-language JD and resume processing.
- Core optimization pipeline (parse -> analyze -> rewrite -> score -> export).
- Interview question generation.
- Optimization history persistence.
- Web-based UI with responsive design.
- Default tenant with free-tier plan (billing integration as stub).

### 7.2 Out of Scope (Future Iterations)

- Full Stripe payment integration (stubbed in MVP).
- Multi-language support (Chinese, etc.).
- Resume template design/formatting.
- Batch processing of multiple JDs.
- Integration with job boards (LinkedIn, Indeed, etc.).
- Mobile native application.
- SSO (SAML/OIDC) enterprise authentication.
- Admin dashboard UI (admin operations via API only in MVP).

### 7.3 Phased Delivery

| Phase | Scope | Timeline |
|-------|-------|----------|
| **Phase 1 (MVP)** | Auth + tenant isolation + core optimization pipeline + history persistence + deployment. Billing is stubbed (hardcoded free plan). | Development sprint |
| **Phase 2 (SaaS Launch)** | Stripe billing integration; admin dashboard UI; usage analytics; tenant self-service onboarding. | Post-MVP iteration |
| **Phase 3 (Growth)** | SSO; multi-language; job board integrations; advanced analytics; mobile app. | Future roadmap |
