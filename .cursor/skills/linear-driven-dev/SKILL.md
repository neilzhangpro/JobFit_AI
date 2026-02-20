---
name: linear-driven-dev
description: Fetch the highest-priority Linear issue, create a git branch, assist development with human-in-the-loop, commit, push, and update Linear status. Use when the user says "开始开发", "拉取需求", "下一个任务", "start dev", or wants to begin working on the next Linear issue.
---

# Linear-Driven Development

Human-in-the-loop workflow: pick issue → branch → **collaborative development** → commit → push → update Linear.

The user drives every phase. AI assists but NEVER proceeds to the next phase without explicit user confirmation.

## Prerequisites

- Git remote `origin` points to GitHub
- Current branch is `main` or can switch to it
- `gh` CLI authenticated (`gh auth status` passes)

## Workflow

### Phase 1: Pick Next Issue

Fetch the highest-priority unstarted issue assigned to the current user.

```
Call Linear MCP:
  server: plugin-linear-linear
  toolName: list_issues
  arguments:
    team: "JobFit_AI"
    state: "Todo"
    assignee: "me"
    orderBy: "updatedAt"
    limit: 10
```

If no "Todo" issues, also check "Backlog":

```
  arguments:
    state: "Backlog"
    assignee: "me"
```

Sort results by priority (1 first), present the top candidate to the user:

```
Issue: JOB-42
Title: [p2][Feature][optimization] Implement JD keyword extraction
Priority: High
Description: ...
```

**WAIT**: Ask user to confirm or pick a different issue. Do NOT proceed until user responds.

### Phase 2: Prepare Branch

Only after user confirms the issue in Phase 1.

Run these git commands sequentially:

```bash
git checkout main
git fetch origin
git rebase origin/main
```

Parse the issue title to derive branch name:
- `[Feature]` → `feature/`
- `[Bug]` → `fix/`
- `[Improvement]` → `improvement/`
- Module and short description form the rest

```bash
git checkout -b feature/{module}-{short-description}
```

Example: `[p2][Feature][optimization] Implement JD keyword extraction` → `feature/optimization-jd-keyword-extraction`

Update Linear issue status to "In Progress":

```
Call Linear MCP:
  server: plugin-linear-linear
  toolName: update_issue
  arguments:
    id: "{issue_id}"
    state: "In Progress"
```

Inform the user that the branch is ready and development can begin.

### Phase 3: Develop (Human-Driven, AI-Assisted)

**CRITICAL: This phase is fully controlled by the user. Do NOT auto-advance to Phase 4.**

Follow the project's `workflow.mdc` rules strictly:

1. **Understand**: Read relevant docs in `docs/` for the bounded context
2. **Test First**: Write failing tests before implementation
3. **Implement**: Write simplest code to pass tests, follow DDD layers
4. **Verify**: Run `make lint` and `make test`

How to collaborate:
- The user may ask AI to write code, review code, run tests, or debug
- The user may also code manually and only ask AI for specific help
- AI responds to each request individually and waits for the next instruction
- AI does NOT chain multiple development steps together unprompted

**STOP here and wait.** Only proceed to Phase 4 when the user explicitly signals completion, such as:
- "开发完成" / "done" / "提交代码" / "可以提交了" / "commit"

### Phase 4: Pre-Commit Review

When the user signals development is complete:

**4a. Run verification**

```bash
make lint
make test
```

Present the results to the user. If either fails, help fix issues — do NOT proceed to commit.

**WAIT**: Both must pass. Ask user: "Lint 和测试均已通过，是否继续提交？"

**4b. Preview commit message**

Generate the commit message and show it to the user BEFORE committing:

Map from issue metadata:
- `[Feature]` → `feat({module}):`
- `[Bug]` → `fix({module}):`
- `[Improvement]` → `refactor({module}):` or `perf({module}):`

```
Proposed commit message:
  feat({module}): {concise description}

  {Why this change was made}

  Linear: JOB-{number}
```

**WAIT**: Ask user to confirm or modify the commit message.

### Phase 5: Commit, Push & Update Linear

Only after user confirms the commit message in Phase 4.

**5a. Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
{confirmed commit message}
EOF
)"
```

**5b. Push**

```bash
git push -u origin HEAD
```

**5c. Update Linear**

```
Call Linear MCP:
  server: plugin-linear-linear
  toolName: update_issue
  arguments:
    id: "{issue_id}"
    state: "Done"
```

### Phase 6: Handoff to PR

After push completes, inform the user:

```
Development complete:
- Branch: feature/optimization-jd-keyword-extraction
- Commits: 1 (feat(optimization): implement JD keyword extraction)
- Linear: JOB-42 → Done
- Next step: say "创建PR" to create a pull request
```

## Linear Configuration Reference

| Field | Value |
|-------|-------|
| Team | JobFit_AI |
| Project | JobFit_AI |
| Status flow | Backlog → Todo → **In Progress** → **Done** |
| Labels | Feature, Bug, Improvement |
| Priority | 1=Urgent, 2=High, 3=Normal, 4=Low |

## Branch Naming Reference

| Issue Type | Branch Prefix | Example |
|------------|---------------|---------|
| Feature | `feature/` | `feature/optimization-jd-analyzer` |
| Bug | `fix/` | `fix/resume-pdf-parsing` |
| Improvement | `improvement/` | `improvement/identity-oauth2-login` |
