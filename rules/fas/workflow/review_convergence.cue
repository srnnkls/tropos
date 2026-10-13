package workflow

import (
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

peer_prompt_missing_finding_bar: {
	when: hook.#PreToolUse & tool.#Write & {
		tool_input: file_path: =~#"prompt\.md$"#
		tool_input: content:   =~"(?i)(you are the (general|architecture|compliance|abstractions) reviewer|reviewer_report|test_review_report)"
		tool_input: content:   !~"(?i)finding bar"
	}
	then: inject: {
		rule_id:  "peer-prompt-missing-finding-bar"
		channel:  "agent"
		priority: 60
		text:     "Reviewer prompt lacks the finding bar: insert `henia show review/reference/finding-bar.md` verbatim."
	}
}

fix_round_convergence: {
	when: hook.#PreToolUse & (tool.#Task | tool.#Agent) & {
		tool_input: description: =~#"(?i)\b(fix|address|resolve|remediate)\b[^\n]*\b(finding|findings|issue|issues|review|feedback|comment|comments)\b"#
		tool_input: prompt:      =~#"(?i)(\.peer/|review\.yaml|finding)"#
	}
	then: inject: {
		rule_id:  "fix-round-convergence"
		channel:  "agent"
		priority: 60
		text:     "Fix round: one wave per mechanism group (synthesis.md §4.6); at most two rounds per subject; `needs decision:` findings go to the user."
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
		text:    "Permutation sweep: unless requirements name these cases, keep only cases that fail when the behavior is wrong; report uncovered reachable cases as gaps."
	}
}
