---
description: Structure of scope documents, checked by scope validation.
stage: source
data:
  sections: ["Goal", "Non-Goals", "Invariants", "Conventions", "Decisions"]
  axes: ["Data & types", "Errors", "Effects", "State", "Dependencies & boundaries", "Naming", "Testing", "Config & tooling", "Prose & output"]
---

# Scope

Rules for `scope.md` files whose frontmatter names an `issue_type`. Scope validation runs them with `henia lint <scope>/scope.md`.

## scope-missing-section

A scope states its Goal, Non-Goals, Invariants, Conventions and Decisions.

```hq
(rule scope-missing-section
  :severity error
  :message "scope has no ## {?section} section"
  :at @f
  (row :table sections :value ?section)
  (file :path ?p (frontmatter :issue_type /^(Initiative|Feature|Task)$/)) @f
  (not (file :path ?p (section :level 2 :title ?section))))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Goal

Ship it.
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Goal

Ship it.

## Non-Goals

- No rewrite

## Invariants

| ID | Invariant | Check |
|----|-----------|-------|
| INV-1 | keeps x | `test/x.test.ts` |

## Conventions

| Axis | Resolution | Exemplar |
|------|------------|----------|
| Data & types | loqui | `src/a.ts` |
| Errors | loqui | `src/a.ts` |
| Effects | loqui | `src/a.ts` |
| State | loqui | `src/a.ts` |
| Dependencies & boundaries | loqui | `src/a.ts` |
| Naming | loqui | `src/a.ts` |
| Testing | loqui | `src/a.ts` |
| Config & tooling | loqui | `src/a.ts` |
| Prose & output | loqui | `src/a.ts` |

## Decisions

- AD-1: keep it; rejected rewrite: cost
```

## scope-missing-axis

Conventions resolves every fixed axis in its own row.

```hq
(rule scope-missing-axis
  :severity error
  :message "Conventions has no {?axis} row"
  :at @s
  (row :table axes :value ?axis)
  (file :path ?p (frontmatter :issue_type /^(Initiative|Feature|Task)$/) (section :title "Conventions") @s)
  (not (file :path ?p (section :title "Conventions" (table (row (cell :column "Axis" :text ?axis)))))))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Conventions

| Axis | Resolution | Exemplar |
|------|------------|----------|
| Errors | loqui | `src/a.ts` |
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Conventions

| Axis | Resolution | Exemplar |
|------|------------|----------|
| Data & types | loqui | `src/a.ts` |
| Errors | loqui | `src/a.ts` |
| Effects | loqui | `src/a.ts` |
| State | loqui | `src/a.ts` |
| Dependencies & boundaries | loqui | `src/a.ts` |
| Naming | loqui | `src/a.ts` |
| Testing | loqui | `src/a.ts` |
| Config & tooling | loqui | `src/a.ts` |
| Prose & output | loqui | `src/a.ts` |
```

## scope-unresolved-axis

Every Conventions row names a resolution and an exemplar.

```hq
(rule scope-unresolved-axis
  :severity error
  :message "{?axis} has no {?column}"
  :at @r
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/)
    (section :title "Conventions"
      (table (row :header false (cell :column "Axis" :text ?axis) (cell :column /^(?<column>Resolution|Exemplar)$/ :text "")) @r))))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Conventions

| Axis | Resolution | Exemplar |
|------|------------|----------|
| Errors | loqui |  |
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Conventions

| Axis | Resolution | Exemplar |
|------|------------|----------|
| Errors | loqui | `src/a.ts` |
```

## scope-unchecked-invariant

Every invariant names the check that holds it.

```hq
(rule scope-unchecked-invariant
  :severity error
  :message "{?id} names no check"
  :at @r
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/)
    (section :title "Invariants"
      (table (row :header false (cell :column "ID" :text ?id) (cell :column "Check" :text "")) @r))))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Invariants

| ID | Invariant | Check |
|----|-----------|-------|
| INV-1 | keeps x |  |
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Invariants

| ID | Invariant | Check |
|----|-----------|-------|
| INV-1 | keeps x | `test/x.test.ts` |
```

## scope-placeholder

No template placeholder survives into a scope.

