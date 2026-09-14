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
		reason:   "Sleeping ≥30s is waiting by polling. Subagent, background-Bash, and workflow completion arrive as a notification that re-invokes you — the sleep only delays when you see it. Do other work now and answer the notification when it lands; use ScheduleWakeup if you genuinely need a timed return, or TaskOutput to read a running agent."
		severity: "MEDIUM"
	}
}

sleep_poll_chain: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#command & {#name: "sleep"}) & {
		tool_input: command: =~"(?i)(\\bsleep\\b[^\\n]*[;&|]\\s*\\b\(_pollInspect)\\b|\\b\(_pollInspect)\\b[^\\n]*[;&|]\\s*sleep\\b)"
	}
	then: deny: {
		rule_id:  "sleep-poll-chain"
		reason:   "sleep chained to a status check is a poll loop. Completion of subagents, background Bash, and workflows is pushed to you as a notification — checking on a timer adds wall time and finds nothing the notification wouldn't deliver. Drop the sleep; inspect state once, now, or wait for the notification."
		severity: "MEDIUM"
	}
}

sleep_hint: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#command & {#name: "sleep"})
	then: inject: {
		rule_id:  "sleep-hint"
		channel:  "agent"
		priority: 50
		text:     "You are about to sleep. Nothing in this harness needs polling: subagents, background Bash, and workflows all notify you on completion. Sleep only to pace something external (a rate limit, a service that needs a moment to bind) — never to wait on your own agents."
	}
}
