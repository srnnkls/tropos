package workflow

import (
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

_aiAttribution: #"(?i)(co-authored-by:[^\n]*(claude|anthropic|codex|openai)|noreply@anthropic\.com|generated with \[?claude)"#

commit_attribution: {
	when: hook.#PreToolUse & tool.#Bash & {
		tool_input: command: =~_aiAttribution
	}
	then: deny: {
		rule_id:  "commit-attribution"
		reason:   "Commits and PR bodies carry no AI attribution: no Co-Authored-By trailer naming an assistant, no \"Generated with\" line. The user is the sole author. Rerun the command with the attribution lines removed, and do not copy trailers seen in git history."
		severity: "MEDIUM"
	}
}
