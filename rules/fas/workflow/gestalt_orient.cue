package workflow

import (
	"github.com/srnnkls/fas/cue/agent"
	"github.com/srnnkls/fas/cue/hook"
)

gestalt_orient: {
	when: hook.#SubagentStart & (agent.#Explore | agent.#Plan | agent.#GeneralPurpose)
	then: inject: {
		rule_id: "gestalt-orient"
		channel: "agent"
		text:    "First action: `gestalt map` (Plan: also `gestalt analyze`); then `gestalt callers|callees|refs <symbol>`; rg after."
	}
}
