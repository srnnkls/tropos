package workflow

import (
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

implement_populate_task_list: {
	when: hook.#PreToolUse & tool.#Skill & {
		tool_input: {
			skill: =~"(?i)^(implement|loop|continue)$"
			args:  =~#"(^|[\s/])scopes/[^/\s]+/[^/\s]+"#
		}
	}
	then: inject: {
		rule_id:  "implement-populate-task-list"
		channel:  "agent"
		priority: 60
		text:     "Scope run — read the scope's tasks.yaml before dispatching; it is the sole task-status authority. A task list, if kept, mirrors it as display state only (see `implement` operations/execute.md)."
	}
}
