package guidance

import (
	"list"

	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

proactive_execute_the_plan: {
	when: hook.#PostToolUse & tool.#TodoWrite & {
		tool_input: todos: list.MatchN(>0, {status: "pending", ...}) & list.MatchN(0, {status: "in_progress", ...})
	}
	then: inject: {
		rule_id:  "proactive-execute-the-plan"
		channel:  "agent"
		priority: 40
		text:     "Mark the first todo in_progress and start it now."
	}
}

proactive_workaround_on_failure: {
	when: hook.#PostToolUse & tool.#Bash & {
		tool_response: {exit_code: !=0, stderr: =~".+", ...}
	}
	then: inject: {
		rule_id:  "proactive-workaround-on-failure"
		channel:  "agent"
		priority: 40
		text:     "Read the error. If it is a permission or sandbox denial, report it. Otherwise change the command or approach; do not rerun it unchanged."
	}
}
