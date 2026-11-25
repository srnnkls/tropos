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

_slotRole: {agent_type: =~"^(tester|implementer|fixer)(-|$)", ...}

provider_show_in_role: {
	when: hook.#PreToolUse & tool.#Bash & _slotRole & {tool_input: command: =~#"henia show ['"]?[\w-]+:"#}
	then: deny: {
		rule_id:  "slot-provider-show"
		reason:   "Denied: per-provider read. Resolve slot providers with one `henia slots --inline` call as the head's Slot providers says."
		severity: "MEDIUM"
	}
}

truncated_slots_in_role: {
	when: hook.#PreToolUse & tool.#Bash & _slotRole & {tool_input: command: =~#"henia slots [^|;]*--inline[^|;]*\|\s*(head|tail|sed)\b"#}
	then: deny: {
		rule_id:  "slot-output-truncated"
		reason:   "Denied: truncated slot output. Rerun `henia slots --inline` without a pipe and read the whole output."
		severity: "MEDIUM"
	}
}
