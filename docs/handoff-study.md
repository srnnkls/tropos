# Session Handoff Study

Decided 2026-11-05.

## Summary

Tropos should add one manual skill that writes a short handoff artifact for a fresh session, invoked from Emacs with one harness-neutral sentence. The session's own model writes it; no cheaper summarizer, hook, or mod is involved. The skill is bookkeeping, not a new mechanism: every part has published prior art, and its value is that it fits Tropos's existing skill delivery, `.tropos/` state, and herdr panes on all four harnesses.

## Question

How should Tropos carry session state across compaction and session boundaries, so that the user can trigger it by hand from Emacs, herdr.el or limen, on Claude Code, Codex, Pi and OMP?

## Prior art

Compaction evidence:

- No compaction strategy consistently beats the session model summarizing itself. A Claude Haiku 4.5 summarizer cost GPT-5.4 0.59 → 0.43 and GPT-5.3-Codex 0.38 → 0.18 on PaperBench and left Opus 4.6 within noise; pointing the agent at a raw transcript dump was neutral to harmful [1].
- Losses compound per round more than with context fill: Claude Code `/compact` kept 53% of safety rules after one round and 10% after five; Terminal-Bench success fell 54% → 31% → 14% across successive compactions [11, 12].
- What gets lost: process instructions (35.9% dropped) and scope exclusions (36.8%) against feature requirements (6.2%) [1]; failed attempts, which lengthen trajectories 13–15% [4]; exact identifiers (16.0% kept by the best LLM, 79.1% by a mechanical index) [3].
- Structure helps where it forces constraints, failures and next steps in [7, 8]; length does not: a first-person handoff passed 86% against 82% for Claude Code's nine-section prompt [9]. Rules survive at summaries of 750 tokens or more and collapse at 300 [10].
- Anthropic recommends on-demand compaction "wherever it is available" [6].

Handoff designs converge on one shape: a manual command with a purpose, a file at a known path, and a one-line "read <path>, continue" for a fresh session [13–19]. Variants:

- Matt Pocock's `handoff`: five instructions, artifacts referenced by path, written to `$TMPDIR` [13].
- REMvisual `claude-handoff`: a Claude Code mod swaps the conversation for a validated handoff; 300–800-line floor, about 80k tokens to write [14].
- A "verify with: <command>" line per claim and an explicit not-verified section [15, 16].
- Routing: unrelated work → `/clear`; related → `/compact <focus>`; leaving the session → handoff [17].
- OMP `/handoff [focus]` writes Goal / Constraints / Progress / Decisions / Critical Context / Next Steps and commits it in place as a compaction entry; Pi ships `handoff.ts` as an installable example extension that seeds a new linked session [18, 19].
- ai-code-interface.el, an Emacs package, records git state, a HEAD baseline and validation commands, and seeds the next agent in two keystrokes over its own backend sessions [20].

Harness mechanics: Claude Code, Pi and OMP accept `/compact <focus>`; Codex `/compact` takes no inline focus, only a global `compact_prompt`. Every harness starts a session with an initial prompt (`claude|codex|pi|omp "<prompt>"`). No harness documents a compaction-model setting.

## Where Tropos stands

- No handoff skill. `continue` resumes only implement checkpoints (`scopes/<state>/<scope>/checkpoint.yaml`); `memex` returns full-transcript `resume_cmd`s.
- `auto_invoke: false` already renders a skill manual-only on all four harnesses (`disable-model-invocation: true`, `allow_implicit_invocation: false`).
- herdr.el's interactive `herdr-send`, `herdr-transient--prompt` and `herdr-transient--start` submit text and start agent panes; `herdr agent prompt --wait` "does not track turns" and returns a state, not output. limen has no send verb.
- "handoff" appears only as prose: the implement and test report YAML, herdr.el's live handoff, and `sweep`'s per-project pointer file `.tropos/sweep.md`. OMP and Pi ship a native `/handoff` command.
- The user writes handoffs by hand under `~/projects/.handoff/`.

## Design

A dynamic Henia library skill, `handoff`, read with `henia show` and never auto-invoked.

1. The user sends, from Emacs, `henia show handoff and follow it for: <purpose>`.
2. Rendering runs its `context_commands` live, so the anchors arrive as command output in every harness: `git branch --show-current`, `git rev-parse --short HEAD`, any `scopes/*/*/checkpoint.yaml`, and the newest existing `.tropos/handoff/*.md`. The model copies branch and HEAD into the artifact; status and diff are not stored.
3. The model writes five slots, imperative, 750–2,000 tokens:
   1. Goal and next concrete step, with its reason.
   2. Constraints and exclusions in the user's words, including every still-active constraint of the predecessor artifact.
   3. Decisions with reasons, including rejected options.
   4. Tried and failed, with the cause.
   5. Not verified: claims the successor re-checks, each with its command; first `git status --short` and `git diff --stat` against the recorded HEAD.
4. With an implement checkpoint present, it points at the checkpoint and names `continue` instead of restating waves.
5. It writes `.tropos/handoff/<UTC timestamp>.md` with one provenance line naming the predecessor artifact, if any.
6. The user starts a fresh pane in any harness with the constant line `Read the newest .tropos/handoff/*.md in full before any other action.`

