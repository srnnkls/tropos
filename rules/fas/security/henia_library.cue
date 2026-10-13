package security

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_heniaLibrary: =~(#"(^|/)henia/(sources|packages)(/|"?$)|^"# + _homeRe + #"/\.henia/skills(/|"?$)"#)

_denyHeniaLibrary: {
	rule_id:  "read-henia-library"
	reason:   "Read library skills with `henia show <skill>[#section]`; list them with `henia ls`."
	severity: "MEDIUM"
}

read_henia_library: {
	when: hook.#PreToolUse & tool.#Read & {
		tool_input: file_path: _heniaLibrary
	}
	then: deny: _denyHeniaLibrary
}

grep_henia_library: {
	when: hook.#PreToolUse & tool.#Grep & {
		tool_input: path: _heniaLibrary
	}
	then: deny: _denyHeniaLibrary
}

bash_read_henia_library: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: _readVerb, targets: list.MatchN(>0, _heniaLibrary)}
	})
	then: deny: _denyHeniaLibrary
}
