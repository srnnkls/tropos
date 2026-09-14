package workflow

import (
	"github.com/srnnkls/fas/cue/agent"
	"github.com/srnnkls/fas/cue/hook"
)

explore_gestalt_orient: {
	when: hook.#SubagentStart & agent.#Explore
	then: inject: {
		rule_id: "explore-gestalt-orient"
		channel: "agent"
		text: """
			Before exploring, run `gestalt map` to orient — call graph, clusters, hotspots, coupling.
			Then drill in with `gestalt callers <symbol>`, `gestalt callees <symbol>`, `gestalt refs <symbol>`.
			Use gestalt for structural understanding first, then rg for targeted lookups.
			"""
	}
}

plan_gestalt_orient: {
	when: hook.#SubagentStart & agent.#Plan
	then: inject: {
		rule_id: "plan-gestalt-orient"
		channel: "agent"
		text: """
			Before designing a plan, run `gestalt analyze` for architecture — hotspots, seams, coupling — and `gestalt map` for navigation.
			Trace impact with `gestalt callers <symbol>` / `gestalt callees <symbol>` / `gestalt refs <symbol>` before committing to an approach.
			Ground the plan in the actual structure, then confirm specifics with rg.
			"""
	}
}

general_gestalt_orient: {
	when: hook.#SubagentStart & agent.#GeneralPurpose
	then: inject: {
		rule_id: "general-gestalt-orient"
		channel: "agent"
		text: """
			Before starting, run `gestalt map` to orient — call graph, clusters, hotspots, coupling.
			Then drill in with `gestalt callers <symbol>`, `gestalt callees <symbol>`, `gestalt refs <symbol>`.
			Use gestalt for structural understanding first, then rg for targeted lookups.
			"""
	}
}
