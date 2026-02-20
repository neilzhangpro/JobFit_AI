# JobFit AI — Git Workflow Guide

This document defines the team's Git workflow, branch management, commit conventions, Pull Request process, and conflict resolution strategies. All team members must follow these practices to maintain a clean, traceable, and collaborative codebase.

---

## 1. Branch Strategy

### 1.1 Branch Overview

Trunk-based development: `main` is the only long-lived branch. All feature and fix branches branch from and merge into `main`.

```
main ─────────────────────────────────────────────── (trunk; production-ready)
  │         │         │
  ├── feature/resume-upload     (Person B)
  ├── feature/jd-analyzer       (Person A)
  └── fix/pdf-parsing-error     (Person B)
```

### 1.2 Branch Definitions

| Branch | Purpose | Branch From | Merge Into | Protection |
|--------|---------|-------------|-----------|------------|
| `main` | Trunk. Production-ready code. Always deployable. | — | — | Protected: requires PR + passing CI + 1 approval |
| `feature/<name>` | New feature development | `main` | `main` (via PR) | No protection |
| `fix/<name>` | Bug fixes (non-urgent) | `main` | `main` (via PR) | No protection |
| `hotfix/<name>` | Production emergency fix | `main` | `main` (via PR) | No protection |

### 1.3 Branch Naming Convention

```
<type>/<bounded-context>-<short-description>
```

**Examples:**

| Branch Name | Who | Description |
|-------------|-----|-------------|
| `feature/optimization-jd-analyzer` | Person A | JD analysis agent implementation |
| `feature/optimization-rag-pipeline` | Person A | RAG retrieval pipeline |
| `feature/identity-jwt-auth` | Person B | JWT authentication flow |
| `feature/resume-pdf-parser` | Person B | PDF upload and parsing |
| `feature/frontend-landing-page` | Person B | Landing page UI |
| `fix/resume-multicolumn-parsing` | Person B | Fix multi-column PDF parsing bug |
| `hotfix/auth-token-expiry` | Person B | Fix JWT expiry bug in production |

**Rules:**
- Use lowercase and hyphens only (no underscores, no spaces).
- Start with the type prefix (`feature/`, `fix/`, `hotfix/`).
- Include the bounded context name when applicable.
- Keep it short but descriptive (max ~50 characters).

---

## 2. Daily Git Workflow

### 2.1 Starting a New Feature

```bash
# 1. Ensure main is up to date
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/optimization-jd-analyzer

# 3. Work on your feature (follow test-first workflow)
# ... write tests, implement, verify ...
```

### 2.2 Making Commits

```bash
# Stage changes
git add .

# Commit with Conventional Commits format
git commit -m "feat(optimization): add JD analyzer agent

Implements the JDAnalyzerAgent that extracts structured requirements
(hard skills, soft skills, responsibilities) from raw JD text using LLM.

Closes #12"
```

### 2.3 Keeping Your Branch Up to Date

Sync with `main` regularly (at least daily) to avoid large merge conflicts:

```bash
# Option A: Rebase (preferred for clean history)
git fetch origin
git rebase origin/main

# Option B: Merge (simpler, but creates merge commits)
git fetch origin
git merge origin/main
```

**When to use which:**
- **Rebase**: When your branch has not been pushed yet, or you're the only one working on it.
- **Merge**: When the branch has been shared/pushed and others might have pulled it.

### 2.4 Pushing Your Branch

```bash
# First push (set upstream)
git push -u origin feature/optimization-jd-analyzer

# Subsequent pushes
git push

# After rebase (force push your own branch only)
git push --force-with-lease
```

> **NEVER** use `git push --force` on `main`. Use `--force-with-lease` on feature branches only after rebase.

### 2.5 Creating a Pull Request

When your feature is ready:

```bash
# 1. Ensure all tests pass locally
make test
make lint

# 2. Push latest changes
git push

# 3. Create PR on GitHub (main <- feature/xxx)
# Use the PR template below
```

---

## 3. Commit Message Convention

All commit messages **MUST** follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### 3.1 Format

```
<type>(<scope>): <short description>

[optional body — explain WHAT and WHY, not HOW]

[optional footer — issue references, breaking changes]
```

### 3.2 Type Reference

| Type | When to Use | Example |
|------|-------------|---------|
| `feat` | Adding a new feature | `feat(optimization): add ATS scoring agent` |
| `fix` | Fixing a bug | `fix(resume): handle empty PDF upload gracefully` |
| `test` | Adding or updating tests only | `test(identity): add tenant isolation tests for UserRepository` |
| `refactor` | Changing code without fixing bugs or adding features | `refactor(shared): extract base repository with tenant filtering` |
| `docs` | Documentation changes only | `docs: add interview prep API endpoint documentation` |
| `chore` | Build, tooling, dependencies | `chore: upgrade LangChain to 0.2.5` |
| `ci` | CI/CD pipeline changes | `ci: add coverage gate to backend test job` |
| `style` | Formatting only (no logic change) | `style(backend): apply ruff formatting to billing context` |

