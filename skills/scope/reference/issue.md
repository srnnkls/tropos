# Scope → Issue

The `issue` skill authors, gates, and publishes each issue; this operation only derives nodes, publishes parents first, and wires edges. Prerequisites: `issue` on PATH (Phora), `gh` authenticated, `peer` installed, `.issues/` git-ignored.

| Scope `issue_type` | Issue tree |
|---|---|
| Task | 1 Task issue |
| Feature | 1 Feature + *n* Task sub-issues |
| Initiative | 1 Initiative + *n* Features (phases) + *n×m* Task sub-issues |

### Step 1: Locate and load the scope

Locate per [Scope Location](../SKILL.md#scope-location), preferring the branch-associated scope when no name is given. Read `scope.md`, `tasks.yaml`, and `dependencies.yaml`/`design.md` if present. If `issue_type` is missing, ask via AskUserQuestion (`Initiative | Feature | Task`).

### Step 2: Derive the issue tree

Each node carries its source slice and source task id. Roots come from `scope.md` (Goal, Requirements, Acceptance Criteria). Task nodes come from `tasks.yaml` `tasks[]` (`content` / `files` / `depends_on`). Initiative Feature nodes come from `phases[]` (`dependencies.yaml` if present, else `tasks.yaml`), each holding the tasks its phase references. A task no phase references is an error: ask whether to attach it to a phase or skip it; never drop it silently.

Edges come only from the scope: parent = hierarchy; depends-on = task `depends_on` (Task→Task) and phase `depends_on` in `dependencies.yaml` (Feature→Feature).

### Step 3: Confirm tree and root parent

Render the planned tree: each node's type, title `<Module> — <summary>`, parent and depends-on edges; for large trees, the issue count `1 + n + Σmᵢ`. Then ask via AskUserQuestion:

- Root parent: pre-seed from `gh issue list --state open --search "type:<ParentType>" --json number,title --limit 20` (Initiative/Feature root under an Initiative; Task under a Feature) plus `No parent`. Never infer.
- Proceed gate, before any subagent publishes: `Proceed`, `Edit tree`, `Cancel`.

On re-runs after a partial publish, detect existing issues by title with `gh issue list` before creating any, and ask whether to resume or start fresh.

### Step 4: Author + publish, level by level

Publish top-down. Dispatch each level's nodes as parallel subagents in one message using the harness's delegation mechanism:

```
Level 1: root            → 1 subagent          → capture root number
Level 2: Features        → n subagents (∥)     → capture {phase → Feature number}
Level 3: Tasks           → Σmᵢ subagents (∥)   → capture {task id → Task number}
```

Feature scopes use Levels 1 and 3; Task scopes Level 1 only.

Each subagent gets fresh materialized repository orientation under [AGENTS.md](../../../instructions/AGENTS.md#tools-and-context) and this prompt:

> Invoke the `issue` skill to author and publish one issue. Do not ask for issue type or parent — they are fixed:
> - Type: `<Initiative|Feature|Task>`
> - Parent: `<resolved parent number, or none for the root>` — pass as `--parent <n>` at publish.
> - Do not set depends-on/blocks — sibling numbers aren't known yet; the orchestrator wires them after.
> - Title: `<Module> — <summary>` (em-dash).
> - Source material: <the node's scope slice — Goal/Requirements/Acceptance for the root; task `content`/`files` for a Task; phase name + member tasks for a Feature>.
> Run the full authoring workflow including the default reviewer gate. Return `<task-id>\t<number>\t<url>`.

Build each level's parent map from the previous level's returned numbers. If a subagent fails its gate or dies, report the node and stop before wiring edges.

### Step 5: Wire dependency edges

After all nodes publish, translate ids to issue numbers and apply each edge once:

```bash
issue depends-on <child#> <dep#,…>     # A depends on B  ⇒  A blockedBy B
```

Wire edges only here, never at publish.

### Step 6: Verify and report

Verify the root and a couple of leaves per [Verifying after submit](../../issue/SKILL.md#verifying-after-submit). Report the root URL, child URLs grouped by parent, and the edges.

`.issues/` drafts persist (git-ignored), one `<number>-<type>-<slug>.md` per issue, with review reports created through the canonical [`peer path` interface](../../peer/SKILL.md#report-layout--peer). `issue purge` clears both.
