package workflow

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_pollInspect: "(git|ls|cat|wc|find|jq|tail|head|grep|rg|stat|date|test)"

sleep_long: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {
			command:   "sleep"
			arguments: list.MatchN(>0, =~#"^([3-9][0-9]|[0-9]{3,})(\.[0-9]+)?s?$|^[0-9]+(\.[0-9]+)?[mh]$"#)
		}
	})
	then: deny: {
		rule_id:  "sleep-long"
		reason:   "Sleep ≥30s denied. Completion of subagents, background commands and workflows re-invokes you; do other work. Use ScheduleWakeup for a timed return."
		severity: "MEDIUM"
	}
}

sleep_poll_chain: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#command & {#name: "sleep"}) & {
		tool_input: command: =~"(?i)(\\bsleep\\b[^\\n]*[;&|]\\s*\\b\(_pollInspect)\\b|\\b\(_pollInspect)\\b[^\\n]*[;&|]\\s*sleep\\b)"
	}
	then: deny: {
		rule_id:  "sleep-poll-chain"
		reason:   "Denied: sleep chained to a status check. Inspect state once now, or wait for the completion notification."
		severity: "MEDIUM"
	}
}