```hq
(rule scope-placeholder
  :severity error
  :message "template placeholder left: {@p.text}"
  :at @p
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/)
    [(paragraph :matches /\$\{[A-Z_]+\}/) (heading :matches /\$\{[A-Z_]+\}/) (item :matches /\$\{[A-Z_]+\}/) (cell :matches /\$\{[A-Z_]+\}/)] @p))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Goal

${OUTCOME_AND_WHY}
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Goal

Ship it.
```

## scope-long-goal

The Goal fits in three lines.

```hq
(rule scope-long-goal
  :severity error
  :message "Goal runs past three lines; move rationale to design.md"
  :at @p
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/) (section :title "Goal" (paragraph :lines (> 3)) @p)))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Goal

One.
Two.
Three.
Four.
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Goal

Ship it.
```

## scope-multiline-item

Each non-goal and decision is one line.

```hq
(rule scope-multiline-item
  :severity error
  :message "a {?section} entry spans several lines"
  :at @i
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/) (section :title /^(?<section>Non-Goals|Decisions)$/ (item :lines (> 1)) @i)))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Non-Goals

- No rewrite,
  and no new module
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Non-Goals

- No rewrite
```

## scope-frontmatter

A scope's frontmatter names a known `status` and `issue_type`.

```hq
(rule scope-frontmatter
  :severity error
  :message "status must be draft, active or done"
  :at @f
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/ :status (not /^(draft|active|done)$/))) @f)
(rule scope-frontmatter
  :severity error
  :message "issue_type must be Initiative, Feature or Task"
  :at @f
  (file (frontmatter :status /^(draft|active|done)$/ :issue_type (not /^(Initiative|Feature|Task)$|^\$\{/))) @f)
```

### Matches

```md
---
status: draft
issue_type: Epic
---

## Goal

Ship it.
```

### Passes

```md
---
status: active
issue_type: Feature
---

## Goal

Ship it.
```

## scope-decision-shape

Each decision names what was chosen and the alternative it rejected, with the reason.

```hq
(rule scope-decision-shape
  :severity error
  :message "write the decision as AD-n: <decision>; rejected <alternative>: <reason>"
  :at @i
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/)
    (section :title "Decisions" > (list > (item :text (not /^AD-\d+: [^;]+; rejected [^:]+: .+/)) @i))))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Decisions

- Keep the parser.
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Decisions

- AD-1: keep the parser; rejected a rewrite: no gain
```

## scope-uncovered-requirement

Every functional requirement has an acceptance criterion that cites it.

```hq
(rule scope-uncovered-requirement
  :severity error
  :message "no acceptance criterion cites {?fr}"
  :at @i
  (file :path ?p (frontmatter :issue_type /^(Initiative|Feature|Task)$/)
    (section :title "Functional Requirements" (item :text /^(?<fr>FR-\d+):/) @i))
  (not (file :path ?p (section :title "Acceptance Criteria" (item :text (contains ?fr))))))
```

### Matches

```md
---
status: draft
issue_type: Task
---

### Functional Requirements

- FR-1: the parser MUST keep tables
- FR-2: the parser MUST keep cells

## Acceptance Criteria

- [ ] AC-1 (FR-1): Given a table, when parsed, then rows exist
```

### Passes

```md
---
status: draft
issue_type: Task
---

### Functional Requirements

- FR-1: the parser MUST keep tables

## Acceptance Criteria

- [ ] AC-1 (FR-1): Given a table, when parsed, then rows exist
```

## scope-dangling-criterion

An acceptance criterion cites only requirements the scope defines.

```hq
(rule scope-dangling-criterion
  :severity error
  :message "{?fr} is not a requirement of this scope"
  :at @i
  (file :path ?p (frontmatter :issue_type /^(Initiative|Feature|Task)$/)
    (section :title "Acceptance Criteria" (item :text /\((?<fr>FR-\d+)\)/) @i))
  (not (file :path ?p (section :title "Functional Requirements" (item :text (contains ?fr))))))
```

### Matches

```md
---
status: draft
issue_type: Task
---

### Functional Requirements

- FR-1: the parser MUST keep tables

## Acceptance Criteria

- [ ] AC-1 (FR-7): Given a table, when parsed, then rows exist
```

### Passes

```md
---
status: draft
issue_type: Task
---

### Functional Requirements

- FR-1: the parser MUST keep tables

## Acceptance Criteria

- [ ] AC-1 (FR-1): Given a table, when parsed, then rows exist
```

## scope-duplicate-id

Each requirement, criterion, decision and invariant id is used once.

