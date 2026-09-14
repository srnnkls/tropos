package workflow

import (
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

implement_populate_task_list: {
	when: hook.#PreToolUse & tool.#Skill & {
		tool_input: skill: =~"(?i)^(implement|loop|continue)$"
	}
	then: inject: {
		rule_id:  "implement-populate-task-list"
		channel:  "agent"
		priority: 60
		text:     "Before dispatching any subagent: read ./scopes/<state>/<name>/tasks.yaml and populate the task list with EVERY uncompleted task (first one in_progress, rest pending). This is a precondition, not bookkeeping — batching, resume, and the tasks.yaml write-back all read from it."
	}
}

implement_task_list_before_phase_a: {
	when: hook.#PreToolUse & (tool.#Task | tool.#Agent) & {
		tool_input: subagent_type: "tester"
	}
	then: inject: {
		rule_id:  "implement-task-list-before-phase-a"
		channel:  "agent"
		priority: 55
		text:     "Batch opening — the task list must already carry this batch's tasks, with the ones now in flight marked in_progress. If it's empty or stale (resumed session, new batch), refresh it from tasks.yaml in this same message."
	}
}
