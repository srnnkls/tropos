package security

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/flag"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_gitHooksPath: =~#"(^|/)\.git/hooks(/|$)"#

_catastrophicPath: =~#"^"?/\*?"?$"# |
	=~("^" + _homeRe + #"/?\*?"?$"#) |
	(=~#"^"?(/etc|/usr|/bin|/sbin|/boot|/lib|/lib64|/opt|/System|/private/etc)(/|"?$)"# &
	!~#"^"?(/usr/local|/opt/homebrew)/[^/"*]"#) |
	(=~#"^"?(/var|/private/var)(/|"?$)"# & !~#"^"?(/var|/private/var)/(tmp|folders)(/|"?$)"#)

_denyGitHooks: {
	rule_id:  "git-hooks"
	reason:   "Do not skip, disable, or edit git hooks; fix what the hook reports."
	severity: "HIGH"
}

git_no_verify: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: (flag.#option & {
			command:    "git"
			subcommand: "commit"
			#spellings: ["--no-verify", "-n"]
		}) | (flag.#option & {
			command:    "git"
			subcommand: "push" | "merge"
			#spellings: ["--no-verify"]
		})
	})
	then: deny: _denyGitHooks
}

git_hook_disable: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {
			command:   "git"
			arguments: list.MatchN(>0, =~#"(?i)^core\.hookspath(=|$)"#) & list.MatchN(0, "unset" | "get" | "--unset" | "--unset-all" | "--get" | "--get-all")
		} | {
			command: "chmod" | "rm" | "unlink" | "trash" | "mv"
			targets: list.MatchN(>0, _gitHooksPath)
		}
	})
	then: deny: _denyGitHooks
}

git_hooks_edit: {
	when: hook.#PreToolUse & (tool.#Edit | tool.#Write | tool.#MultiEdit | tool.#NotebookEdit) & {
		tool_input: file_path: _gitHooksPath
	}
	then: deny: _denyGitHooks
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
		reason:   "Recursive rm of root, home, or a system directory."
		severity: "CRITICAL"
	}
}

_denyRawDevice: {
	rule_id:  "raw-device-write"
	reason:   "Writes to a raw disk device: ask the user."
	severity: "CRITICAL"
}

dd_to_device: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: "dd", targets: list.MatchN(>0, =~#"^of=/dev/(sd|hd|nvme|vd|xvd|disk|rdisk)[a-z0-9]*"#)}
	})
	then: deny: _denyRawDevice
}

mkfs_device: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: =~#"^mkfs(\.[a-z0-9]+)?$"#, targets: list.MatchN(>0, =~#"^/dev/"#)}
	})
	then: deny: _denyRawDevice
}

git_add_secret: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {
			command:    "git"
			subcommand: "add"
			targets:    list.MatchN(>0, _secretFile)
		}
	})
	then: deny: {
		rule_id:  "git-add-secret"
		reason:   "Secret file: do not stage it; add it to .gitignore."
		severity: "HIGH"
	}
}

git_add_all: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: (flag.#option & {command: "git", subcommand: "add", #spellings: ["-A", "--all", "-u", "--update"]}) |
			{command: "git", subcommand: "add", targets: list.MatchN(>0, =~#"^(\./?|:/?)$"#)} |
			(flag.#option & {command: "git", subcommand: "commit", #spellings: ["-a", "--all"]})
	})
	then: deny: {
		rule_id:  "git-add-all"
		reason:   "Stage named paths: `git add <path>…`."
		severity: "MEDIUM"
	}
}

_gitPathLike: =~#"^\.{1,2}(/|$)|\.[A-Za-z][A-Za-z0-9]{0,7}$"#

git_discard_uncommitted: {
	_ref: !~"^-" & !~"^(HEAD|@)$"

	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {
			command:     "git"
			subcommand!: "checkout"
			arguments:   list.MatchN(>0, "--")
			flags:       list.MatchN(0, "--ours" | "--theirs")
			argument_pairs: list.MatchN(0, {first: _ref & !="checkout", second: "--", ...})
		} |
			{
				command:     "git"
				subcommand!: "checkout"
				arguments:   list.MatchN(0, "--")
				flags:       list.MatchN(0, "-b" | "-B" | "--orphan" | "--ours" | "--theirs")
				targets:     list.MatchN(>0, _gitPathLike)
			} |
			{command: "git", subcommand!: "checkout" | "switch", flags: list.MatchN(>0, "-f" | "--force" | "--discard-changes")} |
			{command: "git", subcommand!: "reset", flags: list.MatchN(>0, "--hard")} |
			{command: "git", subcommand!: "clean", flags: list.MatchN(>0, "-f" | "--force")} |
			{
				command:     "git"
				subcommand!: "restore"
				flags:       list.MatchN(0, "--staged" | "-S") | list.MatchN(>0, "--worktree" | "-W")
				argument_pairs: list.MatchN(0, {first: "--source" | "-s", second: _ref, ...})
			}
	})
	then: deny: {
		rule_id:  "git-discard-uncommitted"
		reason:   "Discards uncommitted changes. To split commits, stage hunks (`henia show git/reference/commands.md#hunk-level-staging`); submodule gitlink: `git update-index --skip-worktree <path>`."
		severity: "HIGH"
	}
}
