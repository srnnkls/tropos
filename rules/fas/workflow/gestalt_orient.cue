package workflow

import (
	"github.com/srnnkls/fas/cue/agent"
	"github.com/srnnkls/fas/cue/hook"
)

_workflowRole: "^(tester|implementer|reviewer|fixer)(-|$)"

orient: {
	when: hook.#SubagentStart & (agent.#Explore | agent.#Plan | agent.#GeneralPurpose | {agent_type: =~_workflowRole, ...})
	then: inject: {
		rule_id: "orient"
		channel: "agent"
		text:    "First action: `gestalt map`, `gestalt analyze`, then `callers`/`callees`/`refs` for the symbols you touch (CLAUDE.md, Subagent orientation)."
	}
}
