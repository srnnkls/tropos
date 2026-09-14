package workflow

import (
	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

slow_foreground_bash: {
	when: hook.#PostToolUse & hook.#MainThread & tool.#Bash & {
		duration_ms: >60000
	}
	then: inject: {
		rule_id:  "slow-foreground-bash"
		channel:  "agent"
		priority: 55
		text:     "That call held the foreground for over a minute. If you run it again — a test suite, a build, a long fetch — pass `run_in_background: true` and keep working; the harness re-invokes you when it exits. Reserve the foreground for commands whose output you need before the next decision."
	}
}
