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
		text:    "Read every slot provider your skills list for the task's domain and languages with the command it names, apply them, and name each one with the rules it contributed in your report's `providers_applied`."
	}
}

_resolveSlots: "Resolve this skill's slots: read each listed provider your task needs with the command it names before acting on the skill."

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
