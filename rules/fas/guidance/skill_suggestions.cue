package guidance

import "github.com/srnnkls/fas/cue/hook"

sg_scope: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)(\b(create|new|review|update|finish|list) (a |the )?scope\b|\b(create spec|document spec|write spec|spec documents|done speccing|finalize spec)\b)"#}
	then: inject: {rule_id: "suggest-scope", channel: "agent", text: "Load the `scope` skill."}
}

sg_dispatch: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(execute|run|implement) (the )?(scope|spec)\b"#}
	then: inject: {rule_id: "suggest-dispatch", channel: "agent", text: "Load the `dispatch` skill."}
}

sg_skill: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(create skill|new skill|add skill)\b"#}
	then: inject: {rule_id: "suggest-skill", channel: "agent", text: "Load the `skill` skill."}
}

sg_worktree: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(create|use|start|switch to|remove|add) (a |the )?(git )?worktree"#}
	then: inject: {rule_id: "suggest-worktree", channel: "agent", text: "Before a worktree operation, read `henia show git/reference/worktree.md`. If unavailable, report the gap instead of reconstructing the procedure."}
}
