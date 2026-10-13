package security

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_secretFile:       _secretMaterial & _publicOrTemplate & _exampleOrTestFile
_secretMaterial:   =~#"(?i)(^|[/<])(\.env|[^/]*\.env)(\.[\w-]+)?"?$|(^|[/<])id_(rsa|dsa|ecdsa|ed25519)"?$|\.(key|p12|pfx|pkcs12|jks|keystore|ppk|p8|pem)"?$|(^|[/<])(\.netrc|\.git-credentials|\.pgpass|\.pypirc)"?$|(^|[/<])\.aws/credentials"?$|(^|[/<])credentials\.json"?$"#
_publicOrTemplate: !~#"(?i)(\.(example|sample|samples|template|templ|tmpl|dist|defaults?)"?$|\.pub"?$|(^|/)([^/]*[-_.])?(cert|certificate|fullchain|chain|cacert|ca|ca[-_]bundle|bundle|public)\.pem"?$)"#

_probableSecret:     _credentialDataFile & _exampleOrTestFile
_credentialDataFile: =~#"(?i)(^|/)[^/]*(secrets?|credentials?|password|passwd|apikey|api[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token|private[_-]?key)[^/]*\.(json|ya?ml|toml|ini|cfg|conf|properties)$"#
_exampleOrTestFile:  !~#"(?i)(example|sample|template|fixture|mock|dummy|fake|placeholder|schema|baseline|(^|/)tests?/|[_.-]tests?[_.-]|\.lock$)"#

_readVerb: "cat" | "less" | "more" | "head" | "tail" | "bat" | "nl" | "tac" |
	"xxd" | "od" | "hexdump" | "strings" | "base64" | "cp" | "scp" | "rsync" |
	"grep" | "egrep" | "fgrep" | "rg" | "ag" | "awk" | "sed" | "sort" | "uniq" |
	"source" | "." | "jq" | "yq"

_denySecret: {
	rule_id:  "read-secret-file"
	reason:   "Secret file (key, .env, credential, keystore): ask the user for the value you need."
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

bash_redirect_secret_file: {
	when: hook.#PreToolUse & tool.#Bash & {
		tool_input: parsed: attributes: redirections: list.MatchN(>0, =~#"^[0-9]*<[^<]"# & _secretFile)
	}
	then: deny: _denySecret
}

_askProbableSecret: {
	rule_id:  "read-probable-secret"
	reason:   question
	question: "Possible credentials file. Read it?"
}

read_probable_secret: {
	when: hook.#PreToolUse & tool.#Read & {
		tool_input: file_path: _probableSecret
	}
	then: ask: _askProbableSecret
}

bash_read_probable_secret: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: _readVerb, targets: list.MatchN(>0, _probableSecret)}
	})
	then: ask: _askProbableSecret
}
