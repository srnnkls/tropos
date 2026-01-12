---
name: code-review
description: Code review methodology. Use when reviewing code locally or preparing for a PR review.
---

# Code Review Skill

Generic code review process and methodology. Language-agnostic review guidelines.

---

## When to Use

- Reviewing code changes locally
- Preparing review feedback before a PR
- Understanding what to look for in code
- Categorizing and prioritizing issues

---

## Review Process

### Step 1: Understand Context

Before reviewing code, understand:
- What problem is being solved?
- What are the requirements or acceptance criteria?
- Are there related issues or prior discussions?

### Step 2: Detect Language and Load Guidelines

Identify the primary language and load appropriate guidelines from the `code-implement` skill

### Step 3: Review by Category

Review code across these focus areas:

| Category | What to Check |
|----------|---------------|
| **Correctness** | Logic errors, edge cases, error handling, type safety |
| **Style** | Naming, formatting, code organization, idioms |
| **Performance** | Efficiency, data structures, unnecessary work |
| **Security** | Input validation, secrets, injection risks |
| **Architecture** | Design patterns, coupling, separation of concerns |

### Step 4: Categorize by Severity

Assign severity to each issue:

| Severity | Definition | Action |
|----------|------------|--------|
| **Critical** | Blocks merge - bugs, security issues, data corruption | Must fix |
| **High** | Should fix - significant issues, unclear behavior | Fix before merge |
| **Medium** | Nice to fix - style, minor improvements | Can merge, follow-up |

### Step 5: Provide Actionable Feedback

For each issue:
1. Identify the specific location
2. Explain what's wrong (reference guidelines if applicable)
3. Suggest a concrete fix or alternative

---

## Review Checklist

See [resources/checklist.md](resources/checklist.md) for a generic review checklist.

---

## Language-Specific Guidelines

For language-specific patterns and anti-patterns, delegate to:

- **code-implement**: Language guidelines and implementation patterns

---

## Related Skills

- **code-implement**: Language-specific coding guidelines
- **pr-review**: GitHub PR workflow (delegates here for methodology)
