# Review Harnesses

Review-specific prompt materialization, concurrent fan-out, and partial-result semantics. Registry and dispatch mechanics live in the canonical [peer routing contract](../../peer/reference/routing.md); external harness flags and failures live in the [peer skill](../../peer/SKILL.md).

## Materialization

Build one self-contained prompt per role before dispatch. Embed:

- the actual reviewed target or diff;
- applicable requirements;
- the exact canonical reviewer schema;
- the verbatim finding bar;
- fresh bounded output from the [repository-orientation contract](../../../instructions/AGENTS.md#tools-and-context) for the reviewed working tree;
- only material language guidance.

Commands and workdirs supplement the embedded artifact; they never replace it. Save the complete prompt as `prompt.md` in a directory created by `peer path`.

## Concurrent Dispatch

For implementation-owned initial review, launch every role's native agents and external fan-out in one assistant message. Standalone review launches all selected agents the same way. Resolve each selected alias through [peer routing](../../peer/reference/routing.md); do not restate or infer its mechanism here.

Implementation batch and integration review use the immutable batch routing snapshot, one shared run ID, and one fan-out per role. Standalone review uses its selected review configuration. Post-fix verification is excluded from this fan-out and follows the targeted re-review protocol in [review synthesis](synthesis.md#46-fix-and-re-review-protocol).

## Results

Read every successful native result and every `ok` peer manifest file. Result filename and manifest row are authoritative provenance.

Result eligibility depends on the dispatch owner:

- An ad-hoc standalone review may synthesize available reports when at least one succeeds and must disclose missing coverage.
- An issue-authoring gate requires one successful report from every execution class in its explicit selection or the live default reviewer ensemble.
- A configured scope review requires one successful report from every execution class selected by `validation.yaml.review_config` after resolution against live routing.
- An implementation-owned initial or integration review requires one successful report from every execution class in the immutable batch snapshot.
- A post-fix targeted re-review accepts exactly one successful compatible reviewer report under the [canonical fix protocol](synthesis.md#46-fix-and-re-review-protocol); it has no per-class minimum.

No mode proceeds with zero successful reports or requires a class absent from its configuration source.

Malformed output is a failed report. For a class-gated wave, retain its raw snippet and deliberately redispatch the missing class; never weaken that wave's class minimum. For targeted re-review, retain the snippet and use only the canonical single replacement attempt.
