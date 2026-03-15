---
name: implement
description: Implementation methodology. Use when building features, writing code, or creating artifacts from requirements.
argument-hint: "[target]"
metadata:
  type: generic
---

## Pre-loaded Context

Git status:
!`git status --short 2>/dev/null`

Current branch:
!`git branch --show-current 2>/dev/null`

# Implementation Methodology

Understand requirements, plan approach, build incrementally, verify.

---

## When to Use

- Building features from requirements
- Writing code or creating artifacts
- Deciding on structure, patterns, or approach
- Designing domain models or data structures

**Workflow Integration:**
- **Multiple independent tasks from a scope?** → Use `dispatch` skill instead (it routes to the right execution workflow)
- **Single implementation task?** → Use this skill directly

---

## Git Workflow

When implementing from a spec:

1. **Create a branch for the scope** (if not already on one):
   - Branch from main/master
   - Name: `feat/<scope-name>`
   - Example: `feat/user-auth` for `./scopes/user-auth/`

2. **Verify before starting:**
   - Confirm you're on the correct scope branch
   - Pull latest if branch already exists

---

## Process

### 1. Understand Requirements

- Read the spec/task description
- Identify acceptance criteria
- Note edge cases and constraints

### 2. Plan Approach

- Identify affected files and modules
- Choose patterns appropriate to the domain
- Consider dependencies and ordering

### 3. Build Incrementally

- Start with the simplest working version
- Add complexity only as needed
- Verify each step before moving on

### 4. Verify

- Run relevant tests
- Check against acceptance criteria
- Ensure no regressions

---

## Domain Context

Domain skills inject specifics into this generic methodology:
- **code**: Language guidelines (loqui), code intelligence (gestalt), review roles
- **doc**: Templates, structure, style guides

When invoked via a domain skill, follow the domain-specific guidance provided.

---

## Related Skills

- **dispatch**: Use for multiple independent implementation tasks
- **test**: Use for TDD workflow (write test first, then implement)
- **review**: Review methodology for completed work
