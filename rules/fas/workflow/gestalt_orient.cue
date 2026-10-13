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
		text: [if #slots.orientation != "" {"First action: orient.\n\n\(#slots.orientation)"}, "First action: orient per CLAUDE.md (Tools and context); rg after."][0]
	}
}
