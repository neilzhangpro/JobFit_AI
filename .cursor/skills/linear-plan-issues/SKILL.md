---
name: linear-plan-issues
description: Parse discussed requirements and create Linear issues with standardized title format [px][type][module]. Use when the user finishes discussing a feature, bug, or improvement and wants to write it into Linear, or says "写入Linear", "创建需求", "记录issue", "plan issues".
---

# Linear Issue Planning

Create Linear issues from discussed requirements using standardized naming.

## Title Format

```
[p{priority}][{type}][{module}] {title}
```

- **priority**: 1=Urgent, 2=High, 3=Normal, 4=Low
- **type**: Feature, Bug, Improvement
- **module**: identity, resume, optimization, interview, billing, shared, frontend
- **title**: concise description in English

Examples:

```
[p2][Feature][optimization] Implement JD keyword extraction
[p1][Bug][resume] Fix PDF parsing for multi-column layouts
[p3][Improvement][identity] Add OAuth2 social login support
```

## Workflow

### Step 1: Extract from Conversation

Parse the discussion to identify:
1. What type of work (Feature / Bug / Improvement)
2. Which bounded context module it belongs to
3. Priority level (default p3 if not specified)
4. A concise English title
5. A Markdown description summarizing requirements and acceptance criteria

Present the extracted info to the user for confirmation before creating.

### Step 2: Create Linear Issue

Use the Linear MCP `create_issue` tool with these parameters:

```
server: plugin-linear-linear
toolName: create_issue
arguments:
  title: "[p{n}][{Type}][{module}] {title}"
  team: "JobFit_AI"
  project: "JobFit_AI"
  priority: {1-4}          # matches the p-number
  labels: ["{Type}"]       # one of: Feature, Bug, Improvement
  state: "Backlog"         # new issues start in Backlog
  description: |
    ## Summary
    {requirement summary}

    ## Acceptance Criteria
    - [ ] {criterion 1}
    - [ ] {criterion 2}

    ## Bounded Context
    {module}

    ## Branch Naming
    {feature|fix|improvement}/{module}-{short-description}
```

### Step 3: Confirm

After creation, display:
- Issue identifier (e.g. JOB-42)
- Title
- Priority and labels
- Link to the issue

### Batch Mode

If the user discusses multiple requirements, create them all at once. Present a summary table before creating:

```
| # | Title | Priority | Type | Module |
|---|-------|----------|------|--------|
| 1 | ...   | p2       | Feature | optimization |
| 2 | ...   | p1       | Bug    | resume       |
```

Ask for confirmation, then create all issues sequentially.

## Linear Configuration Reference

| Field | Value |
|-------|-------|
| Team | JobFit_AI |
| Project | JobFit_AI |
| Statuses | Backlog → Todo → In Progress → Done (also: Canceled, Duplicate) |
| Labels | Feature, Bug, Improvement |
| Priority | 1=Urgent, 2=High, 3=Normal, 4=Low |
| Bounded Contexts | identity, resume, optimization, interview, billing, shared, frontend |
