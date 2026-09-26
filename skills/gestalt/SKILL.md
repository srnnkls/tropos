---
name: gestalt
description: |
  Query code intelligence with gestalt. Use when finding callers/callees, tracing references, running CozoScript queries, or generating repo maps.
metadata:
  type: generic
henia:
  targets:
    codex:
      openai:
        interface:
          display_name: Gestalt
          short_description: Apply the canonical gestalt skill workflow
          default_prompt: Use $gestalt for the requested task.
---

<!-- Generated from skills/gestalt/SKILL.md by henia build; edit the canonical source. -->

# gestalt

Rust binary, embedded CozoDB, tree-sitter indexing with optional SCIP overlay. Supports Rust, Python, Go, TypeScript/JavaScript. Auto-indexes on first run.

## Auto-Detect Rules

Parse `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| `review [target]` | Structural review | Read and follow `operations/review.md` |
| No argument / other | Query mode | Continue with gestalt commands below |

## Subagent orientation

```bash
gestalt map                             # Where do I look?
gestalt analyze                         # What are the hotspots, seams, coupling?
```

Then use `callers`/`callees`/`refs` to drill into specific symbols as needed. Names copied from map output work as query arguments, and the `(lines a-b)` these queries report is the range to read.

Test code (`tests/` and `test/` directories, `tests.rs`, `*_test`/`*_tests` files, `.spec.*`/`.test.*` files) is hidden from `map`, `diff`, `rank` and `analyze` unless `--include-tests` is given.

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

## Diff and history

```bash
gestalt diff <base> [target]            # Definition-level changes between revisions
gestalt diff main..HEAD                 # Changed symbols with impact markers
gestalt diff main...HEAD                # From the merge base, as in git diff
gestalt diff main..HEAD --format json   # Machine-readable change set
gestalt diff main..HEAD --verbose       # Impact propagation layers
gestalt diff main..HEAD --depth 3       # Custom impact depth (implies --verbose)
gestalt diff main..HEAD --include-tests # Include test symbols

gestalt blame <symbol>                  # Git blame for symbol's definition
gestalt blame <symbol> --format json    # Machine-readable

gestalt log <symbol>                    # Git log for symbol's line range
gestalt log <symbol> --limit 5          # Limit entries
gestalt log <symbol> --format json      # Machine-readable
```

`diff` and `renames` exit 0 on success; `--exit-code` makes a non-empty result exit 1. Exit 2 is an error.

Output markers for diff:
- `↑N` — N sites reference this symbol
- `⊤ root` — entry point: calls others, not called by others
- `⊥ leaf` — foundation: called by others, calls nothing
- `⇔` — bridge: high betweenness centrality

## Structural review

See [operations/review.md](operations/review.md).

## Call graph

```bash
gestalt callers <symbol>                # Who calls this?
gestalt callers collect_entries         # → mtime_hash [function] src/mtime.rs:37 (lines 29-46)
gestalt callers helper --file src/db.rs # Filter to file

gestalt callees <symbol>                # What does this call?
gestalt callees find_project_root       # → find_markers_at [function] src/project.rs:73 (lines 98-107)

gestalt refs <symbol>                   # All references with location
gestalt refs Config                     # → src/main.rs:42:10 (from: run_command)
```

Output format:
- `callers`/`callees`: `name [kind] file:line (lines a-b)`. `file:line` is the reference; `(lines a-b)` is the named definition's full extent, doc comments and attributes included. Read that range directly instead of grepping for the definition.
- `refs`: `file:line:col (from: symbol_name)` or `(top-level)`
- JSON output carries the extent as `span: {start_line, end_line}`, `null` when unrecorded.

Symbol arguments accept any name gestalt prints: a bare name, `Owner.member` or `Owner::member`, map labels such as `src/db.rs::Database` or `crate::db::Database`, a re-export label with its `(def file)`, and a `:line` suffix.

Every answer is explicit:
- `no callers of 'X'` is a real result, not a failed lookup; do not grep to double-check it.
- `'X' not found` comes with close names when any exist.
- An ambiguous name lists each match as `file::name:line`; rerun with the one you mean.

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

[CozoScript](https://docs.cozodb.org/en/latest/queries.html) (Datalog dialect). Tables: `symbol`, `reference`, `span`, `reexport`.

**symbol**: `scip_symbol`, `name`, `kind`, `file`, `line`, `end_line`, `col`, `end_col`, `is_external` (`line`..`end_line` cover the name only)
**reference**: `from_symbol`, `to_symbol`, `file`, `line`, `col`
**span**: `file`, `line`, `name`, `start_line`, `end_line` (a definition's full extent, keyed like `symbol`)

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
