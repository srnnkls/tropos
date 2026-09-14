package security

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_secretFile:       _secretMaterial & _publicOrTemplate
_secretMaterial:   =~#"(?i)(^|/)(\.env|[^/]*\.env)(\.[\w-]+)?$|(^|/)id_(rsa|dsa|ecdsa|ed25519)$|\.(key|p12|pfx|pkcs12|jks|keystore|ppk|p8)$|\.pem$|(^|/)(\.netrc|\.git-credentials|\.pgpass|\.pypirc)$|(^|/)\.aws/credentials$|(^|/)credentials\.json$"#
_publicOrTemplate: !~#"(?i)(\.(example|sample|samples|template|templ|tmpl|dist|defaults?)$|\.pub$|(^|/)([^/]*[-_.])?(cert|certificate|fullchain|chain|cacert|ca|ca[-_]bundle|bundle|public)\.pem$)"#

_readVerb: "cat" | "less" | "more" | "head" | "tail" | "bat" | "nl" | "tac" |
	"xxd" | "od" | "hexdump" | "strings" | "base64" | "cp" | "scp" | "rsync" |
	"grep" | "egrep" | "fgrep" | "rg" | "ag" | "awk" | "sed" | "sort" | "uniq"

_denySecret: {
	rule_id:  "read-secret-file"
	reason:   "Reading this file is blocked — it holds secret material (private key, .env, credential, or keystore). If you need a value from it, ask the user instead of pulling raw secrets into context."
	severity: "HIGH"
}

read_secret_file: {
	when: hook.#PreToolUse & tool.#Read & {
		tool_input: file_path: _secretFile
	}
	then: deny: _denySecret
}

grep_secret_path: {
	when: hook.#PreToolUse & tool.#Grep & {
		tool_input: path: _secretFile
	}
	then: deny: _denySecret
}

bash_read_secret_file: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: _readVerb, targets: list.MatchN(>0, _secretFile)}
	})
	then: deny: _denySecret
}
_probableSecret:     _credentialDataFile & _exampleOrTestFile
_credentialDataFile: =~#"(?i)(^|/)[^/]*(secrets?|credentials?|password|passwd|apikey|api[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|private[_-]?key)[^/]*\.(json|ya?ml|toml|ini|cfg|conf|properties)$"#
_exampleOrTestFile:  !~#"(?i)(example|sample|template|fixture|mock|dummy|fake|placeholder|schema|baseline|(^|/)tests?/|[_.-]tests?[_.-]|\.lock$)"#

read_probable_secret: {
	when: hook.#PreToolUse & tool.#Read & {
		tool_input: file_path: _probableSecret
	}
	then: ask: {
		rule_id:  "read-probable-secret"
		reason:   "This file name suggests it may hold secrets."
		question: "This file looks like it could contain credentials. Read it anyway?"
	}
}
