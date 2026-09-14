package workflow

import (
	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

peer_prompt_missing_finding_bar: {
	when: hook.#PreToolUse & tool.#Write & {
		tool_input: file_path: =~#"prompt\.md$"#
		tool_input: content:   =~"(?i)(you are the (general|architecture|compliance) reviewer|reviewer_report|test_review_report)"
		tool_input: content:   !~"(?i)finding bar"
	}
	then: inject: {
		rule_id:  "peer-prompt-missing-finding-bar"
		channel:  "agent"
		priority: 60
		text:     "This reviewer prompt has no FINDING BAR. Materialize skills/review/reference/finding-bar.md into it verbatim before dispatch — a prompt without it is what produces one-assertion-per-round refinement spirals. No reviewer prompt goes out without it."
	}
}

peer_reviewer_fanout: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: bash.#argumentPair & {command: "peer", #first: "--agent", #second: =~"^reviewer(-|$)"}
	})
	then: inject: {
		rule_id: "peer-reviewer-fanout-bar"
		channel: "agent"
		text:    "Before this fan-out: the prompt file must carry the finding bar verbatim (skills/review/reference/finding-bar.md), plus the materialized diff, requirements, and exact report schema. External high-effort reviewers produce refinement spirals without it."
	}
}

fix_round_convergence: {
	when: hook.#PreToolUse & (tool.#Task | tool.#Agent) & {
		tool_input: description: =~#"(?i)\b(fix|address|resolve|remediate)\b[^\n]*\b(finding|findings|issue|issues|review|feedback|comment|comments)\b"#
	}
	then: inject: {
		rule_id:  "fix-round-convergence"
		channel:  "agent"
		priority: 60
		text: """
			TRIAGE BEFORE DISPATCH (skills/review/reference/synthesis.md §4.5–4.6):
			- Batch by mechanism, not by assertion. Two findings on the same state machine → sweep the machine and fix the set together; never open a round on the first one.
			- Two fix rounds per subject. A third opens only for a verified failure in a component no prior round examined — otherwise stop, record survivors as residual, and report to the user.
			- A finding whose suggestion reads `needs decision:` never goes to a fix agent. Surface it with its constraint.
			- Findings that failed triage are residual, not work.
			"""
	}
}

exhaustive_test_sweep: {
	when: hook.#PreToolUse & (tool.#Edit | tool.#Write) & {
		tool_input: file_path: =~#"(^|/)(tests?|spec)/|(^|/)test_[^/]*\.[a-z]+$|_test\.[a-z]+$|\.(test|spec)\.[a-z]+$"#
		tool_input: {
			new_string?: =~#"(?i)(itertools\.(product|permutations|combinations)|all_(combinations|permutations)|every (possible |single )?(crash|syscall|interleaving|permutation|transition)|exhaustiv)"#
			content?:    =~#"(?i)(itertools\.(product|permutations|combinations)|all_(combinations|permutations)|every (possible |single )?(crash|syscall|interleaving|permutation|transition)|exhaustiv)"#
		}
	}
	then: inject: {
		rule_id: "exhaustive-test-sweep"
		channel: "agent"
		text:    "This test looks like a permutation sweep. Unless the requirement names those cases, cover the guarantee with a small set of REPRESENTATIVE FALSIFIERS instead — the cases that fail if the behavior is wrong. Exhaustive enumeration of an input, syscall, or interleaving space is deferred hardening, not scope. A reachable uncovered case is a gap to report, not a matrix to encode."
	}
}