### 3.3 Scope Reference

Scope **must** match one of the bounded contexts or cross-cutting concerns:

| Scope | Owned By | What It Covers |
|-------|----------|----------------|
| `identity` | Person B | Auth, users, tenants, JWT |
| `resume` | Person B | PDF upload, parsing, vector store |
| `optimization` | Person A | JD analysis, RAG, rewriting, ATS scoring, gap analysis |
| `interview` | Person A | Question generation, cover letter |
| `billing` | Person B | Subscriptions, quotas, usage tracking |
| `shared` | Both | Base classes, middleware, config |
| `frontend` | Person B | All frontend code |

### 3.4 Good vs Bad Commit Messages

```bash
# BAD — vague, no type, no scope
git commit -m "fix stuff"
git commit -m "update code"
git commit -m "WIP"

# BAD — describes WHAT (obvious from diff), not WHY
git commit -m "feat(optimization): add function calculate_ats_score"

# GOOD — clear type, scope, explains purpose
git commit -m "feat(optimization): add ATS scoring agent

Evaluates keyword match, skill coverage, and formatting compliance
to produce a weighted ATS compatibility score (0-100%).

Uses GPT-4o-mini for cost efficiency on this classification task.

Closes #15"

# GOOD — concise for small changes
git commit -m "fix(resume): handle PDFs with no text layer"
git commit -m "test(billing): add quota enforcement edge cases"
git commit -m "chore: pin Docker base image to python:3.11.9-slim"
```

### 3.5 Commit Frequency

| Principle | Description |
|-----------|-------------|
| **Atomic commits** | Each commit should represent one logical change. Don't mix feature code and formatting in one commit. |
| **Commit often** | Small, frequent commits are easier to review and revert. |
| **Never commit broken code** | Every commit on `main` should pass tests. Feature branches may have WIP commits, but squash before merging. |

---

## 4. Pull Request Process

### 4.1 PR Title

Must follow Conventional Commits format (same as commit message first line):

```
feat(optimization): implement JD analyzer agent with structured output
fix(resume): handle multi-column PDF layouts
test(identity): add comprehensive tenant isolation test suite
```

### 4.2 PR Description Template

Every PR description must include the following sections:

```markdown
## Summary
<!-- What does this PR do? 1-3 bullet points. -->
- Implements the JDAnalyzerAgent that extracts structured requirements from JD text
- Adds unit tests with 95% coverage for the domain layer
- Adds integration test for the /api/optimize endpoint

## Motivation
<!-- Why is this change needed? Link to issue if applicable. -->
Closes #12. This is the first agent in the optimization pipeline, required before
the RAG retriever and rewriter can be implemented.

## Changes
<!-- List the key files changed and why. -->
- `optimization/infrastructure/agents/jd_analyzer.py` — New agent implementation
- `optimization/domain/value_objects.py` — Added JDAnalysis value object
- `tests/test_optimization.py` — Added 8 test cases

## Testing
<!-- How was this tested? What should the reviewer verify? -->
- [x] Unit tests pass: `pytest tests/test_optimization.py -v`
- [x] Tenant isolation test included
- [x] Coverage >= 80%
- [ ] Manual test: paste a real JD and verify extracted skills

## Screenshots (if UI changes)
<!-- Attach screenshots for frontend changes. -->
N/A
```

### 4.3 PR Rules

| Rule | Requirement |
|------|-------------|
| **Target branch** | Feature PRs target `main`. |
| **Size limit** | < 400 lines of changed code. Split larger changes. |
| **Tests required** | Every PR adding/changing functionality must include tests. |
| **CI must pass** | All 6 CI jobs (lint, type check, unit test, integration test, coverage, secret scan) must pass. |
| **AI review** | Wait for the AI review bot comment. Address any critical issues. |
| **Human review** | At least 1 approval from the designated code owner (see CODEOWNERS). |
| **No merge conflicts** | Resolve all conflicts before requesting review. |
| **Squash merge** | Use "Squash and merge" for feature branches to keep history clean. |

### 4.4 PR Review Checklist (for Reviewers)

When reviewing a PR, check the following:

```markdown
- [ ] PR title follows Conventional Commits format
- [ ] PR description includes Summary, Motivation, Changes, Testing
- [ ] Code follows DDD layer rules (no framework imports in domain layer)
- [ ] All repository queries include tenant_id filtering
- [ ] Tests are included and pass
- [ ] No hardcoded secrets, magic numbers, or `any` types
- [ ] Docstrings on all public classes and functions
- [ ] No commented-out code
- [ ] Changes are within the author's ownership area (per CODEOWNERS)
```

### 4.5 PR Lifecycle

```
1. Developer creates feature branch from main
2. Developer implements (test-first workflow)
3. Developer pushes and creates PR → main
4. CI pipeline runs automatically (6 quality gates)
5. AI review bot posts comments
6. Code owner reviews and provides feedback
7. Developer addresses feedback, pushes fixes
8. Code owner approves
9. "Squash and merge" into main
10. Delete the feature branch
```

---

