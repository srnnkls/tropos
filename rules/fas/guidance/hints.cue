package guidance

import (
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

loqui_hint: {
	when: hook.#PreToolUse & (tool.#Edit | tool.#Write | tool.#MultiEdit) & {
		tool_input: file_path: =~#"\.(py|go|rs|sh|bash|zig|el)$"#
	}
	then: inject: {
		rule_id: "loqui-hint"
		channel: "agent"
		text:    "HINT: Use `loqui` skill for language-specific coding guidelines and best practices."
	}
}

explore_map_empty: {
	when: hook.#PostToolUse & (
		(tool.#Grep & {tool_response: numFiles: 0}) |
		(tool.#Glob & {tool_response: filenames: []}))
	then: inject: {
		rule_id: "explore-map-hint"
		channel: "agent"
		text:    "HINT: Use `gestalt map` to get a high-level overview of the codebase structure."
	}
}
