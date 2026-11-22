---
name: scrut
description: Write self-contained, readable scrut CLI tests in Markdown. Use when adding or reviewing scrut tests or other CLI snapshot tests.
metadata:
  type: domain
henia:
  targets:
    codex:
      openai:
        interface:
          display_name: Scrut
          short_description: Write self-contained scrut CLI tests
          default_prompt: Use $scrut to write the CLI test.
---

# Scrut

A scrut test is a Markdown document a reviewer reads top to bottom: prose states the behavior, each block shows the exact input and the expected output.

- Build every input inline, in the block that uses it: heredocs for files, plain `git`/`mkdir` for state. No data files beside the test.
- An external fixture may only make the environment clean, stable and reproducible (isolated `HOME`, pinned config, fixed clock); it carries no test data.
- Call the tool under test directly. No wrapper or checker script between the command and its output; assert on the real stdout, stderr and exit code (`[1]`).
- One behavior per block, its setup kept short enough to read with it. Prose between blocks says what the next block proves.
- Expected output is literal; reach for `(glob)` or `(regex)` only on volatile parts such as paths, times and versions.
- Each file runs in its own temporary working directory; write there, never under `$TESTDIR`.

```scrut
$ mkdir pkg && cat > pkg/a.toml <<'TOML'
> name = "a"
> TOML
$ tool check pkg
pkg/a.toml: OK
```

Run one file with `scrut test <file>`; `scrut update <file>` only after reading the diff it proposes.
