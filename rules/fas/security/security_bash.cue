package security

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/flag"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_catastrophicPath: "/" | "~" | "$HOME" |
	=~#"^(/home|/Users)/[^/]+/?$"# |
	=~#"^(/etc|/usr|/bin|/sbin|/boot|/lib|/lib64|/opt|/System|/private/etc)(/|$)"# |
	(=~#"^(/var|/private/var)(/|$)"# & !~#"^(/var|/private/var)/(tmp|folders)(/|$)"#)

git_no_verify: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: flag.#option & {
			command:    "git"
			subcommand: "commit" | "push" | "merge"
			#spellings: ["--no-verify"]
		}
	})
	then: deny: {
		rule_id:  "git-no-verify"
		reason:   "git --no-verify is not permitted — commit/push hooks must run."
		severity: "HIGH"
	}
}

git_hook_disable: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {
			command: "git"
			argument_pairs: list.MatchN(>0, {first: =~#"(?i)^core\.hookspath$"#, second: "/dev/null", ...})
		} | {
			command: "chmod" | "rm" | "unlink" | "trash" | "mv"
			targets: list.MatchN(>0, _gitHooksPath)
		}
	})
	then: deny: {
		rule_id:  "git-hook-disable"
		reason:   "Disabling or removing git hooks is not permitted."
		severity: "HIGH"
	}
}

rm_catastrophic: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: flag.#option & flag.opt.recursive & {
			command: "rm"
			targets: list.MatchN(>0, _catastrophicPath)
		}
	})
	then: deny: {
		rule_id:  "rm-catastrophic"
		reason:   "Recursive deletion of a root, home, or critical system path is blocked."
		severity: "CRITICAL"
	}
}

dd_to_device: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: "dd", targets: list.MatchN(>0, =~#"^of=/dev/(sd|hd|nvme|vd|xvd|disk|rdisk)[a-z0-9]*"#)}
	})
	then: deny: {
		rule_id:  "dd-to-device"
		reason:   "dd writing directly to a disk device is blocked."
		severity: "CRITICAL"
	}
}

fork_bomb: {
	when: hook.#PreToolUse & tool.#Bash & {
		tool_input: command: =~#":\(\)\s*\{[^}]*:\s*\|[^}]*:[^}]*&[^}]*\}"#
	}
	then: deny: {
		rule_id:  "fork-bomb"
		reason:   "Fork bomb pattern detected."
		severity: "CRITICAL"
	}
}

mkfs_device: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: =~#"^mkfs(\.[a-z0-9]+)?$"#, targets: list.MatchN(>0, =~#"^/dev/"#)}
	})
	then: deny: {
		rule_id:  "mkfs-device"
		reason:   "mkfs on a disk device is blocked."
		severity: "CRITICAL"
	}
}

git_add_secret: {
	_dotenv:     =~#"(?i)(^|/)\.env($|\.)"#
	_credential: =~#"(?i)credentials|credential\.json"#
	_sshKey:     =~#"(?i)(^|/)id_(rsa|dsa|ecdsa|ed25519)($|\.)"#
	_pemOrKey:   =~#"(?i)\.(pem|key)$"#
	_secretBlob: =~#"(?i)(secret|token)[^/]*\.(json|ya?ml|txt)$"#
	_apiKey:     =~"(?i)api_?key"
	_secret:     _dotenv | _credential | _sshKey | _pemOrKey | _secretBlob | _apiKey

	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {
			command:    "git"
			subcommand: "add"
			targets:    list.MatchN(>0, _secret)
		}
	})
	then: deny: {
		rule_id:  "git-add-secret"
		reason:   "Refusing to stage a likely secret (.env / credentials / private key / token). Add it to .gitignore or use a secret manager."
		severity: "HIGH"
	}
}

git_add_all: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: flag.#option & {command: "git", subcommand: "add", #spellings: ["-A", "--all"]}
	})
	then: deny: {
		rule_id:  "git-add-all"
		reason:   "git add -A / --all is not permitted — stage specific paths so unintended files don't get committed."
		severity: "MEDIUM"
	}
}

_discardReason: "This discards uncommitted changes irrecoverably. To commit them separately, stage hunks from the diff instead of resetting: git diff > p.patch, filter the hunks you want, git apply --cached p.patch. A submodule gitlink is not a file — its diff is one SHA line with no hunks to stage, the commit it pointed at survives in the submodule's reflog, and `git update-index --skip-worktree <path>` hides the delta while discarding nothing. See the git skill, reference/commands.md."

git_discard_uncommitted: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: "git", subcommand: "checkout", arguments: list.MatchN(>0, "--")} |
			{command: "git", subcommand: "reset", flags: list.MatchN(>0, "--hard")} |
			{command: "git", subcommand: "clean", flags: list.MatchN(>0, "-f" | "--force")} |
			{command: "git", subcommand: "restore", flags: list.MatchN(0, "--staged" | "-S")}
	})
	then: deny: {
		rule_id:  "git-discard-uncommitted"
		reason:   _discardReason
		severity: "HIGH"
	}
}

git_checkout_tree: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: "git", subcommand: "checkout", targets: list.MatchN(>0, ".")}
	})
	then: deny: {
		rule_id:  "git-checkout-tree"
		reason:   _discardReason
		severity: "HIGH"
	}
}
