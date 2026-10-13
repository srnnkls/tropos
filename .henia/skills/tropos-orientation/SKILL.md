---
name: tropos-orientation
description: Orientation for working on the Tropos skill library itself. Use before changing Tropos skills, agents, instructions, or rules.
henia:
  provides:
    code.orientation: {priority: fallback}
---

# Tropos Orientation

Skills, agents, and instructions are Markdown; code lives under `skills/*/scripts/`.

```bash
henia ls                                    # skills and descriptions
henia show <skill> --head                   # a skill's routes and contents
henia query --canonical '<pattern>'         # sections, links, slots, similar text; see henia query --grammar
henia slots --explain <slot>                # slot owner, providers, consumers
```

Run `gestalt map skills/<skill>/scripts` for script code; `rg` for exact text after.
