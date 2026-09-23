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

_phoraTargets: [
	".config/amethyst/amethyst.yml",
	".config/anax/config.toml",
	".config/fnox/config.toml",
	".config/fas",
	".config/ghostty",
	".config/herdr",
	".config/karabiner/assets/complex_modifications",
	".config/kache/config.toml",
	".config/mise/config.toml",
	".config/mise/config.local.toml",
	".config/mise/tasks",
	".config/zellij",
	".config/ripgrep/config",
	".config/claude-code-proxy",
	".config/doom",
	".config/doom-legacy",
	".config/iterm2/AppSupport/Scripts/AutoLaunch/iterm_cwd.py",
	".cargo/config.toml",
	".zshrc",
	".zshenv",
	".zfunc",
	".local/bin/emacsclient-server-edit",
	".local/bin/emacs-server-up",
	".local/bin/e",
	".local/bin/ghostty-mode",
	".local/bin/emacs-open-pwd",
	".local/bin/herdr-focused-cwd",
	".local/bin/limen",
	".local/bin/doom-legacy",
	".local/bin/emacs-legacy",
	".local/bin/peer",
	".local/bin/issue",
	".claude/mise.toml",
	".claude/CLAUDE.md",
	".claude/settings.json",
	".claude/hooks",
	".claude/file-suggestion.sh",
	".claude/keybindings.json",
	".claude/commands",
	".claude/output-styles",
	".claude/rules",
	".claude/instructions",
	".claude/agents",
	".claude/skills",
	".codex/config.toml",
	".codex/hooks.json",
	".codex/AGENTS.md",
	".codex/instructions",
	".codex/agents",
	".codex/skills",
	".omp/agent/keybindings.yml",
	".pi/agent/extensions",
	".pi/agent/settings/pi-vertex.json",
	".pi/agent/fnox.toml",
	".pi/agent/keybindings.json",
	".pi/agent/instructions",
	".pi/agent/agents",
	".pi/agent/skills",
	".pi/agent/AGENTS.md",
	"Library/LaunchAgents/com.srnnkls.claude-code-proxy.plist",
	"Library/LaunchAgents/io.code17.colorterm.plist",
]

_phoraPathRe: #"(~|\$HOME|/Users/[^/]+|/home/[^/]+)/("# +
	strings.Join([for t in _phoraTargets {regexp.QuoteMeta(t)}], "|") +
	")(/|$)"

_phoraRe: "^" + _phoraPathRe

_phoraReason: "This path is deployed by phora — edit its source in ~/dotfiles (phora.toml maps each target; Tropos skills come from the tropos repo), then run `phora sync`; do not edit the deployed target."

phora_managed_edit: {
	when: hook.#PreToolUse & (tool.#Edit | tool.#Write | tool.#NotebookEdit) & {
		tool_input: file_path: =~_phoraRe
	}
	then: deny: {
		rule_id:  "phora-managed-path-edit"
		reason:   _phoraReason
		severity: "HIGH"
	}
}

phora_managed_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: edits: list.MatchN(>0, {file_path: =~_phoraRe, ...})
	}
	then: deny: {
		rule_id:  "phora-managed-path-multiedit"
		reason:   _phoraReason
		severity: "HIGH"
	}
}

_phoraRedirectRe: "^[0-9]*>>?" + _phoraPathRe

phora_managed_bash_write: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {
			command: "tee"
			targets: list.MatchN(>0, =~_phoraRe)
		} | (flag.#option & {
			command: "sed" | "perl"
			#spellings: ["-i"]
			targets: list.MatchN(>0, =~_phoraRe)
		})
	})
	then: deny: {
		rule_id:  "phora-managed-path-bash"
		reason:   _phoraReason
		severity: "HIGH"
	}
}

phora_managed_bash_redirect: {
	when: hook.#PreToolUse & tool.#Bash & {
		tool_input: parsed: attributes: redirections: list.MatchN(>0, =~_phoraRedirectRe)
	}
	then: deny: {
		rule_id:  "phora-managed-path-redirect"
		reason:   _phoraReason
		severity: "HIGH"
	}
}
