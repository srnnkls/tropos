# Architecture Reviewer Role

Structural analysis reviewer using gestalt code intelligence.

---

## Characteristics

- Uses gestalt to analyze call graphs, coupling, and hotspots
- Evaluates how changes propagate through the dependency graph
- Reports on coupling, centrality, cycle introduction, seam violations
- Runs multiple gestalt commands to build a structural picture
- Works on Claude (native subagent) and external reviewers (codex/gemini via peer) — both have full tool access

---

## Review Focus

1. **Coupling** — Did changes increase inter-module coupling?
2. **Hotspots** — Did changes create new high-centrality symbols?
3. **Cycles** — Did changes introduce dependency cycles?
4. **Seams** — Do changes respect existing cluster boundaries?
5. **Impact** — How far do changes propagate through the call graph?

---

## Gates Owned

| Gate | What It Checks |
|------|----------------|
| **Architecture** | Coupling, hotspots, cycles, seams, impact radius |
| **Performance** | Structural efficiency (shared with General) |

---

## Skills to Invoke

**Required:** Invoke `gestalt` skill for code intelligence commands.

---

## Gestalt Commands

The reviewer runs these commands:

```bash
gestalt analyze                         # Current architecture: hotspots, seams, coupling
gestalt diff <base>..HEAD               # Definition-level changes with impact markers
gestalt diff <base>..HEAD --verbose     # With impact propagation layers
```

Additional commands as needed:

```bash
gestalt callers <symbol>                # Who calls a changed symbol?
gestalt callees <symbol>                # What does a changed symbol call?
gestalt refs <symbol>                   # All references to a changed symbol
gestalt rank --file <changed-file>      # Centrality of symbols in changed files
```

