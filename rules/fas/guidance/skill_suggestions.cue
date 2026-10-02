package guidance

import "github.com/srnnkls/fas/cue/hook"

sg_test: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(tdd|test-driven|write tests?|add tests?|test first|red green)\b"#}
	then: inject: {rule_id: "suggest-test", channel: "agent", text: "A direct request for tests or TDD: use the `test` skill."}
}

sg_review: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(review|code review|check code|review changes|look over)\b"#}
	then: inject: {rule_id: "suggest-review", channel: "agent", text: "Consider using `review` skill for code review methodology."}
}

sg_scope: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(create|new|review|update|finish|list) (a |the )?scope\b"#}
	then: inject: {rule_id: "suggest-scope", channel: "agent", text: "Consider using `scope` skill for the scope lifecycle."}
}

sg_scope_docs: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(create spec|document spec|write spec|spec documents|done speccing|finalize spec)\b"#}
	then: inject: {rule_id: "suggest-scope-docs", channel: "agent", text: "Consider using `scope` skill to generate spec documents."}
}

sg_dispatch: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(execute|run|implement) (the )?(scope|spec)\b"#}
	then: inject: {rule_id: "suggest-dispatch", channel: "agent", text: "Consider using `dispatch` skill to route an explicit scope execution request."}
}

sg_skill: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(create skill|new skill|add skill|slash command)\b"#}
	then: inject: {rule_id: "suggest-skill", channel: "agent", text: "Consider using `skill` skill to build new skills."}
}

sg_pr: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(pull request|github pr|review pr|gh pr)\b"#}
	then: inject: {rule_id: "suggest-pr", channel: "agent", text: "Consider using `review` skill for GitHub PR review."}
}

sg_code_style: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(commit guideline|coding guideline|coding standard|code convention|style guide|naming convention|best practice)\b"#}
	then: inject: {rule_id: "suggest-code-style", channel: "agent", text: "Consider the `code.style` slot providers for language-specific guidelines; the `skill` skill's `scripts/resolve-slots code.style` lists them."}
}

sg_worktree: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)(worktree|\.worktrees|isolated workspace|parallel branch|separate workspace|work in isolation|isolate work|branch isolation)"#}
	then: inject: {rule_id: "suggest-worktree", channel: "agent", text: "Before a worktree operation, load the git skill and read reference/worktree.md. If unavailable, report the gap instead of reconstructing the procedure."}
}
