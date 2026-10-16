package workflow

import "github.com/srnnkls/fas/cue/hook"

cross_session_messaging: {
	when: hook.#PreToolUse & {tool_name: "SendMessage" | "ListAgents"}
	then: deny: {
		rule_id:  "cross-session-messaging"
		reason:   "Reach other agent sessions through herdr: `herdr --help`, `herdr --skill`."
		severity: "MEDIUM"
	}
}
