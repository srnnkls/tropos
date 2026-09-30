package guidance

import (
	"list"
	"strings"

	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_slashFile: =~#"\.(go|rs|ts|tsx|js|jsx|mjs|cjs|c|h|cc|cpp|hpp|java|cue|kdl|kt|kts|scala|swift|dart|php|cs|proto|zig)$"#
_hashFile:  =~#"\.(py|sh|bash|zsh|fish|toml|yaml|yml|rb|pl|r|jl|nix|tf|ps1)$"#
_semiFile:  =~#"\.(el|lisp|lsp|cl|clj|cljs|cljc|edn|scm|ss|rkt|fnl)$"#
_dashFile:  =~#"\.(lua|sql|hs|lhs|elm|applescript)$"#

_slashBlock: =~#"(?m)(^[ \t]*//[^\n]*\n[ \t]*//|/\*\*?[ \t]*$)"#
_hashBlock:  =~#"(?m)^[ \t]*#[^!\n][^\n]*\n[ \t]*#"#
_semiBlock:  =~#"(?m)^[ \t]*;[^\n]*\n[ \t]*;"#
_dashBlock:  =~#"(?m)^[ \t]*--[^\n]*\n[ \t]*--"#

_slashLintRe: #"(//|/\*)[ \t]*(eslint-disable|@ts-ignore|@ts-expect-error|@ts-nocheck|prettier-ignore|biome-ignore|nolint|istanbul ignore|[cv]8 ignore|stylelint-disable)"#
_hashLintRe:  #"#[ \t]*(noqa|type:[ \t]*ignore|pylint:|pyright:|mypy:|ruff:|fmt:[ \t]*(on|off)|nosec|flake8:|pragma:[ \t]*no|shellcheck[ \t]+disable|rubocop:|yamllint|tflint-ignore)"#
_dashLintRe:  #"--+[ \t]*(luacheck:|noqa|@diagnostic|stylua:|sqlfluff:)"#

_slashLint: =~("(?i)" + _slashLintRe)
_hashLint: =~("(?i)" + _hashLintRe)
_dashLint: =~("(?i)" + _dashLintRe)

_slashAddedBlock: =~#"(?m)(^\+[ \t]*//[^\n]*\n\+[ \t]*//|^\+[ \t]*/\*\*?[ \t]*$)"#
_hashAddedBlock:  =~#"(?m)^\+[ \t]*#[^!\n][^\n]*\n\+[ \t]*#"#
_semiAddedBlock:  =~#"(?m)^\+[ \t]*;[^\n]*\n\+[ \t]*;"#
_dashAddedBlock:  =~#"(?m)^\+[ \t]*--[^\n]*\n\+[ \t]*--"#

_slashAddedLint: =~(#"(?im)^\+[^\n]*"# + _slashLintRe)
_hashAddedLint: =~(#"(?im)^\+[^\n]*"# + _hashLintRe)
_dashAddedLint: =~(#"(?im)^\+[^\n]*"# + _dashLintRe)

_bashAdded: {
	#file: _
	#text: _
	out: hook.#PostToolUse & tool.#Bash & {
		tool_response: bashEditDiff: files: list.MatchN(>0, {
			filePath: #file
			hunks: list.MatchN(>0, {
				lines: [...string]
				_text: strings.Join(lines, "\n") & #text
			})
		})
	}
}

_bashWrites: {
	#file: _
	#text: _
	out: hook.#PreToolUse & tool.#Bash & {
		tool_input: {
			command: #text
			parsed: attributes: redirections: list.MatchN(>0, =~#"^[0-9&]*>[>|]?"# & #file)
		}
	}
}

_denyComment: {
	rule_id:  "comment-block"
	reason:   _injectComment.text
	severity: "MEDIUM"
}

_denyLint: {
	rule_id:  "lint-suppression"
	reason:   _injectLint.text
	severity: "MEDIUM"
}

_injectComment: {
	rule_id: "comment-block"
	channel: "agent"
	text: """
		STOP — delete this comment block. House style (AGENTS.md → Comments & Documentation) forbids comment blocks; the default answer is DELETE, not justify.
		Before you keep ANY of it, the burden is on you to pass all three, out loud: (1) name the exact category — hidden constraint / non-obvious invariant / workaround tied to a NAMED bug+issue / external quirk with a NAMED source; nothing else exists. (2) Show why a better NAME cannot carry it. (3) Show why a TEST cannot pin it.
		There is NO length exception — collapsing the block to a single line does not redeem it. The bar is the category test above, not brevity. Fail it → delete, whatever the length.
		Fail any step, or find yourself reaching for words like "load-bearing", "subtle", "important to note", "for clarity", or any defense of your own choices → that IS the leakage; delete the whole block now and fix the name.
		Restating WHAT the code does, walkthroughs, and process narration are auto-delete — do not even evaluate them.
		"""
}

_injectLint: {
	rule_id: "lint-suppression"
	channel: "agent"
	text: """
		STOP — delete this linter directive. House style (AGENTS.md → Comments & Documentation) bans non-technical comments, suppressions, and pragmas (# noqa, # type: ignore, // eslint-disable, // @ts-expect-error, # shellcheck disable, and the like).
		A suppression silences the tool instead of fixing the code. Fix the underlying issue — the type, the unused import, the real violation — so the directive is unnecessary.
		If the suppression is genuinely unavoidable, that is a NAMED external-quirk exception: state the tool, the exact rule, and why the code cannot satisfy it — out loud, before keeping it. Default is DELETE.
		"""
}

slash_comment_block_edit: {
	when: hook.#PreToolUse & tool.#Edit & {
		tool_input: file_path:  _slashFile
		tool_input: new_string: _slashBlock
	}
	then: inject: _injectComment
}

slash_comment_block_write: {
	when: hook.#PreToolUse & tool.#Write & {
		tool_input: file_path: _slashFile
		tool_input: content:   _slashBlock
	}
	then: inject: _injectComment
}

slash_comment_block_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: file_path: _slashFile
		tool_input: edits: list.MatchN(>0, {new_string: _slashBlock, ...})
	}
	then: inject: _injectComment
}

