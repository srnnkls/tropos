package workflow

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

#WorktreeCreation: (tool.#Bash & (bash.#call & {
	#match: {command: "git", subcommand: "worktree", subcommand_args: ["add", ...]}
})) | tool.#EnterWorktree | ((tool.#Agent | tool.#Task) & {
	tool_input: {isolation: "worktree", ...}
	...
})

worktree_outside_repo: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {
			command:    "git"
			subcommand: "worktree"
			subcommand_args: ["add", ...]
			targets: list.MatchN(>0, =~"^(/|~|\\$HOME|\\.\\.)" & !~"/(\\.)?worktrees(/|$)")
		}
	})
	then: deny: {
		rule_id:  "worktree-outside-repo"
		reason:   "Worktree target escapes the repo (/tmp, ~, $HOME, ../). Create it project-local instead: `git worktree add .worktrees/<name> -b <branch> origin/<trunk>`, then link ignored state with `git worktreeinclude apply`."
		severity: "MEDIUM"
	}
}

worktree_creation_followup: {
	when: hook.#PostToolUse & #WorktreeCreation
	then: inject: {
		rule_id: "worktree-creation-followup"
		channel: "agent"
		text:    "Run the post-creation steps in `henia show git/reference/worktree.md` before reporting the worktree ready."
	}
}

worktree_include_followup: {
	when: hook.#PostToolUse & tool.#Bash & (bash.#call & {
		#match: {command: "git", subcommand: "worktreeinclude", subcommand_args: ["apply", ...]}
	})
	then: inject: {
		rule_id: "worktree-include-followup"
		channel: "agent"
		text:    "Verify each linked path exists in the worktree (`henia show git/reference/worktree.md`, Creation step 3); exit 0 does not prove linking."
	}
}
