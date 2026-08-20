# Scope → Issue

Publish a scope as a GitHub issue tree, delegating each issue to the `issue` skill.

The scope's `issue_type` decides the shape of the tree:

| Scope `issue_type` | Issue tree |
|---|---|
| Task | 1 **Task** issue |
| Feature | 1 **Feature** issue + *n* **Task** sub-issues (one per task in `tasks.yaml`) |
| Initiative | 1 **Initiative** issue + *n* **Feature** issues (one per phase) + *n×m* **Task** sub-issues (the tasks in each phase) |

Each issue is authored, gated (the `issue` skill's mandatory 2×2 review), and published by the `issue` skill — this operation only orchestrates the tree: deriving nodes, ordering publication so parents exist before children, and wiring edges from the scope's dependency graph.

---

## Workflow

### Step 1: Locate and load the scope

1. Resolve the name: `/scope issue <name>` → search `scopes/{draft,active,done}/<name>/`; no argument → the branch-associated scope, else the most recent `scopes/*/*/scope.md`.
2. Read `scope.md` (frontmatter `issue_type` drives the tree), `tasks.yaml`, `dependencies.yaml` (if present), and `design.md` (if present).
3. If `issue_type` is missing, ask via **AskUserQuestion** (`Initiative | Feature | Task`) before continuing.

### Step 2: Derive the issue tree

Map scope artifacts to nodes. Carry each node's source slice (the scope sections / task / phase it derives from) so the authoring subagent has its raw material, and the source **task id** so edges resolve later.

- **Task** → one Task node sourced from `scope.md` (Goal, Requirements, Acceptance Criteria).
- **Feature** → a Feature root sourced from `scope.md`; one Task node per entry in `tasks.yaml` `tasks[]`, sourced from that task's `content` / `files` / `depends_on`.
- **Initiative** → an Initiative root sourced from `scope.md`; one Feature node per `phases[]` entry (`dependencies.yaml` `phases[]` when present, else `tasks.yaml` `phases[]`); under each Feature, one Task node per task id the phase references. A task that no phase references is an error — surface it and ask whether to attach it to a phase or skip; never drop it silently.

**Edges** come from the scope, never invented:
- **Parent** — the tree hierarchy (Task→Feature→Initiative).
- **Depends-on** — each task's `depends_on` in `tasks.yaml`, translated from task ids to the published issue numbers (see Step 5). Phase-level `depends_on` (in `dependencies.yaml`) becomes Feature→Feature depends-on edges.

### Step 3: Confirm tree and root parent

Render the planned tree (each node's type, title `<Module> — <summary>`, and its parent / depends-on edges) so the user sees exactly what will be published. Then, via **AskUserQuestion**:

- **Root parent.** Pre-seed plausible parents from `gh issue list --state open --search "type:<ParentType>" --json number,title --limit 20` (an Initiative or standalone Feature may sit under an existing Initiative; a Task under an existing Feature). Offer `No parent`. Never infer silently.
- **Proceed gate.** Publishing is outward-facing and runs *n* review gates — confirm before any subagent publishes. Offer `Proceed`, `Edit tree`, `Cancel`.

For large trees, state the issue count up front (`1 + n + Σmᵢ`) so the user knows the gate cost before confirming.

### Step 4: Author + publish, level by level

Publish **top-down** so `--parent` always resolves against an existing number. Within a level the nodes are independent — dispatch them as **parallel subagents in one message** (per CLAUDE.md: only Task subagents parallelize).

```
Level 1: root            → 1 subagent          → capture root number
Level 2: Features        → n subagents (∥)     → capture {phase → Feature number}
Level 3: Tasks           → Σmᵢ subagents (∥)   → capture {task id → Task number}
```

(Feature scope collapses to Level 1 + Level 3; Task scope to Level 1 only.)

Each subagent runs the **`issue` skill** end-to-end for its single node — orient (`gestalt map`), draft the body to `.issues/` against the canonical template, clear the 2×2 review gate, and publish — with the structural metadata **predetermined** so the skill does not stop to ask:

> Invoke the `issue` skill to author and publish one issue. Do **not** ask for issue type or parent — they are fixed:
> - **Type:** `<Initiative|Feature|Task>`
> - **Parent:** `<resolved parent number, or none for the root>` — pass as `--parent <n>` at publish.
> - **Do not set depends-on/blocks** — sibling numbers aren't known yet; the orchestrator wires them after.
> - **Title:** `<Module> — <summary>` (em-dash).
> - **Source material:** <the node's scope slice — Goal/Requirements/Acceptance for the root; task `content`/`files` for a Task; phase name + member tasks for a Feature>.
> Run the full authoring workflow including the mandatory 2×2 gate. Return `<task-id>\t<number>\t<url>`.

Collect each level's returned numbers before dispatching the next — the parent map for Level *k+1* is built from Level *k*'s results. If a subagent fails its gate or dies, report which node failed and stop before wiring edges; a half-built tree with missing parents is worse than none.

### Step 5: Wire dependency edges

After every node is published, build the `task id → issue number` map (and `phase → Feature number`). For each task with `depends_on`, translate the ids and apply once:

```bash
issue depends-on <child#> <dep#,…>     # A depends on B  ⇒  A blockedBy B
```

Apply phase-level `depends_on` the same way between the Feature issues. Edges are applied in this single pass (not folded into publish) because siblings publish in parallel and don't know each other's numbers at creation time.

### Step 6: Verify and report

Run `issue verify <n>` on the root (and spot-check a couple of leaves) to read back type, parent, `blockedBy`, `blocking`. Report the published tree: root URL, child URLs grouped by parent, and the edges set. If any edge the scope declared didn't resolve, stop and surface it — don't leave the tree half-wired.

---

## Notes

- **Delegation, not duplication.** The `issue` skill owns body authoring, the template, the 2×2 gate, and the GraphQL plumbing. This operation owns only the tree: derivation, ordering, and edge wiring. Don't re-implement issue authoring here.
- **`.issues/` drafts** for every node persist (git-ignored) as the audit trail — one `<number>-<type>-<slug>.md` per issue, with its review reports under `.peer/issue-<number>/`. Use `issue purge` to clear both when done.
- **Idempotency / re-runs.** If a scope was already partly published (e.g., a prior run failed at Level 3), prefer `gh issue list` to detect existing issues by title before re-creating; ask the user whether to resume or start fresh rather than producing duplicates.
- **Prerequisites** are the `issue` skill's: `issue` on PATH (`mise run install-issue`), `gh` authenticated, `peer` installed for the gate, `.issues/` git-ignored.