Emacs cost: three actions, no path copying.

## Gains

- Resume cost of 750–2,000 tokens plus what the successor re-reads, against a ~10k-character summary plus up to 25k tokens of re-injected skill bodies on Claude Code, a 20k-token verbatim tail on Pi and OMP, or a full transcript through memex.
- Anchors and the successor's first checks come from commands; unverified claims are named with their checks.
- The categories compaction loses most (exclusions, process rules, failed attempts) have dedicated slots.
- One Emacs path on all four harnesses, with no spelling table and no per-harness code.
- Exactly one boundary per handoff, chosen by the user.

## Costs

- One skill with five rules: manual only, anchors, five slots, checkpoint deferral, path and resume line.
- Slots 1–4 remain model-written.
- Three Emacs actions instead of OMP's one.

## Positioning

The skill sits beside native compaction. In-session `/compact <focus>` stays the tool for related work in the same session; the skill is for work that leaves it. OMP's in-place `/handoff` and Pi's extension remain available and are not routed around.

## Decisions

| # | Decision | Goals | Recommendation | Rejected |
|---|---|---|---|---|
| D1 | Add the skill | G2, G3 | Add it as designed | No change: native compaction plus hand-written files |
| D2 | Name | G4 | `handoff`: no Tropos skill, slot or command owns it; the trigger is `henia show`, so OMP and Pi `/handoff` do not collide | `relay`: a second word for the same thing |
| D3 | Invocation | G1, G3, G5 | Harness-neutral `henia show handoff and follow it for: <purpose>`, with anchors as dynamic context | Per-harness slash commands (`/x`, `$x`, `/skill:x`) needing a spelling table |
| D4 | Resume line | G1 | Constant "newest artifact" line | Printed per-artifact path copied by hand |
| D5 | Summarizer | G3, G6 | The session's own model | A Haiku or other external summarizer |
| D6 | Emacs one-step chain | G1, G6 | None; three actions with existing commands | A chained herdr.el command: no reliable completion signal |
| D7 | OMP and Pi native `/handoff` | G4, G6 | No deferral rule | A per-harness routing table |
| D8 | In-place swap | G5, G6 | None | Claude Code mod on early-access, undocumented returns |

## Open questions

- `sweep` writes a per-project pointer handoff with branch, scope, session `resume_cmd` and next step; the session handoff overlaps it. Either `sweep` cites the newest session handoff per item, or both share one section list.
- Does the harness-neutral sentence trigger the skill reliably on each harness? One manual run per harness settles it.
- Concurrent sessions in one repo race on "newest artifact". A herdr.el start-with-initial-prompt command would allow per-artifact paths; it belongs to herdr.el.
- Cross-repo handoffs, such as those under `~/projects/.handoff/`, are not served by a repo-local path.
- Auto-compaction during the skill can still produce an artifact from compacted context; the skill cannot detect it.
- Slots 2 and 4 can quote secrets; `.tropos/` is gitignored but not redacted.
- Fresh successor against in-place `/compact` with the same five slots is unmeasured. Falsifier: one task, both arms, successor turns until the first correct action.

## Sources

1. Benchmarks Are Surprisingly Compaction-Friendly, arXiv 2610.31778 — https://arxiv.org/abs/2610.31778
2. CompInt, arXiv 2608.11242 — https://arxiv.org/abs/2608.11242
3. Context Compaction Theory, arXiv 2608.01326 — https://arxiv.org/abs/2608.01326
4. JetBrains, The Complexity Trap, arXiv 2508.21433 — https://arxiv.org/abs/2508.21433
5. Anthropic, Effective context engineering for AI agents — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
6. Anthropic, compaction and context editing — https://platform.claude.com/docs/en/build-with-claude/context-editing
7. Gemini CLI chat compression and probe turn, google-gemini/gemini-cli source
8. Factory, Evaluating context compression — https://factory.com/news/evaluating-compression
9. Compact-Bench, arXiv 2610.31710 — https://arxiv.org/abs/2610.31710
10. ARCBench, arXiv 2611.03223 — https://arxiv.org/abs/2611.03223
11. The Compaction Cliff, arXiv 2608.22752 — https://arxiv.org/abs/2608.22752
12. Meta-Task Terminal-Bench analysis, arXiv 2607.27929 — https://arxiv.org/abs/2607.27929
13. mattpocock/skills, handoff — https://github.com/mattpocock/skills
14. REMvisual/claude-handoff — https://github.com/REMvisual/claude-handoff
15. alexknowshtml/claude-auto-handoff — https://github.com/alexknowshtml/claude-auto-handoff
16. nathanonn handoff-doc — https://github.com/nathanonn/agent-skills/blob/HEAD/skills/handoff-doc/SKILL.md
17. melodic-software/claude-code-plugins #5808 — https://github.com/melodic-software/claude-code-plugins/issues/5808
18. oh-my-pi handoff pipeline — https://github.com/can1357/oh-my-pi/blob/main/docs/handoff-generation-pipeline.md
19. Pi handoff extension — https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/extensions/handoff.ts
20. tninja/ai-code-interface.el — https://github.com/tninja/ai-code-interface.el
21. Amp, Handoff — https://ampcode.com/news/handoff
