package workflow

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_worktreePolicy: "Load the git skill and read reference/worktree.md. If unavailable, report the gap and stop."

#WorktreeCreation: (tool.#Bash & (bash.#call & {
	#match: {command: "git", subcommand: "worktree", subcommand_args: ["add", ...]}
})) | tool.#EnterWorktree | ((tool.#Agent | tool.#Task) & {
	tool_input: {isolation: "worktree", ...}
	...
})

worktree_outside_repo: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {
			command:         "git"
			subcommand:      "worktree"
			subcommand_args: ["add", ...]
			targets:         list.MatchN(>0, =~"^(/|~|\\$HOME|\\.\\.)" & !~"/(\\.)?worktrees(/|$)")
		}
	})
	then: deny: {
		rule_id:  "worktree-outside-repo"
		reason:   "Worktree target escapes the repo (/tmp, ~, $HOME, ../). Create it project-local instead: `git worktree add .worktrees/<name> -b <branch> origin/<trunk>`, then link ignored state with `git worktreeinclude apply`. Paths outside the checkout get no .gitignore coverage and drift from the repo they were cut from."
		severity: "MEDIUM"
	}
}

worktree_creation_followup: {
	when: hook.#PostToolUse & #WorktreeCreation
	then: inject: {
		rule_id: "worktree-creation-followup"
		channel: "agent"
		text:    _worktreePolicy + " Follow its applicable post-creation steps before reporting the worktree ready; ground completion in the tool result and verification evidence."
	}
}

worktree_include_followup: {
	when: hook.#PostToolUse & tool.#Bash & (bash.#call & {
		#match: {command: "git", subcommand: "worktreeinclude", subcommand_args: ["apply", ...]}
	})
	then: inject: {
		rule_id: "worktree-include-followup"
		channel: "agent"
		text:    _worktreePolicy + " Apply the result-verification requirements in its 'Link Ignored Repo-Root State' section before claiming state is linked."
	}
}
