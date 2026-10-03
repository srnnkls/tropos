package preload

import (
	"list"

	"github.com/srnnkls/fas/cue/bash"
	"github.com/srnnkls/fas/cue/henia"
)

_networkClient: "curl" | "wget" | "http" | "https" | "xh" | "xhs" | "nc" | "ncat" | "socat" | "telnet"

_interpreter: "python" | "python3" | "node" | "deno" | "bun" | "ruby" | "perl" | "php" | "lua" | "Rscript" | "julia"

project_preload_network: {
	when: henia.#Project & (bash.#command & {#name: _networkClient})
	then: deny: {
		rule_id:  "project-preload-network"
		reason:   "Preloads from a project's own .henia/skills may not reach the network: a cloned repository's skill could send local data elsewhere. Move the command into the workflow, where the agent runs it."
		severity: "HIGH"
	}
}

project_preload_gh_api: {
	when: henia.#Project & (bash.#call & {#match: {command: "gh", targets: list.MatchN(>0, "api")}})
	then: deny: {
		rule_id:  "project-preload-gh-api"
		reason:   "Preloads from a project's own .henia/skills may not call gh api: it can send arbitrary requests. Use a read-only gh subcommand such as gh pr list."
		severity: "HIGH"
	}
}

project_preload_interpreter: {
	when: henia.#Project & (bash.#command & {#name: _interpreter})
	then: deny: {
		rule_id:  "project-preload-interpreter"
		reason:   "Preloads from a project's own .henia/skills may not run interpreters, whose code Henia cannot inspect."
		severity: "HIGH"
	}
}
