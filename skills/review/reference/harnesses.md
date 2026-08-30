# Review Harnesses

Review-specific prompt materialization, concurrent fan-out, and partial-result semantics. Registry and dispatch mechanics live in the canonical [peer routing contract](../../peer/reference/routing.md); external harness flags and failures live in the [peer skill](../../peer/SKILL.md).

## Materialization

Build one self-contained prompt per role before dispatch. Embed:

- the actual reviewed target or diff;
- applicable requirements;
- the exact canonical reviewer schema;
- the verbatim finding bar;
- bounded structural context;
- only material language guidance.

Commands and workdirs supplement the embedded artifact; they never replace it. Save the complete prompt as `prompt.md` in a directory created by `peer path`.

## Concurrent Dispatch

For implementation-owned review, launch every role's native agents and external fan-out in one assistant message. Standalone review launches all selected agents the same way. Resolve each selected alias through [peer routing](../../peer/reference/routing.md); do not restate or infer its mechanism here.

Implementation batch and integration review use the immutable batch routing snapshot, one shared run ID, and one fan-out per role. Standalone review uses its selected review configuration.

## Results

Read every successful native result and every `ok` peer manifest file. Result filename and manifest row are authoritative provenance.

Standalone review may synthesize available reports when at least one succeeds and must disclose partial coverage. An implementation-owned gate pauses until every execution class configured for the role has one successful report. Neither mode proceeds with zero reports.

For malformed output, retain the raw snippet, mark that reviewer failed, and continue only when the mode's execution-class minimum still holds. Redispatch only missing reports for the same wave.
