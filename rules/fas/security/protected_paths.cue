package security

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_protectedPath: =~#"^(/etc|/System|/private/etc)(/|$)"# | =~#"(^|/)\.ssh(/|$)"#
_gitHooksPath:  =~#"(^|/)\.git/hooks(/|$)"#
_writeCommands: "rm" | "cp" | "mv" | "ln" | "dd" | "tee" | "install" | "truncate" | "chmod" | "chown" | "chgrp" | "mkdir" | "rmdir" | "touch"

protected_edit: {
	when: hook.#PreToolUse & (tool.#Edit | tool.#Write | tool.#NotebookEdit) & {
		tool_input: file_path: =~"^(/etc|/System|/private/etc)(/|$)" | =~#"(^|/)\.ssh(/|$)"#
	}
	then: deny: {
		rule_id:  "protected-path-edit"
		reason:   "This path is protected (system config or ~/.ssh) and cannot be modified."
		severity: "HIGH"
	}
}

protected_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: edits: list.MatchN(>0, {file_path: =~"^(/etc|/System|/private/etc)(/|$)" | =~#"(^|/)\.ssh(/|$)"#, ...})
	}
	then: deny: {
		rule_id:  "protected-path-multiedit"
		reason:   "This path is protected (system config or ~/.ssh) and cannot be modified."
		severity: "HIGH"
	}
}

protected_bash_write: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: _writeCommands, targets: list.MatchN(>0, _protectedPath)}
	})
	then: deny: {
		rule_id:  "protected-path-bash"
		reason:   "Writing to a protected path (system config or ~/.ssh) is not permitted."
		severity: "HIGH"
	}
}

git_hooks_edit: {
	when: hook.#PreToolUse & (tool.#Edit | tool.#Write | tool.#MultiEdit | tool.#NotebookEdit) & {
		tool_input: file_path: _gitHooksPath
	}
	then: deny: {
		rule_id:  "git-hooks-edit"
		reason:   "Git hook files are protected from modification."
		severity: "HIGH"
	}
}
