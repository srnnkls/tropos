# slint

*Semantic compliance, compiled.*

A compiler for human-written engineering rules, with a local runtime that semantically lints code
and text against the compiled policy artifact. Style guides, ADRs, specs and policies go in; a
versioned rule artifact comes out; `slint check` runs it against files, diffs or documents and emits
diagnostics with evidence and provenance.

Status: prototype. Python 3.12, standard library only at runtime. The decision model is
[Jev](https://docs.typesafe.ai/introduction), TypeSafe's System One model, reached over plain HTTPS.

## Why this shape

The naive semantic linter asks a model about every (rule, chunk) pair. With `m` rules and `n`
chunks that is `m · n` model judgments, and every guide change re-evaluates the whole source.

slint collapses that matrix in three ways, cheapest first:

| Evaluator | What decides it | Cost at check time |
|---|---|---|
| `static` | a native detector over the AST or the text | zero model calls |
| `feature` | a predicate over the semantic IR (`k` fixed features per chunk, extracted once, cached) | `O(n)` calls, shared by every rule |
| `judge` | Jev asked directly, all judges routed to a chunk batched into one call | `O(n')` calls, `n'` = chunks with routed judges |

Routing keeps the pair matrix sparse: heading rules only see headings, Python rules never see
Markdown, opening-paragraph rules see one chunk per document. Rules that compile to the same check
are merged into one rule with several sources. Changing the guide never forces re-extraction when
the rules only need features already in the vocabulary.

```
compile phase                              check phase
guides / specs / ADRs / policies           source / diff / prose
        │                                          │
        ▼                                          ▼
 candidate sentences (deterministic)          chunks (headings, paragraphs, lists,
        │                                       code blocks, functions, classes)
        ▼                                          │
 classification (Jev fan-out, or keywords)         ├── static  ── native detectors
        │                                          ├── feature ── semantic IR ── predicates
        ▼                                          └── judge   ── one batched Jev call per chunk
 .slint/rules.json + manifest.json                        │
   id · modality · scope · domain · language              ▼
   evaluator · sources (file:line §section)        text / JSON / SARIF diagnostics
```

## Usage

```bash
cd prototypes/slint
uv sync

# compile guides into an artifact
uv run slint compile examples/guides --prefix EX -o .slint
uv run slint compile ~/.cache/tropos/loqui/languages/python --prefix LOQ-PY -o .slint-loqui

# check sources against it
uv run slint check examples/sources
uv run slint check src/ --diff HEAD~1
uv run slint check README.md --format sarif > results.sarif

# inspect
uv run slint rules            # every compiled rule, its evaluator and where it came from
uv run slint features doc.md  # dump the semantic IR per chunk
```

Set `TYPESAFE_API_KEY` to use Jev for compilation, feature extraction and judge rules. Without a
key, or with `--offline`, slint runs the native detectors plus a keyword compiler and a heuristic
feature extractor. Heuristic feature findings are capped at `warning` and labelled
`feature/heuristic`; judge rules are counted and skipped. `--trace` prints every model exchange as
JSON lines on stderr.

Exit codes: `0` clean, `1` findings at or above `--fail-on` (default `error`), `2` usage or
configuration error.

## What a finding looks like

```
examples/sources/client.py:28: error EX-001 [static] Outbound HTTP requests MUST configure an explicit timeout.
    requests.get() without an explicit timeout
    > response = requests.get(self.url(f"/invoices/{invoice_id}"), headers=headers)
    source: examples/guides/networking-spec.md:11 §Networking spec > Timeouts
```

Every finding names the rule that fired, the span, the evidence the evaluator used, the evaluator
kind and confidence, and the sentence in the guide the rule was compiled from.

## The compiled artifact

`slint compile` writes two files:

- `rules.json`: one `Requirement` per rule with `id`, `statement`, `modality` (MUST, MUST_NOT,
  SHOULD, SHOULD_NOT), `severity`, `scope` (any, heading, opening, closing, list, body, code),
  `domain`, `language`, an `evaluator` and `sources` with file, heading path, line span and the
  original text.
- `manifest.json`: compiler version, feature schema version, model fingerprint, source digests and
  evaluator counts. The runtime refuses an artifact compiled against a different feature schema.

The artifact is meant to be committed, or produced in a dedicated policy-update job. CI needs the
binary and the artifact, nothing else, and only calls the model where a rule genuinely needs it.

## The semantic IR

`src/slint/features.py` is the vocabulary. Each feature is a Jev question with a fixed answer type
and a polarity:

- prose: `purpose`, `tone`, `verbosity`, `hedging`, `directness`, `audience_level`,
  `contains_repetition`, `contains_uncertain_claim`, `contains_unsupported_claim`, `uses_jargon`,
  `passive_voice_heavy`
- code: `code_purpose`, `makes_network_call`, `sets_explicit_timeout`, `swallows_errors`,
  `rewraps_without_context`, `logs_sensitive_data`, `mutates_global_state`,
  `comments_restate_code`, `names_are_descriptive`, `class_is_namespace`, `untyped_data_in_core`,
  `duplicates_dependency_validation`

Polarity is what makes rule compilation robust: a guide never wants more hedging, so any rule
about hedging is violated when `hedging` is high regardless of how the sentence is phrased.
"Do not hedge unless the claim is genuinely uncertain" compiles to
`hedging > 1.5 and contains_uncertain_claim is False`.

## Compiling loqui

[loqui](https://github.com/srnnkls/loqui) is a good corpus: opinionated, normative, mixed static
and semantic rules, with `paths:` front matter that gives the language. Offline, the Python guides
compile to 145 rules: 15 static, 7 feature, 123 judge. Against `examples/sources/client.py` the
static rules alone report ten errors: behavioral inheritance, `@staticmethod`, a mutable default,
a request without timeout, blocking I/O in an async function, `dict[str, Any]` in core logic,
root-logger configuration, a section divider and a missing `from __future__ import annotations`.

With Jev, the compiler's `is_requirement` gate drops the non-rules the keyword pass keeps
("Use pattern matching when:" style lead-ins are already filtered deterministically), and the
judge rules become evaluable.

## Layout

```
src/slint/
  jev.py         Jev client: Noul/Choice/Score questions, typed answers, scripted and recording backends
  chunks.py      Markdown and Python chunking with kind, position and heading path
  features.py    the semantic IR vocabulary and polarity
  detectors.py   native detectors (Python AST, Markdown text)
  rules.py       Requirement, evaluators, artifact save/load with typed parsing
  compiler.py    candidate extraction, Jev or keyword classification, merging, ids
  extraction.py  IR extraction with content cache and heuristic fallback
  evaluation.py  routing, static/feature/judge evaluation, stats
  reporting.py   text, JSON, SARIF
  diff.py        restrict a check to lines changed since a revision
  cli.py         compile · check · rules · features
tests/           pytest, module-level functions, protocol-based fakes (ScriptedJev)
examples/        two guides and two deliberately non-compliant sources
```

Development: `uv run pytest`, `uv run ruff check src tests`, `uv run pyright src tests`.

## Relationship to fas

[fas](https://github.com/srnnkls/fas) evaluates AI-agent hook events against CUE patterns by
subsumption and emits a gate decision. slint shares its engineering philosophy but not its
primitive, and the two should stay separate tools:

- Same shape: parse once into facts, evaluate many rules over them; explicit compile/load versus
  runtime split; findings that localize to a span and cite the rule; text, JSON and SARIF output;
  no agent loop, no framework.
- Different primitive: fas asks "does this CUE pattern subsume this value?", a closed-world,
  deterministic check over one event. slint asks "does this region satisfy this normative
  sentence?", a probabilistic judgment over a corpus, with confidence thresholds and provenance
  back to prose. fas's output algebra is a gate (allow, deny, ask, inject, modify); slint's is a
  diagnostic (severity, evidence, confidence, source).
- Narrow bridges worth considering later, none of them architecture: (1) slint's compiler could
  draft fas rules from policy prose for requirements about agent tool calls, since fas rules are
  hand-authored CUE today and `fas vet` can validate the draft; (2) fas's input schema already has
  a `signals` extension point, so a semantic signal computed by Jev could feed a CUE pattern
  without changing fas's decision model; (3) slint should adopt fas's compile-time strictness and
  its `explain` command, both of which this prototype lacks.
