"""The semantic intermediate representation: a fixed vocabulary of k features per chunk.

Extracting these once per chunk turns the m x n rule-by-chunk judgment matrix into O(n) extraction
calls plus O(m) predicate evaluations in code. A rule that only needs features already in this
vocabulary never triggers a model call when the guide changes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from slint.chunks import Domain
from slint.jev import Choice, Noul, Question, Score
from slint.rules import FEATURE_SCHEMA_VERSION, Condition

type FeatureKind = Literal["noul", "choice", "score"]
type Polarity = Literal["bad", "good", "neutral"]


@dataclass(frozen=True, kw_only=True)
class FeatureSpec:
    name: str
    kind: FeatureKind
    domain: Domain
    polarity: Polarity
    description: str
    instructions: str
    keywords: tuple[str, ...] = ()
    options: Mapping[str, str] | None = None
    levels: tuple[str, ...] = ()

    def question(self) -> Question:
        match self.kind:
            case "noul":
                return Noul(instructions=self.instructions)
            case "choice":
                return Choice(instructions=self.instructions, criteria=dict(self.options or {}))
            case "score":
                return Score(instructions=self.instructions, criteria=self.levels)

    @property
    def midpoint(self) -> float:
        return (len(self.levels) - 1) / 2

    def violation_conditions(
        self, *, option: str | None, forbids_option: bool
    ) -> tuple[Condition, ...] | None:
        """How a rule about this feature is violated. Polarity is a property of the feature, not of the rule:
        a guide never wants more hedging, so any rule about hedging is violated when hedging is high."""
        match self.kind, self.polarity:
            case "noul", "bad":
                return (Condition(feature=self.name, op="is", value=True),)
            case "noul", "good":
                return (Condition(feature=self.name, op="is", value=False),)
            case "score", "bad":
                return (Condition(feature=self.name, op=">", value=self.midpoint),)
            case "score", "good":
                return (Condition(feature=self.name, op="<", value=self.midpoint),)
            case "choice", _:
                if option is None or option not in (self.options or {}):
                    return None
                return (Condition(feature=self.name, op="==" if forbids_option else "!=", value=option),)
        return None


PROSE_FEATURES: tuple[FeatureSpec, ...] = (
    FeatureSpec(
        name="purpose",
        polarity="neutral",
        kind="choice",
        domain="prose",
        description="the role the passage plays in the document",
        instructions="What is the primary purpose of this passage within the document?",
        keywords=("purpose", "answer", "conclusion", "summary", "introduction"),
        options={
            "answer": "Directly answers the reader's question or states the main point",
            "context": "Background, motivation or framing before the main point",
            "instruction": "Tells the reader how to do something",
            "argument": "Justifies or defends a position",
            "example": "Illustrates a point with a concrete case",
            "summary": "Recaps or concludes what came before",
            "other": "None of the above",
        },
    ),
    FeatureSpec(
        name="tone",
        polarity="neutral",
        kind="choice",
        domain="prose",
        description="the register of the writing",
        instructions="What is the tone of this passage?",
        keywords=("tone", "promotional", "marketing", "hype", "casual", "formal", "salesy"),
        options={
            "neutral": "Plain and factual",
            "formal": "Formal or academic",
            "casual": "Conversational or chatty",
            "promotional": "Salesy, hype or marketing language",
            "defensive": "Apologetic or preemptively justifying",
        },
    ),
    FeatureSpec(
        name="verbosity",
        polarity="bad",
        kind="score",
        domain="prose",
        description="how much filler the passage carries relative to its content",
        instructions="How verbose is this passage relative to what it needs to say?",
        keywords=("verbose", "concise", "wordy", "padding", "filler", "brief", "terse", "short"),
        levels=(
            "Terse: every sentence carries new information",
            "Efficient: little padding",
            "Wordy: noticeable filler, restatement or throat-clearing",
            "Padded: much of the text could be cut without losing meaning",
        ),
    ),
    FeatureSpec(
        name="hedging",
        polarity="bad",
        kind="score",
        domain="prose",
        description="how much the passage qualifies its statements",
        instructions="How much does this passage hedge or qualify its statements?",
        keywords=("hedg", "qualif", "maybe", "might", "commit", "tentative", "confident"),
        levels=(
            "None: statements are made plainly",
            "Light: an occasional qualifier",
            "Heavy: most claims carry qualifiers",
            "Evasive: the passage avoids committing to anything",
        ),
    ),
    FeatureSpec(
        name="directness",
        polarity="good",
        kind="score",
        domain="prose",
        description="how quickly the passage reaches its point",
        instructions="How directly does this passage get to its point?",
        keywords=("direct", "answer first", "lead with", "up front", "bury", "preamble", "get to the point"),
        levels=(
            "Buried: the point is missing or arrives only at the end",
            "Delayed: significant preamble before the point",
            "Prompt: the point arrives within the first sentence or two",
            "Immediate: the point is the first thing stated",
        ),
    ),
    FeatureSpec(
        name="audience_level",
        polarity="neutral",
        kind="choice",
        domain="prose",
        description="the expertise the passage assumes of its reader",
        instructions="What level of expertise does this passage assume of the reader?",
        keywords=("audience", "beginner", "expert", "reader", "novice", "assume"),
        options={
            "beginner": "Explains basics and defines all terms",
            "practitioner": "Assumes working familiarity with the domain",
            "expert": "Assumes deep specialist knowledge",
        },
    ),
    FeatureSpec(
        name="contains_repetition",
        polarity="bad",
        kind="noul",
        domain="prose",
        description="whether the passage repeats a point already made within it",
        instructions="Does this passage make the same point more than once?",
        keywords=("repeat", "repetition", "redundant", "restat"),
    ),
    FeatureSpec(
        name="contains_uncertain_claim",
        polarity="good",
        kind="noul",
        domain="prose",
        description=(
            "whether the passage makes a genuinely uncertain claim that legitimately warrants a qualifier"
        ),
        instructions="Does this passage make a claim whose truth is genuinely uncertain or contested?",
        keywords=("uncertain", "genuinely", "contested"),
    ),
    FeatureSpec(
        name="contains_unsupported_claim",
        polarity="bad",
        kind="noul",
        domain="prose",
        description="whether the passage asserts a non-obvious fact without evidence or reference",
        instructions=(
            "Does this passage assert a non-obvious factual claim without supporting evidence or a reference?"
        ),
        keywords=("evidence", "unsupported", "cite", "source", "claim", "assert"),
    ),
    FeatureSpec(
        name="uses_jargon",
        polarity="bad",
        kind="noul",
        domain="prose",
        description="whether the passage uses specialist terms or acronyms without defining them",
        instructions="Does this passage use specialist jargon or acronyms without defining them?",
        keywords=("jargon", "acronym", "define", "expand", "plain language"),
    ),
    FeatureSpec(
        name="passive_voice_heavy",
        polarity="bad",
        kind="noul",
        domain="prose",
        description="whether the passage relies mostly on passive constructions",
        instructions="Is this passage written predominantly in the passive voice?",
        keywords=("passive", "active voice"),
    ),
)

CODE_FEATURES: tuple[FeatureSpec, ...] = (
    FeatureSpec(
        name="code_purpose",
        polarity="neutral",
        kind="choice",
        domain="code",
        description="the kind of work the code unit does",
        instructions="What is the primary responsibility of this code?",
        keywords=("responsibility", "purpose"),
        options={
            "network": "Makes HTTP or other network requests",
            "io": "Reads or writes files, databases or other local I/O",
            "transform": "Pure data transformation or computation",
            "control": "Orchestration or glue between components",
            "config": "Configuration, constants or wiring",
            "test": "Test code",
            "other": "None of the above",
        },
    ),
    FeatureSpec(
        name="makes_network_call",
        polarity="neutral",
        kind="noul",
        domain="code",
        description="whether the code performs an outbound network request",
        instructions="Does this code perform an outbound network request (HTTP, socket, RPC)?",
        keywords=("network i/o", "http request", "outbound"),
    ),
    FeatureSpec(
        name="sets_explicit_timeout",
        polarity="good",
        kind="noul",
        domain="code",
        description="whether the outbound or async I/O calls in the code configure an explicit timeout",
        instructions="Do the I/O or network calls in this code configure an explicit timeout?",
        keywords=("timeout",),
    ),
    FeatureSpec(
        name="swallows_errors",
        polarity="bad",
        kind="noul",
        domain="code",
        description="whether the code catches exceptions and discards them without logging or re-raising",
        instructions=(
            "Does this code catch exceptions and silently discard them without logging or re-raising?"
        ),
        keywords=("swallow", "silently", "ignore error", "except: pass", "discard"),
    ),
    FeatureSpec(
        name="rewraps_without_context",
        polarity="bad",
        kind="noul",
        domain="code",
        description=(
            "whether the code catches an exception only to re-raise a different one without "
            "adding information"
        ),
        instructions=(
            "Does this code catch an exception and re-raise it as a different exception "
            "without adding context?"
        ),
        keywords=("re-wrap", "rewrap", "without adding context", "adding context"),
    ),
    FeatureSpec(
        name="logs_sensitive_data",
        polarity="bad",
        kind="noul",
        domain="code",
        description="whether the code writes secrets, tokens or personal data to logs or stdout",
        instructions=(
            "Does this code write secrets, credentials, tokens or personal data to logs or standard output?"
        ),
        keywords=("secret", "credential", "token", "sensitive", "pii", "personal data"),
    ),
    FeatureSpec(
        name="mutates_global_state",
        polarity="bad",
        kind="noul",
        domain="code",
        description="whether the code mutates module-level or global state",
        instructions="Does this code mutate module-level or global state?",
        keywords=("global", "singleton", "hidden dependenc", "module-level state"),
    ),
    FeatureSpec(
        name="comments_restate_code",
        polarity="bad",
        kind="noul",
        domain="code",
        description="whether comments or docstrings merely restate what the code plainly does",
        instructions="Do the comments or docstrings in this code merely restate what the code plainly does?",
        keywords=("comment", "docstring", "restate", "self-documenting"),
    ),
    FeatureSpec(
        name="names_are_descriptive",
        polarity="good",
        kind="noul",
        domain="code",
        description="whether identifiers are descriptive enough that the code needs no explanatory comments",
        instructions=(
            "Are the identifiers in this code descriptive enough that it needs no explanatory comments?"
        ),
        keywords=("naming", "good names", "descriptive name", "abbreviat", "name things", "5x"),
    ),
    FeatureSpec(
        name="class_is_namespace",
        polarity="bad",
        kind="noul",
        domain="code",
        description=(
            "whether a class exists only to group functions or constants rather than to "
            "encapsulate mutable state"
        ),
        instructions=(
            "Does this code define a class that exists only to group functions or constants, "
            "with no mutable state shared across its methods?"
        ),
        keywords=(
            "namespace",
            "namespacing",
            "classes only",
            "mutable state",
            "class as",
            "module functions",
        ),
    ),
    FeatureSpec(
        name="untyped_data_in_core",
        polarity="bad",
        kind="noul",
        domain="code",
        description=(
            "whether the code passes untyped dictionaries or raw input deep into its logic "
            "instead of parsing at the boundary"
        ),
        instructions=(
            "Does this code pass untyped dictionaries or raw external input into its core logic "
            "instead of parsing it into typed values at the boundary?"
        ),
        keywords=("dict[str, any]", "parse", "boundary", "validate", "typed", "stringly"),
    ),
    FeatureSpec(
        name="duplicates_dependency_validation",
        polarity="bad",
        kind="noul",
        domain="code",
        description="whether the code re-checks conditions that a called dependency already guarantees",
        instructions=(
            "Does this code re-validate conditions that the libraries or functions it calls "
            "already guarantee?"
        ),
        keywords=("trust", "delegation", "duplicate validation", "duplicate validat", "already do"),
    ),
)

ALL_FEATURES: Mapping[str, FeatureSpec] = {spec.name: spec for spec in (*PROSE_FEATURES, *CODE_FEATURES)}


def features_for(domain: Domain) -> tuple[FeatureSpec, ...]:
    return PROSE_FEATURES if domain == "prose" else CODE_FEATURES


@dataclass(frozen=True, kw_only=True)
class FeatureValue:
    """One extracted feature: a probability (noul), an option name (choice) or a level position (score)."""

    value: float | str
    confidence: float
    probabilities: Mapping[str, float]


type Extractor = Literal["jev", "heuristic"]


@dataclass(frozen=True, kw_only=True)
class ChunkFeatures:
    chunk_id: str
    domain: Domain
    extractor: Extractor
    model: str
    schema_version: str = FEATURE_SCHEMA_VERSION
    values: Mapping[str, FeatureValue]

    def get(self, name: str) -> FeatureValue | None:
        return self.values.get(name)
