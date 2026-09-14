package workflow

import (
	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

scope_commit_checkpoint: {
	when: hook.#PostToolUse & hook.#MainThread & tool.#Bash & (bash.#call & {#match: {command: "git", subcommand: "commit"}}) & {
		tool_input: command:      !~"(?i)checkpoint"
		tool_response: exit_code: 0
	}
	then: inject: {
		rule_id:  "scope-commit-checkpoint"
		channel:  "agent"
		priority: 55
		text:     "Commit landed. If this is a scope batch, refresh ./scopes/<state>/<name>/checkpoint.yaml — last_batch, last_commit, task done/pending, next_batch — and commit it so `continue` can resume from here. Skip if this commit isn't scope work."
	}
}