hash_comment_block_edit: {
	when: hook.#PreToolUse & tool.#Edit & {
		tool_input: file_path:  _hashFile
		tool_input: new_string: _hashBlock
	}
	then: inject: _injectComment
}

hash_comment_block_write: {
	when: hook.#PreToolUse & tool.#Write & {
		tool_input: file_path: _hashFile
		tool_input: content:   _hashBlock
	}
	then: inject: _injectComment
}

hash_comment_block_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: file_path: _hashFile
		tool_input: edits: list.MatchN(>0, {new_string: _hashBlock, ...})
	}
	then: inject: _injectComment
}

semi_comment_block_edit: {
	when: hook.#PreToolUse & tool.#Edit & {
		tool_input: file_path:  _semiFile
		tool_input: new_string: _semiBlock
	}
	then: inject: _injectComment
}

semi_comment_block_write: {
	when: hook.#PreToolUse & tool.#Write & {
		tool_input: file_path: _semiFile
		tool_input: content:   _semiBlock
	}
	then: inject: _injectComment
}

semi_comment_block_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: file_path: _semiFile
		tool_input: edits: list.MatchN(>0, {new_string: _semiBlock, ...})
	}
	then: inject: _injectComment
}

dash_comment_block_edit: {
	when: hook.#PreToolUse & tool.#Edit & {
		tool_input: file_path:  _dashFile
		tool_input: new_string: _dashBlock
	}
	then: inject: _injectComment
}

dash_comment_block_write: {
	when: hook.#PreToolUse & tool.#Write & {
		tool_input: file_path: _dashFile
		tool_input: content:   _dashBlock
	}
	then: inject: _injectComment
}

dash_comment_block_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: file_path: _dashFile
		tool_input: edits: list.MatchN(>0, {new_string: _dashBlock, ...})
	}
	then: inject: _injectComment
}

