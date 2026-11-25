package workflow

import (
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

apply_slot_providers: {
	when: hook.#SubagentStart & {agent_type: =~"^(tester|implementer|fixer)(-|$)", ...}
	then: inject: {
		rule_id: "apply-slot-providers"
		channel: "agent"
		text:    "Resolve and apply your slot providers per `henia show 'implement.reference.subagent-workflow#resolution'`."
	}
}

_resolveSlots: "Resolve this skill's slots as its head says before acting on the skill."

resolve_skill_slots: {
	when: hook.#PostToolUse & tool.#Skill
	then: inject: {
		rule_id: "resolve-skill-slots"
		channel: "agent"
		text:    _resolveSlots
	}
}

resolve_shown_skill_slots: {
	when: hook.#PostToolUse & tool.#Bash & {tool_response: stdout: =~"(?m)^Slot providers:$", ...}
	then: inject: {
		rule_id: "resolve-shown-skill-slots"
		channel: "agent"
		text:    _resolveSlots
	}
}
