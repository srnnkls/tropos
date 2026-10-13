package workflow

import (
	"github.com/srnnkls/fas/cue/agent"
	"github.com/srnnkls/fas/cue/hook"
)

orient: {
	when: hook.#SubagentStart & (agent.#Explore | agent.#Plan | agent.#GeneralPurpose)
	then: inject: {
		rule_id: "orient"
		channel: "agent"
		text:    "First action: orient (CLAUDE.md, Subagent orientation)."
	}
}
