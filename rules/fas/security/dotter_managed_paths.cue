package security

import (
	"list"
	"regexp"
	"strings"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/flag"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_dotterTargets: [
	".config/amethyst/amethyst.yml",
	".config/anax/config.toml",
	".config/fnox/config.toml",
	".config/fas/rules",
	".config/mise/config.toml",
	".config/zellij/config.kdl",
	".config/ripgrep/config",
	".config/opencode",
	".config/doom",
	".config/doom-legacy",
	".zshrc",
	".zshenv",
	".zfunc",
	".local/bin/emacsclient-server-edit",
	".claude/mise.toml",
	".claude/CLAUDE.md",
	".claude/settings.json",
	".claude/hooks/herdr-cwd.py",
	".claude/file-suggestion.sh",
	".claude/keybindings.json",
	".claude/commands",
	".claude/agents",
	".claude/skills",
	".codex/config.toml",
	".pi/agent/extensions",
	".pi/agent/settings/pi-vertex.json",
	".pi/agent/fnox.toml",
	".pi/agent/agents",
	".pi/agent/skills",
	".pi/agent/AGENTS.md",
]

_dotterPathRe: #"(~|\$HOME|/Users/[^/]+|/home/[^/]+)/("# +
	strings.Join([for t in _dotterTargets {regexp.QuoteMeta(t)}], "|") +
	")(/|$)"

_dotterRe: "^" + _dotterPathRe

_dotterReason: "This path is managed by dotter — follow .dotter/global.toml to its owning source, then run `dotter deploy`; do not edit the deployed target."

dotter_managed_edit: {
	when: hook.#PreToolUse & (tool.#Edit | tool.#Write | tool.#NotebookEdit) & {
		tool_input: file_path: =~_dotterRe
	}
	then: deny: {
		rule_id:  "dotter-managed-path-edit"
		reason:   _dotterReason
		severity: "HIGH"
	}
}

dotter_managed_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: edits: list.MatchN(>0, {file_path: =~_dotterRe, ...})
	}
	then: deny: {
		rule_id:  "dotter-managed-path-multiedit"
		reason:   _dotterReason
		severity: "HIGH"
	}
}

_dotterRedirectRe: "^[0-9]*>>?" + _dotterPathRe

dotter_managed_bash_write: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {
			command: _writeCommands | "trash" | "rsync"
			targets: list.MatchN(>0, =~_dotterRe)
		} | (flag.#option & {
			command: "sed" | "perl"
			#spellings: ["-i"]
			targets: list.MatchN(>0, =~_dotterRe)
		})
	})
	then: deny: {
		rule_id:  "dotter-managed-path-bash"
		reason:   _dotterReason
		severity: "HIGH"
	}
}

dotter_managed_bash_redirect: {
	when: hook.#PreToolUse & tool.#Bash & {
		tool_input: parsed: attributes: redirections: list.MatchN(>0, =~_dotterRedirectRe)
	}
	then: deny: {
		rule_id:  "dotter-managed-path-redirect"
		reason:   _dotterReason
		severity: "HIGH"
	}
}
