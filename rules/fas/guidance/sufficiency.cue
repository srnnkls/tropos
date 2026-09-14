package guidance

import "github.com/srnnkls/fas/cue/hook"

sg_hardening_cutoff: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(harden(ing|ed)?|bulletproof|airtight|watertight|belt and braces|defensive|paranoid|every edge case|all edge cases|exhaustive(ly)?|permutations?|be thorough|make (it|this) robust)\b"#}
	then: inject: {
		rule_id: "sufficiency-cutoff"
		channel: "agent"
		text:    "SUFFICIENCY CUTOFF: satisfy the documented guarantees with a small set of representative falsifiers, fix confirmed reachable failures, stop. Additional permutations, observability, telemetry precision, and provenance formalism are deferred until production integration or an observed failure demands them — locally stronger code at disproportionate cost is a YAGNI violation, not thoroughness."
	}
}

sg_adversarial_finding_bar: {
	when: hook.#UserPromptSubmit & {prompt: =~#"(?i)\b(adversarial|red team|red-team|pre-?mortem|devil'?s advocate|falsif(y|ication)|poke holes|tear (it|this) apart)\b"#}
	then: inject: {
		rule_id: "adversarial-finding-bar"
		channel: "agent"
		text:    "Adversarial pass — hold each candidate to the finding bar: a REACHABLE trigger plus the WRONG OUTCOME it produces, or it is not a finding. Enumerate the whole state machine (publication, sealing, invalidation, recovery, verification) in ONE pass and report its defects together; one assertion per round is what turns a review into a spiral. Five verified findings beat forty candidates."
	}
}

sg_review_round_churn: {
	when: hook.#UserPromptSubmit & {prompt: =~"(?i)((another|next|second|third|more) (round|review|pass|iteration)|reviewer (found|says|flagged)|still (finding|flagging)|one more (issue|finding|thing to fix))"}
	then: inject: {
		rule_id: "review-round-churn"
		channel: "agent"
		text:    "Round discipline: two fix rounds per subject. A further round opens only for a verified failure mode in a component no prior round examined — never for a narrower variant of something already fixed. Batch by mechanism (sweep the whole state machine at once), and surface `needs decision:` findings to the user instead of dispatching a fix."
	}
}
