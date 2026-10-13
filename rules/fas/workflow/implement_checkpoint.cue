package workflow

import (
	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_mutatingRole: "^(tester|implementer)(-|$)"

_scopeRun: #"(^|[^\w.-])scopes/[^/\s]+/[^/\s]+|\.peer/[^/\s]+/[^/\s]+/b[0-9]+-"#

_stageEntry: "Before dispatch: arm `in_flight_mutations` in checkpoint.yaml (task, phase, agent, report_dir, status, evidence.before) in one write per wave."

_cursorEntry: "Before review dispatch: set `batch.phase: review` and record `reports.review` dirs in one write."

checkpoint_stage_before_mutating_dispatch: {
	when: hook.#PreToolUse & hook.#MainThread & (tool.#Task | tool.#Agent) & {
		tool_input: {
			subagent_type: =~_mutatingRole
			prompt:        =~_scopeRun
		}
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
	}) & {tool_input: command: =~_scopeRun}
	then: inject: {
		rule_id:  "checkpoint-stage-before-mutating-peer"
		channel:  "agent"
		priority: 70
		text:     _stageEntry
	}
}

checkpoint_cursor_before_review_dispatch: {
	when: hook.#PreToolUse & hook.#MainThread & (tool.#Task | tool.#Agent) & {
		tool_input: {
			subagent_type: =~"^reviewer(-|$)"
			prompt:        =~_scopeRun
		}
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
	}) & {tool_input: command: =~_scopeRun}
	then: inject: {
		rule_id:  "checkpoint-cursor-before-review-peer"
		channel:  "agent"
		priority: 70
		text:     _cursorEntry
	}
}

checkpoint_peer_launch_handle: {
	when: hook.#PostToolUse & hook.#MainThread & tool.#Bash & (bash.#call & {
		#match: bash.#argumentPair & {command: "peer", #first: "--agent", #second: =~_mutatingRole}
	}) & {tool_input: command: =~_scopeRun}
	then: inject: {
		rule_id:  "checkpoint-peer-launch-handle"
		channel:  "agent"
		priority: 60
		text:     "Record the peer's task id, output file and report_dir in its `in_flight_mutations` entry."
	}
}

checkpoint_clear_after_peer_report: {
	when: hook.#PostToolUse & hook.#MainThread & tool.#Read & {
		tool_input: file_path: =~#"\.peer/[^/]+/[^/]+/b[0-9]+-[^/]+/.*\.ya?ml$"#
	}
	then: inject: {
		rule_id:  "checkpoint-clear-after-peer-report"
		channel:  "agent"
		priority: 65
		text:     "Apply the RED/GREEN/finding gate before editing checkpoint.yaml; write wave results once after all reports land."
	}
}
