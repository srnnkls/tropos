# Claude Reviewer Role

Reviewer persona for the native Claude subagent. Defines what to evaluate, not how to dispatch (see [harnesses/claude.md](../harnesses/claude.md) for dispatch).

---

## Review Focus

1. **Completeness:** Cross-reference with similar features in codebase
2. **Consistency:** Check against project terminology and patterns
3. **Feasibility:** Verify dependencies exist, APIs available
4. **Clarity:** Apply project documentation standards
5. **Design Depth:** Verify alternatives are substantiated, invariants testable, complexity claims have evidence (n/a when no design.md)
