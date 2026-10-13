# Design Document Quality Model

Every design choice states what was decided, its motivation (a constraint, insight, or observed problem), alternatives considered with rejection reasons, and the accepted tradeoffs.

| Section | Requirement |
|---|---|
| Problem | Concrete, observable, quantified with current/target metrics: "Per-file extraction makes 5 passes over the AST", not "The current system could be faster" |
| Core insight | One structural observation from which the subsequent decisions follow |
| Design | Each decision: decision → motivation → alternatives → tradeoffs |
| Alternatives | Only seriously considered ones, each with an explicit rejection rationale |
| Implementation | Phased; dependencies and verification per phase; each phase yields an observable result |
| Invariants | Linked to test cases |

Avoid assertion mode ("we chose X" without why X and why not Y) and laundry lists of independent decisions.
