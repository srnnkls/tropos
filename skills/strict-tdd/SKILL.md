---
name: strict-tdd
description: Oracle-first, smallest-falsifier test design at the code's public seam. The default test.approach for task domains without their own provider.
metadata:
  type: generic
henia:
  provides:
    test.approach:
  targets:
    codex:
      openai:
        interface:
          display_name: Strict TDD
          short_description: Design oracle-first minimal falsifiers
          default_prompt: Use $strict-tdd to design the tests for the requested behavior.
---

# Strict TDD

1. Derive the oracle from the requirement before reading implementation bodies.
2. Read existing tests and the target public interface for conventions and the test seam. Read implementation only as far as needed to locate that seam; never copy its behavior into the oracle.
3. Write the smallest representative falsifier set.
