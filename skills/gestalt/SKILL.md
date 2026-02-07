---
name: gestalt
description: |
  Query code intelligence with gestalt. Use when finding callers/callees, tracing references, running CozoScript queries, or generating repo maps.
---

# gestalt

Rust binary, embedded CozoDB, tree-sitter indexing with optional SCIP overlay. Supports Rust, Python, Go, TypeScript/JavaScript. Auto-indexes on first run.

## Subagent orientation

All subagents (implementers, testers, reviewers) should orient before starting work:

```bash
gestalt map                             # Where do I look?
gestalt analyze                         # What are the hotspots, seams, coupling?
```

Then use `callers`/`callees`/`refs` to drill into specific symbols as needed.

## map vs analyze

| | `gestalt map` | `gestalt analyze` |
|---|---|---|
| Purpose | Navigation | Understanding |
| Question | "Where do I look?" | "Why is it structured this way?" |
| Audience | Agents, quick orientation | Humans refactoring, debugging architecture |
| Output | Module signatures with symbols | Cluster metrics, seams, hotspots, coupling |

### map — the territory

```bash
gestalt map src/                        # Enriched map (auto-indexes)
gestalt map src/ --tokens 512           # Token budget
gestalt map --top 20                    # Top-20 ranked symbols
gestalt map --verbose                   # Per-cluster detail
```

```
∴ clusters(5): ...
∴ depth(4): ⊤ command_cache_migration → ... → tags ⊥
∴ bridges(5): extract_tags → ...
∴ fan-in(3): ...
∴ fan-out(3): ...

./src/tree/parser.rs:
   72│pub fn parse ...
```

Feed to an agent or skim when starting work.

### analyze — why the territory looks that way

```bash
gestalt analyze                         # Full analysis
gestalt analyze --top 50                # More symbols
gestalt analyze --file src/db.rs        # Single file
gestalt analyze --kind function         # Filter by kind
gestalt analyze --format json           # Machine-readable
gestalt analyze --no-clusters           # Hide clusters
gestalt analyze --no-cycles             # Hide cycles
gestalt analyze --no-entry-points       # Hide entry points
```

```
∴ hotspots(5): find_project_root (↑21 ↓2), ...
∴ seams(4): extract (3 clusters), fingerprint (2 clusters), ...
∴ links(1): [fingerprint, locking, manifest] → [fingerprint, project] (1 refs)
∴ graph: 417 nodes, 723 edges, 13 clusters, density 0.004
∴ singletons(6): ...

[extract, parser] (rank: 0.0474, size: 2, coupling: 0.08) †extract
./src/tree/parser.rs:
    72 │ function parse ↑38 ↓1
```

Study when the graph reveals a problem — refactoring targets, coupling hotspots, architectural seams.

## Call graph

```bash
gestalt callers <symbol>                # Who calls this?
gestalt callers parse                   # → parse [function] src/tree/parser.rs:78
gestalt callers helper --file src/db.rs # Filter to file

gestalt callees <symbol>                # What does this call?
gestalt callees mtime_hash              # → collect_entries [function] src/mtime.rs:44

gestalt refs <symbol>                   # All references with location
gestalt refs Config                     # → src/main.rs:42:10 (from: run_command)
```

Output format:
- `callers`/`callees`: `name [kind] file:line`
- `refs`: `file:line:col (from: symbol_name)` or `(top-level)`

## Other commands

| Command | Purpose |
|---------|---------|
| `gestalt rank` | Rank symbols by PageRank + degree centrality |
| `gestalt rank --format tree` | Same ranking, tree output |
| `gestalt rank --file src/db.rs --kind function` | Filter by file/kind |
| `gestalt index [paths]` | Index with tree-sitter |
| `gestalt index src/ --scip index.scip` | Index + SCIP overlay |
| `gestalt query '<datalog>'` | Raw CozoScript query |
| `gestalt cache list` | Show indexed projects |
| `gestalt cache clear` | Delete all cache |
| `gestalt cache prune` | Remove stale entries |

## Output markers

| Marker | Meaning |
|--------|---------|
| `↑N ↓M` | In-degree / out-degree |
| `⇔` | Bridge node (top-10% betweenness centrality) |
| `⇄` | Cycle member (SCC with >1 symbol) |
| `†stem` | Seam (file stem appears in multiple clusters) |

## SCIP overlay

Precise cross-crate references. Generate the index, then overlay:

```bash
gestalt index src/ --scip index.scip
```

| Language | Indexer | Install |
|----------|---------|---------|
| Rust | rust-analyzer | `rustup component add rust-analyzer` |
| Go | scip-go | `go install github.com/sourcegraph/scip-go/cmd/scip-go@latest` |
| Python | scip-python | `npm i -g @sourcegraph/scip-python` |
| TypeScript | scip-typescript | `npm i -g @sourcegraph/scip-typescript` |

## CozoScript queries

[CozoScript](https://docs.cozodb.org/en/latest/queries.html) (Datalog dialect). Tables: `symbol`, `reference`.

**symbol**: `scip_symbol`, `name`, `kind`, `file`, `line`, `end_line`, `col`, `end_col`, `is_external`
**reference**: `from_symbol`, `to_symbol`, `file`, `line`, `col`

```bash
# Schema introspection
gestalt query '::relations'             # List tables
gestalt query '::columns symbol'        # Columns for a table

# Functions in a file
gestalt query '?[name, line] := *symbol{name, kind, file, line}, kind = "function", file = "src/main.rs"'

# Call graph
gestalt query '?[caller, callee] := *reference{from_symbol: cs, to_symbol: cs2}, *symbol{scip_symbol: cs, name: caller}, *symbol{scip_symbol: cs2, name: callee}'

# Unused functions
gestalt query '
  called[sym] := *reference{to_symbol: sym}
  ?[name, file, line] := *symbol{scip_symbol: sym, name, kind, file, line}, kind = "function", not called[sym]
'
```

## Troubleshooting

- **Empty results**: Run `gestalt index .` or `gestalt map` to populate the database.
- **Stale data**: `gestalt cache clear` then re-index.
- **Query syntax**: [CozoScript docs](https://docs.cozodb.org/en/latest/queries.html).
