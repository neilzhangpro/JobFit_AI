---
name: pr-ci-merge
description: Create GitHub pull request, monitor CI checks, fix failures, and merge when green. Use when the user says "创建PR", "提交PR", "检查CI", "合并PR", "create PR", "merge", or after completing development and pushing a branch.
---

# PR, CI & Merge Workflow

Automate: create PR → monitor CI → fix failures → merge to main.

## Prerequisites

- `gh` CLI authenticated: run `gh auth login -h github.com` if not
- Current branch is NOT `main` (must be a feature/fix branch)
- Branch is pushed to `origin` (`git push -u origin HEAD`)

## Workflow

### Step 1: Create Pull Request

**1a. Gather context**

Run in parallel:
- `git log main..HEAD --oneline` — list all commits on this branch
- `git diff main...HEAD --stat` — show changed files summary
- Parse the branch name for type and module (e.g. `feature/optimization-jd-analyzer`)

**1b. Check PR size**

Count total changed lines:

```bash
git diff main...HEAD --shortstat
```

If > 400 lines, warn the user per project rules and suggest splitting.

**1c. Build PR content**

Map branch prefix to Conventional Commits title:
- `feature/` → `feat({module}): {description}`
- `fix/` → `fix({module}): {description}`
- `improvement/` → `refactor({module}): {description}`

PR body template:

```markdown
## Summary
- {bullet point summary of changes}

## Motivation
{Why this change is needed — reference Linear issue}

## Changes
- {list of key changes}

## Testing Checklist
- [ ] Unit tests pass (`make test`)
- [ ] Lint passes (`make lint`)
- [ ] Coverage >= 80% overall, >= 90% domain layer
- [ ] Tenant isolation test included (if repository changes)
- [ ] No `any` types (TS), no bare `except` (Python)

Linear: JOB-{number}
```

**1d. Create PR**

```bash
git push -u origin HEAD

gh pr create \
  --title "feat({module}): {description}" \
  --body "$(cat <<'EOF'
{PR body from template above}
EOF
)"
```

Display the PR URL to the user.

### Step 2: Monitor CI

**2a. Wait and check**

CI typically takes 2-5 minutes. Poll with exponential backoff:

```bash
sleep 30
gh pr checks --watch --fail-fast 2>&1 || true
```

If `--watch` is not supported, poll manually:

```bash
gh pr checks
```

Repeat every 30s until all checks complete or fail.

**2b. Interpret results**

If ALL checks pass → go to Step 4 (Merge).
If ANY check fails → go to Step 3 (Fix).

### Step 3: Fix CI Failures

**3a. Get failure details**

```bash
gh pr checks
```

Identify which check(s) failed. For GitHub Actions:

```bash
gh run list --branch "$(git branch --show-current)" --limit 5
gh run view {run_id} --log-failed
```

**3b. Analyze and fix**

Read the error output and identify the root cause:
- Lint errors → run `make lint`, fix violations
- Test failures → read test output, fix code or tests
- Type errors → run `mypy --strict` or `tsc --noEmit`, fix types
- Build errors → check dependency issues

**3c. Push fix**

```bash
git add -A
git commit -m "$(cat <<'EOF'
fix({module}): resolve CI failures

{Brief description of what was fixed}
EOF
)"
git push
```

**3d. Re-monitor**

Return to Step 2. Repeat until all checks pass.

Maximum 3 fix iterations — if still failing after 3 attempts, stop and ask the user for help.

### Step 4: Merge

Once all CI checks pass:

**4a. Confirm with user**

```
All CI checks passed:
  ✓ lint
  ✓ test
  ✓ build
  ✓ type-check
  ✓ coverage
  ✓ security

Ready to merge. Proceed? (squash merge to main)
```

**4b. Execute merge**

```bash
gh pr merge --squash --delete-branch
```

**4c. Clean up local**

```bash
git checkout main
git pull origin main
```

**4d. Report**

```
Merge complete:
- PR: #{pr_number} merged to main
- Branch: {branch_name} deleted
- Linear: JOB-{number} → Done
- Local main updated
```

## Error Handling

| Scenario | Action |
|----------|--------|
| `gh` not authenticated | Print: `gh auth login -h github.com` and stop |
| Branch not pushed | Run `git push -u origin HEAD` first |
| PR already exists | Use `gh pr view` to get existing PR, continue from Step 2 |
| Merge conflicts | Run `git fetch origin && git rebase origin/main`, resolve conflicts, force push with `--force-with-lease` |
| CI fails > 3 times | Stop auto-fix loop, present full error log to user |

## gh CLI Quick Reference

| Action | Command |
|--------|---------|
| Create PR | `gh pr create --title "..." --body "..."` |
| View PR | `gh pr view` |
| Check CI | `gh pr checks` |
| List runs | `gh run list --branch {branch}` |
| View failed logs | `gh run view {id} --log-failed` |
| Merge (squash) | `gh pr merge --squash --delete-branch` |