```hq
(rule scope-duplicate-id
  :severity error
  :message "{?id} is used twice"
  :at @b
  (file :path ?p (frontmatter :issue_type /^(Initiative|Feature|Task)$/) (item :text /^(\[[ x]\] )?(?<id>(AD|FR|TR|AC)-\d+)\b/ :node ?n) @a)
  (file :path ?p (item :text /^(\[[ x]\] )?(?<id>(AD|FR|TR|AC)-\d+)\b/ :node (after ?n)) @b))
(rule scope-duplicate-id
  :severity error
  :message "{?id} is used twice"
  :at @b
  (file :path ?p (frontmatter :issue_type /^(Initiative|Feature|Task)$/) (cell :column "ID" :text /^(?<id>INV-\d+)$/ :node ?n) @a)
  (file :path ?p (cell :column "ID" :text /^(?<id>INV-\d+)$/ :node (after ?n)) @b))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Decisions

- AD-1: keep the parser; rejected a rewrite: no gain
- AD-1: keep the cells; rejected regexes: brittle
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Decisions

- AD-1: keep the parser; rejected a rewrite: no gain
- AD-2: keep the cells; rejected regexes: brittle
```

## scope-check-not-runnable

An invariant's check names a test, command or rule id in a code span, not prose.

```hq
(rule scope-check-not-runnable
  :severity error
  :message "{?id} check is prose; name a test, command or rule id in backticks"
  :at @r
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/)
    (section :title "Invariants"
      (table (row :header false (cell :column "ID" :text ?id) (cell :column "Check" :text /./ :matches (not /\$\{/) (not (code :inline true)))) @r))))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Invariants

| ID | Invariant | Check |
|----|-----------|-------|
| INV-1 | keeps x | reviewers look at it |
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Invariants

| ID | Invariant | Check |
|----|-----------|-------|
| INV-1 | keeps x | `test/x.test.ts` |
```

## scope-exemplar-not-a-path

An exemplar is the path of existing code in a code span, or `n/a`.

```hq
(rule scope-exemplar-not-a-path
  :severity error
  :message "{?axis} exemplar is not a path in backticks or n/a"
  :at @r
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/)
    (section :title "Conventions"
      (table (row :header false (cell :column "Axis" :text ?axis) (cell :column "Exemplar" :text (not /^(n\/a)?$/) (not (code :inline true)))) @r))))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Conventions

| Axis | Resolution | Exemplar |
|------|------------|----------|
| Errors | loqui | the error module |
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Conventions

| Axis | Resolution | Exemplar |
|------|------------|----------|
| Errors | loqui | `src/errors.ts` |
| Effects | n/a | n/a |
```

## scope-open-question

Open questions live in `validation.yaml` as assumptions, not as markers in the scope.

```hq
(rule scope-open-question
  :severity error
  :message "open question in the scope; record it as an assumption in validation.yaml"
  :at @q
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/)
    [(paragraph :matches /\b(TODO|TBD|FIXME)\b/) (item :matches /\b(TODO|TBD|FIXME)\b/) (cell :matches /\b(TODO|TBD|FIXME)\b/) (heading :matches /\b(TODO|TBD|FIXME)\b/)] @q))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Goal

Ship it. TBD which parser.
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Goal

Ship it.
```

## scope-missing-user-stories

An Initiative states its user stories.

```hq
(rule scope-missing-user-stories
  :severity error
  :message "an Initiative scope has no ## User Stories section"
  :at @f
  (file (frontmatter :issue_type "Initiative") (not (section :level 2 :title "User Stories"))) @f)
```

### Matches

```md
---
status: draft
issue_type: Initiative
---

## Goal

Ship it.
```

### Passes

```md
---
status: draft
issue_type: Initiative
---

## Goal

Ship it.

## User Stories

- US001 (P1): a user ships; independent test: `mise run ship`
```

## scope-empty-section

Non-Goals and Decisions hold at least one entry.

```hq
(rule scope-empty-section
  :severity error
  :message "{?section} has no entries"
  :at @s
  (file (frontmatter :issue_type /^(Initiative|Feature|Task)$/)
    (section :level 2 :title /^(?<section>Non-Goals|Decisions)$/ (not (item))) @s))
```

### Matches

```md
---
status: draft
issue_type: Task
---

## Non-Goals

None.
```

### Passes

```md
---
status: draft
issue_type: Task
---

## Non-Goals

- No rewrite
```
