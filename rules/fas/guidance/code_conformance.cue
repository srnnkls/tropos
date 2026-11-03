package guidance

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_sourceExt: #"\.("# + _slashExt + "|" + _hashExt + "|" + _semiExt + "|" + _dashExt + ")"

_sourceFile:     =~(_sourceExt + #""?$"#)
_sourcePatch:    =~(#"(?m)^\*\*\* (Add|Update) File: [^\n]*"# + _sourceExt + "$")
_sourceRedirect: =~#"^[0-9]*(&?>>?|>\|)"# & _sourceFile

_sourceLiteral: =~(#"[\w./-]+"# + _sourceExt + #"\b"#)
_scriptWrite:   =~#"open\([^)]*,\s*['"][wax]|write_text|write_bytes|writeFile|File\.write|\.write\("#

_inPlaceEditor: "sed" | "gsed" | "perl" | "ruby"
_targetWriter:  "tee" | "cp" | "mv" | "install" | "sd"
_interpreter:   "python" | "python3" | "node" | "bun" | "deno" | "ruby" | "perl"

_conformancePointer: "apply the `code.conformance` providers: `henia slots --inline code.conformance.<language>`"

_injectConformance: {
	rule_id: "code-conformance"
	channel: "agent"
	text:    "Source edit: unless already applied this session for this language, first " + _conformancePointer + "."
}

_injectConformanceAfter: {
	rule_id: "code-conformance"
	channel: "agent"
	text:    "Source edited: unless already applied this session for this language, " + _conformancePointer + ", then bring the edit into conformance."
}

code_conformance_edit: {
	when: hook.#PreToolUse & (tool.#Edit | tool.#Write | tool.#MultiEdit) & {tool_input: file_path: _sourceFile}
	then: inject: _injectConformance
}

code_conformance_patch: {
	when: hook.#PreToolUse & tool.#ApplyPatch & {tool_input: command: _sourcePatch}
	then: inject: _injectConformance
}

code_conformance_bash_write: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {
		#match: {command: _inPlaceEditor, flags: list.MatchN(>0, =~"^-i"), targets: list.MatchN(>0, _sourceFile)} |
			{command: _targetWriter, targets: list.MatchN(>0, _sourceFile)}
	})
	then: inject: _injectConformance
}

code_conformance_bash_redirect: {
	when: hook.#PreToolUse & tool.#Bash & {
		tool_input: parsed: attributes: redirections: list.MatchN(>0, _sourceRedirect)
	}
	then: inject: _injectConformance
}

code_conformance_bash_script: {
	when: hook.#PreToolUse & tool.#Bash & (bash.#call & {#match: {command: _interpreter}}) & {
		tool_input: command: _sourceLiteral & _scriptWrite
	}
	then: inject: _injectConformance
}

code_conformance_bash_edited: {
	when: hook.#PostToolUse & tool.#Bash & {
		tool_response: bashEditDiff: files: list.MatchN(>0, {filePath: _sourceFile, ...})
	}
	then: inject: _injectConformanceAfter
}
