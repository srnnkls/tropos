package workflow

import (
	"list"

	"github.com/srnnkls/fas/cue/hook"
	"github.com/srnnkls/fas/cue/tool"
)

task_next_after_tester: {
	when: hook.#PostToolUse & {tool_name: "Task", tool_input: subagent_type: "tester"}
	then: inject: {rule_id: "task-next-tester", channel: "agent", text: "NEXT PHASE: Dispatch implementer. Ensure the subagent invokes `/code-implement` and reads loqui guidelines for the language."}
}

task_next_after_implementer: {
	when: hook.#PostToolUse & {tool_name: "Task", tool_input: subagent_type: "implementer"}
	then: inject: {rule_id: "task-next-implementer", channel: "agent", text: "NEXT PHASE: Dispatch reviewer. Ensure the subagent invokes `/code-review` for review methodology."}
}

task_next_after_reviewer: {
	when: hook.#PostToolUse & {tool_name: "Task", tool_input: subagent_type: "reviewer"}
	then: inject: {rule_id: "task-next-reviewer", channel: "agent", text: "BATCH COMPLETE: Synthesize review feedback, fix critical/high issues, then commit and proceed to the next batch."}
}

reviewer_dispatch: {
	when: hook.#PreToolUse & {tool_name: "Task", tool_input: subagent_type: "reviewer"}
	then: inject: {rule_id: "reviewer-dispatch", channel: "agent", text: "Reviewers run in parallel: the Claude `reviewer` (Task) + ONE `peer run` (Bash, run_in_background) that fans out to the external reviewers from validation.yaml review_config. Never shell out to codex/gemini directly; read `peer run`'s manifest."}
}

todo_all_completed: {
	when: hook.#PostToolUse & tool.#TodoWrite & {
		tool_input: todos: list.MatchN(>0, {status: "completed", ...}) & list.MatchN(0, {status: !="completed", ...})
	}
	then: inject: {rule_id: "todo-all-completed", channel: "agent", text: "All tasks completed — write it back before archiving: set every finished task to `status: done` in ./scopes/<state>/<name>/tasks.yaml and refresh `meta.last_updated` / `meta.progress`, then run `scope done`. Skip if this todo list isn't scope work."}
}

todo_some_completed: {
	when: hook.#PostToolUse & tool.#TodoWrite & {
		tool_input: todos: list.MatchN(>0, {status: "completed", ...}) & list.MatchN(>0, {status: !="completed", ...})
	}
	then: inject: {rule_id: "todo-some-completed", channel: "agent", text: "Task marked completed — mirror it into ./scopes/<state>/<name>/tasks.yaml now: set that task's `status: done`, refresh `meta.last_updated` / `meta.progress` (`scope update` does this from git evidence). Skip if this todo list isn't scope work."}
}
