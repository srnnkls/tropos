package guidance

import (
	"list"
	"strings"

	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_slashFile: =~#"\.(go|rs|ts|tsx|js|jsx|mjs|cjs|c|h|cc|cpp|hpp|java|cue|kdl|kt|kts|scala|swift|dart|php|cs|proto|zig)$"#
_hashFile:  =~#"\.(py|sh|bash|zsh|fish|rb|pl|r|jl|nix|tf|ps1)$"#
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
_hashLint:  =~("(?i)" + _hashLintRe)
_dashLint:  =~("(?i)" + _dashLintRe)

_slashAddedBlock: =~#"(?m)(^\+[ \t]*//[^\n]*\n\+[ \t]*//|^\+[ \t]*/\*\*?[ \t]*$)"#
_hashAddedBlock:  =~#"(?m)^\+[ \t]*#[^!\n][^\n]*\n\+[ \t]*#"#
_semiAddedBlock:  =~#"(?m)^\+[ \t]*;[^\n]*\n\+[ \t]*;"#
_dashAddedBlock:  =~#"(?m)^\+[ \t]*--[^\n]*\n\+[ \t]*--"#

_slashAddedLint: =~(#"(?im)^\+[^\n]*"# + _slashLintRe)
_hashAddedLint:  =~(#"(?im)^\+[^\n]*"# + _hashLintRe)
_dashAddedLint:  =~(#"(?im)^\+[^\n]*"# + _dashLintRe)

_addedLines: {
	#old:      string
	#new:      string
	_oldLines: strings.Split(#old, "\n")
	out: strings.Join([for l in strings.Split(#new, "\n") if !list.Contains(_oldLines, l) {l}], "\n")
}

_editAdded: {
	#file: _
	#text: _
	out: hook.#PreToolUse & tool.#Edit & {
		tool_input: matchN(1, [{
			file_path:  #file
			old_string: string
			new_string: string
			_added: (_addedLines & {#old: old_string, #new: new_string}).out & #text
			...
		}])
	}
}

_multiEditAdded: {
	#file: _
	#text: _
	out: hook.#PreToolUse & tool.#MultiEdit & {
		tool_input: {
			file_path: #file
			edits: list.MatchN(>0, {
				old_string: string
				new_string: string
				_added: (_addedLines & {#old: old_string, #new: new_string}).out & #text
				...
			})
		}
	}
}

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
	text:    "Comment block added. Delete it unless it records a hidden constraint, a non-obvious invariant, a workaround with an issue link, or an external quirk with a source, and neither a name nor a test can carry it."
}

_injectLint: {
	rule_id: "lint-suppression"
	channel: "agent"
	text:    "Lint suppression added. Fix the cause instead. Keep it only for an external-tool defect, naming the tool, rule and issue in the directive."
}

slash_comment_block_edit: {
	when: (_editAdded & {#file: _slashFile, #text: _slashBlock}).out
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
	when: (_multiEditAdded & {#file: _slashFile, #text: _slashBlock}).out
	then: inject: _injectComment
}

hash_comment_block_edit: {
	when: (_editAdded & {#file: _hashFile, #text: _hashBlock}).out
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
	when: (_multiEditAdded & {#file: _hashFile, #text: _hashBlock}).out
	then: inject: _injectComment
}

semi_comment_block_edit: {
	when: (_editAdded & {#file: _semiFile, #text: _semiBlock}).out
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
	when: (_multiEditAdded & {#file: _semiFile, #text: _semiBlock}).out
	then: inject: _injectComment
}

dash_comment_block_edit: {
	when: (_editAdded & {#file: _dashFile, #text: _dashBlock}).out
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
	when: (_multiEditAdded & {#file: _dashFile, #text: _dashBlock}).out
	then: inject: _injectComment
}

slash_lint_suppression_edit: {
	when: (_editAdded & {#file: _slashFile, #text: _slashLint}).out
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
	when: (_multiEditAdded & {#file: _slashFile, #text: _slashLint}).out
	then: inject: _injectLint
}

hash_lint_suppression_edit: {
	when: (_editAdded & {#file: _hashFile, #text: _hashLint}).out
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
	when: (_multiEditAdded & {#file: _hashFile, #text: _hashLint}).out
	then: inject: _injectLint
}

dash_lint_suppression_edit: {
	when: (_editAdded & {#file: _dashFile, #text: _dashLint}).out
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
	when: (_multiEditAdded & {#file: _dashFile, #text: _dashLint}).out
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