## 5. Code Ownership (CODEOWNERS)

The project uses a `.github/CODEOWNERS` file to enforce review assignments:

| Area | Owner | Must Approve |
|------|-------|-------------|
| `backend/optimization/` | Person A | Any change to optimization pipeline |
| `backend/interview/` | Person A | Any change to interview agents |
| `backend/shared/` | Person B | Any change to shared kernel |
| `backend/identity/` | Person B | Any change to auth/tenant |
| `backend/resume/` | Person B | Any change to resume parsing |
| `backend/billing/` | Person B | Any change to billing |
| `frontend/` | Person B | Any frontend change |
| `backend/shared/domain/` | **Both** | Shared domain base classes — both must approve |
| `backend/config.py` | **Both** | Application config — both must approve |
| `docs/` | **Both** | Documentation — both must approve |

---

## 6. Release Process

### 6.1 Tagging a Release

With trunk-based development, `main` is always production-ready. To cut a release:

```bash
git checkout main
git pull origin main
make test && make lint   # All green

git tag -a v0.1.0 -m "v0.1.0 — MVP launch"
git push origin v0.1.0
```

This triggers the CD pipeline (build -> deploy) if configured for tags.

### 6.2 Hotfix (production emergency)

```bash
# 1. Branch from main
git checkout main
git pull origin main
git checkout -b hotfix/auth-token-crash

# 2. Fix the bug (test-first!)
# ... write test, implement fix ...

# 3. Push and create PR → main
git push -u origin hotfix/auth-token-crash

# 4. After review and merge to main (triggers deploy)
```

---

## 7. Conflict Resolution

### 7.1 Preventing Conflicts

| Practice | Description |
|----------|-------------|
| **Sync daily** | Run `git fetch && git rebase origin/main` on your feature branch daily. |
| **Small PRs** | Keep PRs under 400 lines. Smaller changes = fewer conflicts. |
| **Communicate** | If two people need to edit the same file, coordinate via chat first. |
| **Bounded contexts** | DDD structure naturally reduces conflicts — each person works in separate directories. |

### 7.2 Resolving Conflicts

```bash
# 1. Update your branch
git fetch origin
git rebase origin/main

# 2. Git will pause at conflicts. For each conflicted file:
#    - Open the file and look for conflict markers:
#      <<<<<<< HEAD
#      (their changes)
#      =======
#      (your changes)
#      >>>>>>> your-branch

# 3. Edit the file to resolve (keep the correct version)

# 4. Mark as resolved and continue
git add <resolved-file>
git rebase --continue

# 5. If things go wrong, abort and start over
git rebase --abort
```

### 7.3 Common Conflict Scenarios

| Scenario | Who Resolves | Strategy |
|----------|-------------|----------|
| Both edited `config.py` | The person who merges second | Keep both changes (usually additive). |
| Both edited `shared/domain/base_entity.py` | Discuss together | Schedule a quick call; shared kernel changes need consensus. |
| Both edited the same API route file | Should not happen | Each person owns different bounded contexts. If it happens, something is wrong with the architecture split. |
| `package-lock.json` or `requirements.txt` conflict | Accept theirs, then re-run install | `git checkout --theirs package-lock.json && npm install` |

---

## 8. Git Configuration Recommendations

### 8.1 Recommended Git Settings

```bash
# Set your identity
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Use rebase by default when pulling
git config pull.rebase true

# Auto-prune deleted remote branches
git config fetch.prune true

# Better diff output
git config diff.algorithm histogram

# Default branch for new repos
git config init.defaultBranch main
```

### 8.2 Useful Aliases

```bash
# Add to ~/.gitconfig [alias] section
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.st status
git config --global alias.cm "commit -m"
git config --global alias.lg "log --oneline --graph --decorate -15"
git config --global alias.sync "!git fetch origin && git rebase origin/main"
```

---

## 9. Quick Reference Card

```
┌─────────────────────── Daily Workflow ───────────────────────┐
│                                                              │
│  git checkout main && git pull                                │
│  git checkout -b feature/optimization-rag-pipeline           │
│                                                              │
│  ... write tests first, then implement ...                   │
│                                                              │
│  git add . && git commit -m "feat(optimization): ..."        │
│  git push -u origin feature/optimization-rag-pipeline        │
│                                                              │
│  → Create PR on GitHub (target: main)                        │
│  → Wait for CI (6 checks) + AI review + human review         │
│  → Squash and merge                                          │
│  → Delete feature branch                                     │
│                                                              │
├─────────────────────── Keep in Sync ─────────────────────────┤
│                                                              │
│  git fetch origin && git rebase origin/main                  │
│  (do this daily to avoid conflicts)                          │
│                                                              │
├─────────────────────── Commit Format ────────────────────────┤
│                                                              │
│  feat(optimization): add ATS scoring agent                   │
│  fix(resume): handle empty PDF upload                        │
│  test(identity): add tenant isolation tests                  │
│  refactor(shared): extract base repository class             │
│  docs: update API documentation                              │
│  chore: upgrade LangChain to 0.2.5                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```