slash_lint_suppression_edit: {
	when: hook.#PreToolUse & tool.#Edit & {
		tool_input: file_path:  _slashFile
		tool_input: new_string: _slashLint
	}
	then: inject: _injectLint
}

slash_lint_suppression_write: {
	when: hook.#PreToolUse & tool.#Write & {
		tool_input: file_path: _slashFile
		tool_input: content:   _slashLint
	}
	then: inject: _injectLint
}

slash_lint_suppression_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: file_path: _slashFile
		tool_input: edits: list.MatchN(>0, {new_string: _slashLint, ...})
	}
	then: inject: _injectLint
}

hash_lint_suppression_edit: {
	when: hook.#PreToolUse & tool.#Edit & {
		tool_input: file_path:  _hashFile
		tool_input: new_string: _hashLint
	}
	then: inject: _injectLint
}

hash_lint_suppression_write: {
	when: hook.#PreToolUse & tool.#Write & {
		tool_input: file_path: _hashFile
		tool_input: content:   _hashLint
	}
	then: inject: _injectLint
}

hash_lint_suppression_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: file_path: _hashFile
		tool_input: edits: list.MatchN(>0, {new_string: _hashLint, ...})
	}
	then: inject: _injectLint
}

dash_lint_suppression_edit: {
	when: hook.#PreToolUse & tool.#Edit & {
		tool_input: file_path:  _dashFile
		tool_input: new_string: _dashLint
	}
	then: inject: _injectLint
}

dash_lint_suppression_write: {
	when: hook.#PreToolUse & tool.#Write & {
		tool_input: file_path: _dashFile
		tool_input: content:   _dashLint
	}
	then: inject: _injectLint
}

dash_lint_suppression_multiedit: {
	when: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: file_path: _dashFile
		tool_input: edits: list.MatchN(>0, {new_string: _dashLint, ...})
	}
	then: inject: _injectLint
}

slash_comment_block_bash: {
	when: (_bashAdded & {#file: _slashFile, #text: _slashAddedBlock}).out
	then: inject: _injectComment
}

hash_comment_block_bash: {
	when: (_bashAdded & {#file: _hashFile, #text: _hashAddedBlock}).out
	then: inject: _injectComment
}

semi_comment_block_bash: {
	when: (_bashAdded & {#file: _semiFile, #text: _semiAddedBlock}).out
	then: inject: _injectComment
}

dash_comment_block_bash: {
	when: (_bashAdded & {#file: _dashFile, #text: _dashAddedBlock}).out
	then: inject: _injectComment
}

slash_lint_suppression_bash: {
	when: (_bashAdded & {#file: _slashFile, #text: _slashAddedLint}).out
	then: inject: _injectLint
}

hash_lint_suppression_bash: {
	when: (_bashAdded & {#file: _hashFile, #text: _hashAddedLint}).out
	then: inject: _injectLint
}

dash_lint_suppression_bash: {
	when: (_bashAdded & {#file: _dashFile, #text: _dashAddedLint}).out
	then: inject: _injectLint
}

slash_comment_block_redirect: {
	when: (_bashWrites & {#file: _slashFile, #text: _slashBlock}).out
	then: deny: _denyComment
}

hash_comment_block_redirect: {
	when: (_bashWrites & {#file: _hashFile, #text: _hashBlock}).out
	then: deny: _denyComment
}

semi_comment_block_redirect: {
	when: (_bashWrites & {#file: _semiFile, #text: _semiBlock}).out
	then: deny: _denyComment
}

dash_comment_block_redirect: {
	when: (_bashWrites & {#file: _dashFile, #text: _dashBlock}).out
	then: deny: _denyComment
}

slash_lint_suppression_redirect: {
	when: (_bashWrites & {#file: _slashFile, #text: _slashLint}).out
	then: deny: _denyLint
}

hash_lint_suppression_redirect: {
	when: (_bashWrites & {#file: _hashFile, #text: _hashLint}).out
	then: deny: _denyLint
}

dash_lint_suppression_redirect: {
	when: (_bashWrites & {#file: _dashFile, #text: _dashLint}).out
	then: deny: _denyLint
}
