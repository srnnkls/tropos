package workflow

import (
	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_mutatingRole: "^(tester|implementer)(-|$)"

_stageEntry: "Before this dispatch, checkpoint.yaml needs an `incomplete_stages` entry: batch, task, phase (tester|implementer|fix), agent alias, report_dir, `status: in_progress`, and pre-dispatch `git status --short` plus the relevant diff. Write it now if it isn't there — a stall past this point is unrecoverable without it."

_cursorEntry: "Before this review gate, set `phase_cursor` to the gate phase with `status: in_progress` and one entry per configured alias (test_review/targeted_review → `reports`; code_review/final_review → `roles`), each with its report_dir and `status: pending`. Preserve roles already completed."

checkpoint_brief_staged: {
	when: hook.#PostToolUse & hook.#MainThread & tool.#Write & {
		tool_input: file_path: =~#"\.peer/.*(tester|implementer|fix)[^/]*brief"#
	}
	then: inject: {
		rule_id:  "checkpoint-brief-staged"
		channel:  "agent"
		priority: 75
		text:     "Brief staged — the dispatch is the next call. \(_stageEntry)"
	}
}

checkpoint_stage_before_mutating_dispatch: {
	when: hook.#PreToolUse & hook.#MainThread & (tool.#Task | tool.#Agent) & {
		tool_input: subagent_type: =~_mutatingRole
	}
	then: inject: {
		rule_id:  "checkpoint-stage-before-mutating-dispatch"
		channel:  "agent"
		priority: 70
		text:     _stageEntry
	}
}

checkpoint_stage_before_mutating_peer: {
	when: hook.#PreToolUse & hook.#MainThread & tool.#Bash & (bash.#call & {
		#match: bash.#argumentPair & {command: "peer", #first: "--agent", #second: =~_mutatingRole}
	})
	then: inject: {
		rule_id:  "checkpoint-stage-before-mutating-peer"
		channel:  "agent"
		priority: 70
		text:     _stageEntry
	}
}

checkpoint_cursor_before_review_dispatch: {
	when: hook.#PreToolUse & hook.#MainThread & (tool.#Task | tool.#Agent) & {
		tool_input: subagent_type: =~"^reviewer(-|$)"
	}
	then: inject: {
		rule_id:  "checkpoint-cursor-before-review-dispatch"
		channel:  "agent"
		priority: 70
		text:     _cursorEntry
	}
}

checkpoint_cursor_before_review_peer: {
	when: hook.#PreToolUse & hook.#MainThread & tool.#Bash & (bash.#call & {
		#match: bash.#argumentPair & {command: "peer", #first: "--agent", #second: =~"^reviewer(-|$)"}
	})
	then: inject: {
		rule_id:  "checkpoint-cursor-before-review-peer"
		channel:  "agent"
		priority: 70
		text:     _cursorEntry
	}
}

checkpoint_peer_launch_handle: {
	when: hook.#PostToolUse & hook.#MainThread & tool.#Bash & (bash.#call & {
		#match: bash.#argumentPair & {command: "peer", #first: "--agent", #second: =~"^(tester|implementer|reviewer)(-|$)"}
	})
	then: inject: {
		rule_id:  "checkpoint-peer-launch-handle"
		channel:  "agent"
		priority: 60
		text:     "Peer launched. Update its checkpoint entry with the launch metadata — task id, output file, report_dir — so a lost session can find the run instead of redispatching it."
	}
}

checkpoint_clear_after_peer_report: {
	when: hook.#PostToolUse & hook.#MainThread & tool.#Read & {
		tool_input: file_path: =~#"\.peer/.*\.ya?ml$"#
	}
	then: inject: {
		rule_id:  "checkpoint-clear-after-peer-report"
		channel:  "agent"
		priority: 65
		text:     "Report is in. Verify its gate (RED for a tester, GREEN for an implementer, the finding bar for a reviewer) BEFORE touching checkpoint.yaml — a clean tool exit is not a pass. On success: save the report under its report_dir, remove the `incomplete_stages` entry, advance `phase_cursor`. On failure or invalid report: keep the entry, `status: failed`, add post-failure git status/diff and the reason. Never roll back partial edits."
	}
}
