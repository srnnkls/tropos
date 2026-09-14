package guidance

import (
	"list"

	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

proactive_mindset: {
	when: hook.#UserPromptSubmit
	then: inject: {
		rule_id:  "proactive-mindset"
		channel:  "agent"
		priority: 40
		text: """
			Operating mindset — be proactive and act. Once you have enough, act (recommend, don't survey options you won't take). Take the hardest part head-on rather than circling it. A long, multi-step turn is fine — don't stop early or hand back a plan you could execute. Lead with the outcome (first sentence = what happened / what you found). Ground every progress claim in a check that can fail — a test that ran, an artifact that exists in the right shape, a source actually read — not "it looks right." Before delivering, read your result as a skeptic: name its weakest part and fix it or flag it. When the user is only asking or thinking aloud, give your assessment and stop. (Full profile: CLAUDE.md.)
			"""
	}
}
proactive_parallel_dispatch: {
	when: hook.#PreToolUse & tool.#Agent
	then: inject: {
		rule_id:  "proactive-parallel-dispatch"
		channel:  "agent"
		priority: 40
		text:     "If other subtasks here are independent, dispatch them as additional Agent calls in THIS message so they run concurrently — don't spawn one, wait for it, then spawn the next."
	}
}

proactive_delegate_async: {
	when: hook.#PostToolUse & (tool.#Agent | tool.#TaskCreate)
	then: inject: {
		rule_id: "proactive-delegate-async"
		channel: "agent"
		text:    "Sub-agent running — keep working on independent threads instead of blocking on its result. Intervene only if it goes off track or is missing context."
	}
}
proactive_execute_the_plan: {
	when: hook.#PostToolUse & tool.#TodoWrite & {
		tool_input: todos: list.MatchN(>0, {status: "pending", ...}) & list.MatchN(0, {status: "in_progress", ...})
	}
	then: inject: {
		rule_id:  "proactive-execute-the-plan"
		channel:  "agent"
		priority: 40
		text:     "Plan captured — now execute. Start the first task immediately and dispatch independent ones as parallel sub-agents; don't keep refining the list before acting."
	}
}
proactive_workaround_on_failure: {
	when: hook.#PostToolUse & tool.#Bash & {
		tool_response: {exit_code: !=0, stderr: =~".+", ...}
	}
	then: inject: {
		rule_id:  "proactive-workaround-on-failure"
		channel:  "agent"
		priority: 40
		text:     "That command failed — a blocked path isn't a dead end. Read the actual error, then route around it: adjust the command, use a different tool, or build a small scaffold (a script, a probe, a throwaway server) to get what you need. If the whole approach failed, find the real cause and switch strategy rather than retrying the same way. Report blocked or ask the user only after you've genuinely tried another route."
	}
}
