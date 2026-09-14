package workflow

import (
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

dispatch_use_tester: {
	when: hook.#PreToolUse & (tool.#Task | tool.#Agent) & {
		tool_input: {
			description:    =~#"(?i)(\b(write|add|strengthen|update|fix|red)\b[^\n]*\btests?\b|\btdd\b|\bfailing tests?\b)"#
			subagent_type?: !="tester"
		}
	}
	then: inject: {
		rule_id:  "dispatch-use-tester"
		channel:  "agent"
		priority: 60
		text:     "This is Phase A (tester) work — dispatch it as the dedicated `tester` subagent, not a generic Agent, so the phase-transition protocol engages (A → A.5 test-review gate → B → C). The orchestrator NEVER authors tests; delegate. Verify RED before moving on."
	}
}

dispatch_use_implementer: {
	when: hook.#PreToolUse & (tool.#Task | tool.#Agent) & {
		tool_input: {
			description:    =~#"(?i)(\bimplement(ation|ing)?\b|\bmake [^\n]{0,24}\bpass\b|\bgreen state\b|\bbuild (the )?feature\b)"#
			subagent_type?: !="implementer"
		}
	}
	then: inject: {
		rule_id:  "dispatch-use-implementer"
		channel:  "agent"
		priority: 60
		text:     "This is Phase B (implementer) work — dispatch it as the dedicated `implementer` subagent, not a generic Agent. Precondition: tests exist, are RED, and cleared the Phase A.5 review gate. The orchestrator NEVER writes code; delegate, then verify GREEN."
	}
}

dispatch_use_reviewer: {
	when: hook.#PreToolUse & (tool.#Task | tool.#Agent) & {
		tool_input: {
			description:    =~#"(?i)\breview(s|er|ers|ing)?\b"#
			description:    !~#"(?i)\b(fix|address|resolve|remediate|apply)\b"#
			subagent_type?: !="reviewer"
		}
	}
	then: inject: {
		rule_id:  "dispatch-use-reviewer"
		channel:  "agent"
		priority: 60
		text:     "Review work — per role, dispatch a Claude `reviewer` subagent PLUS one `peer run` for the external reviewers (codex + gemini, per validation.yaml review_config). `peer run` fans out to all external harnesses; never shell out to codex/gemini directly. Every batch is reviewed before commit. See the `peer` skill."
	}
}

tester_role_contract: {
	when: hook.#SubagentStart & {agent_type: "tester"}
	then: inject: {
		rule_id: "tester-role-contract"
		channel: "agent"
		text: """
			You are a TESTER (Phase A). Orient with `gestalt map` first.
			Iron Law of TDD: write FAILING tests, then verify RED — tests must fail because the feature is MISSING, not from typos or imports. Discover expected behavior from specs/code independently; never mirror an implementation or assume the answer in a mock.
			Final message = ONLY the tester_report YAML, no prose.
			"""
	}
}

implementer_role_contract: {
	when: hook.#SubagentStart & {agent_type: "implementer"}
	then: inject: {
		rule_id: "implementer-role-contract"
		channel: "agent"
		text: """
			You are an IMPLEMENTER (Phase B). Orient with `gestalt map` first; consult `loqui` for language guidelines.
			Run the failing tests, write the MINIMAL code to make them GREEN, then refactor while staying green. Do NOT weaken, skip, or edit the tests to pass.
			Final message = ONLY the implementer_report YAML, no prose.
			"""
	}
}

reviewer_role_contract: {
	when: hook.#SubagentStart & {agent_type: "reviewer"}
	then: inject: {
		rule_id: "reviewer-role-contract"
		channel: "agent"
		text: """
			You are a REVIEWER (Phase C). Orient with `gestalt map` first; apply `/code-review` methodology.
			Review the batch's changes against scope requirements and report issues by severity — do not fix them.
			Final message = ONLY the review report YAML, no prose.
			"""
	}
}
