package security

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_homeRe:        #""?(~|\$HOME|\$\{HOME\}|/Users/[^/"]+|/home/[^/"]+)"?"#
_redirectOutRe: #"^[0-9]*(&?>>?|>\|)"?"#

_protectedRe:   #"(^|[>|"=])(/etc|/private/etc)(/|"?$)|(^|[/>|"=])\.ssh(/|"?$)"#
_protectedPath: =~_protectedRe

_anyTargetWriter: "rm" | "mv" | "dd" | "tee" | "truncate" | "chmod" | "chown" | "chgrp" | "mkdir" | "rmdir" | "touch"

_destWriter: {
	#path:   _
	command: "cp" | "mv" | "ln" | "install"
	targets: or([for n in list.Range(0, 8, 1) {list.Concat([list.Repeat([string], n), [#path]])}])
} | {
	#path:   _
	command: "cp" | "mv" | "ln" | "install"
	argument_pairs: list.MatchN(>0, {first: "-t" | "--target-directory", second: #path, ...})
}

_denyProtected: {
	rule_id:  "protected-path"
	reason:   "Protected path (/etc, ~/.ssh): ask the user to make this change."
	severity: "HIGH"
}

protected_edit: {
	when: hook.#PreToolUse & (tool.#Edit | tool.#Write | tool.#NotebookEdit) & {
		tool_input: file_path: _protectedPath
	}
	then: deny: _denyProtected
}

protected_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: edits: list.MatchN(>0, {file_path: _protectedPath, ...})
	}
	then: deny: _denyProtected
}

protected_bash_write: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: _anyTargetWriter, targets: list.MatchN(>0, _protectedPath)} |
			(_destWriter & {#path: _protectedPath})
	})
	then: deny: _denyProtected
}

protected_bash_redirect: {
	when: hook.#PreToolUse & tool.#Bash & {
		tool_input: parsed: attributes: redirections: list.MatchN(>0, =~_redirectOutRe & _protectedPath)
	}
	then: deny: _denyProtected
}
