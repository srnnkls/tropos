# Review Harnesses

Registry and dispatch mechanics: [peer routing contract](../../peer/reference/routing.md). External harness flags and failures: [peer skill](../../peer/SKILL.md).

## Dispatch Prompt

Write one `prompt.md` per role with the [reviewer fields](../../implement/reference/subagent-workflow.md#dispatch) in a directory created by `peer path`, and dispatch per that section. The prompt names the reviewed target and the files of its requirements and diff; it embeds no library text.

## Role Slots

Each reviewer reads, for the change's domains and languages, the providers its skills list:

- every role: `review.criteria`;
- General: `review.general` and `review.tests`;
- Architecture: `review.architecture`;
- Compliance: `code.style` and `code.conformance`;
- Abstractions: `review.abstractions`, and it runs each `review.detectors` command on the change and weighs the dispatch's `ownership` entries.

## Concurrent Dispatch

Launch every selected role's native agents and external fan-out for an initial review, implementation-owned or standalone, in one assistant message. Resolve each alias through [peer routing](../../peer/reference/routing.md) without restating its mechanism.

Implementation batch and integration review use the immutable batch routing snapshot, one shared run ID, and one fan-out per role; standalone review uses its selected review configuration. Post-fix verification is outside this fan-out and follows [targeted re-review](synthesis.md#46-fix-and-re-review-protocol).

## Results

Read every successful native result and every `ok` peer manifest file; result filename and manifest row are authoritative provenance.

Required successful reports by dispatch owner:

- ad-hoc standalone review: at least one; disclose missing coverage;
- issue-authoring gate: one successful report from every execution class in its explicit selection or the live default reviewer ensemble;
- configured scope review: one successful report from every execution class selected by `validation.yaml.review_config`, resolved against live routing;
- implementation-owned initial or integration review: one successful report from every execution class in the immutable batch snapshot;
- post-fix targeted re-review: exactly one compatible reviewer report under the [canonical fix protocol](synthesis.md#46-fix-and-re-review-protocol), no per-class minimum.

No mode proceeds with zero successful reports or requires a class absent from its configuration source.

Malformed output is a failed report. In a class-gated wave, retain its raw snippet and redispatch the missing class; never weaken the class minimum. In a targeted re-review, retain the snippet and use only the single replacement attempt.
