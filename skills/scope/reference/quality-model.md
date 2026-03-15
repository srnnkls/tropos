# Design Document Quality Model

Patterns extracted from exemplary design documents (gestalt/sira/nmnm). Use as a thinking pattern, not a fill-in-the-blank template.

---

## The Iron Rule

**No unmotivated decisions.** Every design choice must state:
1. What was decided
2. Why (the motivation — a constraint, insight, or observed problem)
3. What alternatives were considered and why rejected
4. What tradeoffs are accepted

---

## Quality Pattern

### 1. Problem — Concrete, Quantified

Lead with observable reality, not abstract framing.

**Good:** "Per-file extraction makes 5 passes over the AST" (gestalt)
**Good:** "Processor FLOPS grew ~1,000,000% since 1996; DRAM bandwidth only ~100%" (nmnm)
**Good:** "Existing KV stores carry complexity from one architectural decision: maintaining online order" (sira)

**Bad:** "The current system could be faster"
**Bad:** "We need a better architecture"

Ground all subsequent decisions in observable reality to prevent abstract over-design.

### 2. Core Insight — Structural Observation That Cascades

Find the one structural observation that makes all subsequent decisions flow.

**Good:** "Order is a batch property, not an online property" (sira)
**Good:** "Sequential composition routes around the memory wall" (nmnm)
**Good:** "All five extraction tasks can be done in a single cursor walk" (gestalt)

The insight prevents the design from being a laundry list of independent choices — decisions flow from one observation.

### 3. Design — Consequences of the Insight

Each decision section follows: decision → motivation → alternatives → tradeoffs.

**Pattern from nmnm:**
> "Split owns both grain and morsel shape. The Split trait declares a single Grain dimension. Both coarse dispatch splitting and fine morsel splitting use the same trait — the only difference is the grain value. The alternative — separate traits for dispatch-level and morsel-level splitting — would duplicate logic and fragment the abstraction."

**Pattern from sira:**
> "Why a new engine: Existing embedded KV stores carry complexity from maintaining online order. Every insert updates an ordered index — B-tree page splits, skip-list rebalancing, LSM compaction heuristics."

This structure makes the reasoning chain auditable — anyone reading can verify whether the logic holds.

### 4. Why Not Alternatives — Comparative Analysis

Not exhaustive — only alternatives seriously considered, with explicit rejection rationale.

**Pattern from nmnm:**
> | System | Why it doesn't enable sequential composition |
> | Rayon | Recursive task splitting via join(). No control over morsel size, cache residency... |
> | Tokio spawn_blocking | Designed for IO-bound work. No work-stealing deques, no data locality... |

Including rejections prevents future revisiting of already-explored dead ends.

### 5. Implementation Approach — Phased with Verification

Clear dependencies and verification per phase. Each phase should produce observable results.

---

## Anti-Patterns

| Anti-pattern | What to do instead |
|---|---|
| Assertion mode ("we chose X") | State why X and why not Y |
| Laundry list of independent decisions | Find the insight that connects them |
| Abstract problem statement | Quantify with current/target metrics |
| Exhaustive alternatives catalog | Only seriously considered ones with rejection rationale |
| Design without verification | Link invariants to test cases |

---

## Why Chain-of-Thought Matters for LLM Design

Without explicit motivation requirements, LLMs default to assertion mode — "we chose X" without explaining why. Requiring the motivation chain (decision → why → alternatives → tradeoffs) forces the reasoning to be externalized and verifiable. The human can then validate the reasoning, not just the conclusion.
