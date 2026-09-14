package guidance

import "github.com/srnnkls/fas/cue/hook"

sg_debug: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(bug|debug|error|failing|broken|not working|crash|exception|traceback|stack trace|unexpected|investigate)\b"#}
	then: inject: {rule_id: "suggest-debug", channel: "agent", text: "Consider using `implement` skill for systematic debugging."}
}

sg_debug_intent: {
	when: hook.#UserPromptSubmit & {prompt: =~"(?i)(fix|debug|investigate|find).*(bug|error|issue|problem)"}
	then: inject: {rule_id: "suggest-debug", channel: "agent", text: "Consider using `implement` skill for systematic debugging."}
}

sg_test: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(tdd|test-driven|write test|add test|unit test|test first|red green)\b"#}
	then: inject: {rule_id: "suggest-test", channel: "agent", text: "Consider using `test` skill for TDD workflow."}
}

sg_implement: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(implement|add feature|create function|write code|new feature)\b"#}
	then: inject: {rule_id: "suggest-test", channel: "agent", text: "Consider using `test` skill for TDD workflow."}
}

sg_review: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(review|code review|check code|review changes|look over)\b"#}
	then: inject: {rule_id: "suggest-review", channel: "agent", text: "Consider using `review` skill for code review methodology."}
}

sg_scope: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(specification|validate spec|clarify requirements|requirements|scope|unclear|ambiguous)\b"#}
	then: inject: {rule_id: "suggest-scope", channel: "agent", text: "Consider using `scope` skill for requirements clarification."}
}

sg_scope_docs: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(create spec|document spec|write spec|spec documents|done speccing|ready to implement|finalize spec)\b"#}
	then: inject: {rule_id: "suggest-scope-docs", channel: "agent", text: "Consider using `scope` skill to generate spec documents."}
}

sg_dispatch: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(execute spec|execute tasks|run tasks|dispatch tasks|dispatch|subagent|parallel tasks)\b"#}
	then: inject: {rule_id: "suggest-dispatch", channel: "agent", text: "Consider using `implement` skill for subagent execution."}
}

sg_skill: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(create skill|new skill|add skill|slash command)\b"#}
	then: inject: {rule_id: "suggest-skill", channel: "agent", text: "Consider using `skill` skill to build new skills."}
}

sg_pr: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(pull request|github pr|review pr|gh pr)\b"#}
	then: inject: {rule_id: "suggest-pr", channel: "agent", text: "Consider using `review` skill for GitHub PR review."}
}

sg_loqui: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(commit guideline|coding guideline|coding standard|code convention|style guide|naming convention|best practice)\b"#}
	then: inject: {rule_id: "suggest-loqui", channel: "agent", text: "Consider using `loqui` skill for language-specific guidelines."}
}

sg_worktree: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)(worktree|\.worktrees|isolated workspace|parallel branch|separate workspace|work in isolation|isolate work|branch isolation)"#}
	then: inject: {rule_id: "suggest-worktree", channel: "agent", text: "Before a worktree operation, load the git skill and read reference/worktree.md. If unavailable, report the gap instead of reconstructing the procedure."}
}
