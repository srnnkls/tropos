---
name: rsb
description: Run a research → synthesis → breakthrough pass on a stuck design question — parallel primary-source research tracks, a synthesis only their combination allows, a bounded novelty check, independent adversarial review, owner decisions, and amendments. Use for "rsb", "research, synthesis, breakthrough", "research track on X", or when a design point keeps relocating edge cases.
---

# Research, Synthesis, Breakthrough

:::head
Notes go to `.tropos/rsb/<Topic>/`; nothing tracked changes before phase 7.

| # | Phase | Output |
|---|---|---|
| 1 | Frame | `0-brief.md` |
| 2 | Research | `1-…md` … `N-…md` |
| 3 | Synthesis | `S-synthesis.md` |
| 4 | Novelty | `V-novelty.md` |
| 5 | Review | `R1-soundness.md`, `R2-goals.md` |
| 6 | Decide | `docs/<topic>-study.md` |
| 7 | Amend | one commit: study + doc diffs |

## 1 Frame

Brief: the project's numbered goals (from its goals doc, else restated and confirmed with the user), the question, the obstruction that triggered it, the user's pain points verbatim, and the metric each goal is measured in.

## 2 Research

Launch 3–6 parallel subagent tracks with the brief, each with a search budget. One track inventories the project itself; the others cover prior art, theory, evidence or incidents, lineage. Each file:

- sources marked (read) when fetched in the track, (listing) when known from a snippet; verbatim quotes; no claims from memory;
- per source: takeaway, findings, inferences, gaps;
- ends with implications mapped to pain points.

## 3 Synthesis

Score candidates × goals against the current design as a baseline, in the brief's metrics. A breakthrough candidate:

- resolves a named tension instead of trading it off;
- needs findings from ≥2 tracks;
- reuses existing mechanism or obligations;
- reduces the rule count (state before → after) or derives existing rules from one principle.

None qualifies: say so; "no change" is a valid result. Close edge cases or name them; never relocate them.

## 4 Novelty

List claims C1..Cn plus the combination. Within a bounded search, give each a verdict (published / partial / not found) with the closest prior art matched by mechanism. Narrow every claim to what survives.

## 5 Review

Separate reviewers, never the synthesis author: soundness and goals, each running $adversarial. Each finding: severity, counterexample, broken rule, minimal fix. Fix, then re-review once. Keep the files.

## 6 Decide

Study: summary, question, prior art, where the project stands, design, gains, costs, positioning, numbered decisions mapped to goals with a recommendation and the rejected alternative, open questions, sources. No track references or process wording. The user decides; when delegated, decide by the goals.

## 7 Amend

After the decisions: mark the study "Decided <date>", apply diffs to the affected docs, commit both together per $git.

## Stop

- Off-goal drift: park it as an open question.
- Research that yields no synthesis: report the obstruction; do not pad with parallels.
:::
