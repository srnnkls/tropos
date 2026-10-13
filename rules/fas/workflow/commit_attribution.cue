package workflow

import (
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_aiAttribution: #"(?i)(co-authored-by:[^\n]*(claude|anthropic|codex|openai)|noreply@anthropic\.com|generated with \[?claude)"#

commit_attribution: {
	when: hook.#PreToolUse & tool.#Bash & {
		tool_input: command: =~_aiAttribution & =~#"\b(git (commit|commit-tree|tag)|gh (pr|issue) (create|edit))\b"#
	}
	then: deny: {
		rule_id:  "commit-attribution"
		reason:   "Remove AI attribution (assistant Co-Authored-By trailer, 'Generated with' line) and rerun; do not copy trailers from history."
		severity: "MEDIUM"
	}
}
