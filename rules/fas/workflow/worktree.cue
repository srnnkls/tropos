package workflow

import (
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

worktree_creation_approval: {
	when: hook.#PreToolUse & #WorktreeCreation
	then: ask: {
		rule_id:  "worktree-creation-approval"
		reason:   _worktreePolicy
		question: "Have the applicable worktree preconditions in git/reference/worktree.md been checked, and do you approve this worktree operation?"
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
