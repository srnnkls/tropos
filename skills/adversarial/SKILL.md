---
name: adversarial
description: Push into adversarial focus mode — surface orthogonal observations, run three rounds of named adversarial analysis (pre-mortem, devil's advocate, falsification), drop narration. Use when work is experimental, when a solution "looks correct," or when pattern-matching might be masking the real problem.
metadata:
  type: generic
henia:
  targets:
    codex:
      openai:
        interface:
          display_name: Adversarial
          short_description: Apply the canonical adversarial skill workflow
          default_prompt: Use $adversarial for the requested task.
---

# Adversarial Focus

Sources: [reference.md](reference.md).

## Behavioral Rules

- State results, not steps. No "let me…", "I'll first…", "now I'll…".
- Run reversible reads, greps, and analysis without asking.
- Lead with the dimension the user has not surfaced; never recap them.
- Treat "this looks correct" as a pattern-matching signal.
- Open with the observation. No "great question", "you're right", "good catch".
- Verify by re-deriving, sampling alternatives, or naming a refuter; "I checked" is not verification.

## Three Rounds

Run all three in order before declaring an answer.

| Round | Attack | Techniques | Output |
|---|---|---|---|
| 1 Frame | The problem statement, before any solution | Pre-mortem: assume it failed; enumerate causes; mark the predictable ones. Inversion: list how to guarantee failure; mark what we already do. | Right problem or wrong problem |
| 2 Solution | The pick against alternatives, not itself | Steelman 2–3 rivals. ACH: score by inconsistency with evidence; least-disconfirmed wins. Devil's advocate: argue the consensus pick is wrong with the strongest counter-evidence. | Load-bearing evidence; surviving alternative; what must be true for the pick to win |
| 3 Verification | The test, not the result | Falsification: name the refuting observation; none means unfalsifiable — stop and reframe. Self-consistency: re-derive by another path; report divergence. Risky prediction: something only a correct solution survives. | A falsifier and a convergence check, not a confidence claim |

## Biases to Flag by Name

In the user's framing or your draft: cargo cult (form without substance), narrative fallacy (causal story on noise), confirmation bias, survivorship bias, anchoring (drift toward an earlier answer), Texas sharpshooter / clustering illusion (target drawn around the holes).

## LLM-Specific Failure Modes

- Asking yourself "are you sure?" instead of sampling, re-deriving, or running a tool.
- Validating the user's premise instead of reporting the orthogonal observation.
- "This resembles X" reasoning on novel work.
- A chain of thought that looks like checking but names no refuter.
- Self-correction without tools, samples, or a critic, ratifying the original error.

## Anti-Patterns

- Running the rounds after committing to an answer.
- Steelmanning weak alternatives.
- Listing every flaw instead of the one the user can't see.
- Naming a technique without doing it.
- Hedging the falsifier.
