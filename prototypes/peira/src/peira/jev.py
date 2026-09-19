"""Client for TypeSafe's System One API (Jev), a decision model rather than a text generator.

Jev evaluates typed questions against one state and returns typed answers. Every question in a
call is evaluated in parallel and in isolation, so the cheapest shape is one call carrying every
question the caller might need (speculative fan-out) rather than one call per question.

Wire format, from https://docs.typesafe.ai/api:

    POST {base_url}/v1/systemone
    Authorization: Bearer $TYPESAFE_API_KEY
    {"state": <str | object | array>, "model": "jev-latest", "questions": {<id>: <question>}}
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from peira.errors import JevError

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-latest"
DEFAULT_TIMEOUT_SECONDS = 30.0
RETRYABLE_STATUSES = frozenset({408, 409, 425, 429, 500, 502, 503, 504})

type JsonValue = str | int | float | bool | list["JsonValue"] | dict[str, "JsonValue"] | None
type State = str | Sequence[JsonValue] | Mapping[str, JsonValue]


@dataclass(frozen=True, kw_only=True)
class Noul:
    """A yes/no question. The answer is the probability that the answer is yes."""

    instructions: str
    criteria: Mapping[str, str] | None = None

    def to_wire(self) -> dict[str, JsonValue]:
        wire: dict[str, JsonValue] = {"type": "noul", "instructions": self.instructions}
        if self.criteria:
            wire["criteria"] = dict(self.criteria)
        return wire


@dataclass(frozen=True, kw_only=True)
class Choice:
    """Pick one option out of a named set. Descriptions may be None when names are self-explanatory."""

    instructions: str
    criteria: Mapping[str, str | None]

    def to_wire(self) -> dict[str, JsonValue]:
        return {"type": "choice", "instructions": self.instructions, "criteria": dict(self.criteria)}


@dataclass(frozen=True, kw_only=True)
class Score:
    """Rate against ordered levels, low to high. The answer is a position on that scale."""

    instructions: str
    criteria: tuple[str, ...]

    def to_wire(self) -> dict[str, JsonValue]:
        return {"type": "score", "instructions": self.instructions, "criteria": list(self.criteria)}


type Question = Noul | Choice | Score


@dataclass(frozen=True, kw_only=True)
class NoulAnswer:
    type: Literal["noul"] = "noul"
    noul: float


@dataclass(frozen=True, kw_only=True)
class ChoiceAnswer:
    type: Literal["choice"] = "choice"
    choice: str
    confidence: float
    probabilities: Mapping[str, float]


@dataclass(frozen=True, kw_only=True)
class ScoreAnswer:
    type: Literal["score"] = "score"
    score: float
    confidence: float
    probabilities: Mapping[str, float]


type Answer = NoulAnswer | ChoiceAnswer | ScoreAnswer


@dataclass(frozen=True, kw_only=True)
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True, kw_only=True)
class Response:
    model: str
    answers: Mapping[str, Answer]
    usage: Usage = field(default_factory=Usage)


def parse_answer(raw: Mapping[str, Any]) -> Answer:
    """Parse one wire answer into its typed variant. Raises JevError on unknown shapes."""
    match raw:
        case {"type": "noul", "noul": float() | int() as noul}:
            return NoulAnswer(noul=float(noul))
        case {"type": "choice", "choice": str() as choice}:
            return ChoiceAnswer(
                choice=choice,
                confidence=float(raw.get("confidence", 0.0)),
                probabilities=_parse_probabilities(raw.get("probabilities")),
            )
        case {"type": "score", "score": float() | int() as score}:
            return ScoreAnswer(
                score=float(score),
                confidence=float(raw.get("confidence", 0.0)),
                probabilities=_parse_probabilities(raw.get("probabilities")),
            )
    raise JevError(f"unrecognised answer shape: {json.dumps(raw)[:200]}")


def _parse_probabilities(raw: object) -> dict[str, float]:
    if not isinstance(raw, Mapping):
        return {}
    return {str(key): float(value) for key, value in raw.items()}


def parse_response(raw: Mapping[str, Any], *, fallback_model: str) -> Response:
    answers_raw = raw.get("answers")
    if not isinstance(answers_raw, Mapping):
        raise JevError("response has no answers object")
    usage_raw = raw.get("usage") or {}
    return Response(
        model=str(raw.get("model") or fallback_model),
        answers={str(key): parse_answer(value) for key, value in answers_raw.items()},
        usage=Usage(input_tokens=usage_raw.get("input_tokens"), output_tokens=usage_raw.get("output_tokens")),
    )


class Jev(Protocol):
    """Anything that answers a batch of typed questions about one state."""

    @property
    def model(self) -> str: ...

    def ask(self, state: State, questions: Mapping[str, Question]) -> Response: ...


@dataclass
class HttpJev:
    """Talks to the real API over urllib; retries transient failures with exponential backoff."""

    api_key: str
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = 3
    calls: int = 0
    questions_asked: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    @classmethod
    def from_env(cls, *, model: str | None = None) -> HttpJev:
        api_key = os.environ.get("TYPESAFE_API_KEY", "").strip()
        if not api_key:
            raise JevError("TYPESAFE_API_KEY is not set")
        return cls(
            api_key=api_key,
            model=model or os.environ.get("TYPESAFE_DEFAULT_MODEL", "").strip() or DEFAULT_MODEL,
            base_url=(os.environ.get("TYPESAFE_BASE_URL", "").strip() or DEFAULT_BASE_URL).rstrip("/"),
        )

    def ask(self, state: State, questions: Mapping[str, Question]) -> Response:
        if not questions:
            return Response(model=self.model, answers={})
        body = json.dumps(
            {
                "state": state,
                "model": self.model,
                "questions": {key: q.to_wire() for key, q in questions.items()},
            }
        ).encode()
        request = urllib.request.Request(
            f"{self.base_url}/v1/systemone",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "peira/0.1",
            },
        )
        raw = self._send_with_retries(request)
        response = parse_response(raw, fallback_model=self.model)
        self.calls += 1
        self.questions_asked += len(questions)
        self.input_tokens += response.usage.input_tokens or 0
        self.output_tokens += response.usage.output_tokens or 0
        return response

    def _send_with_retries(self, request: urllib.request.Request) -> dict[str, Any]:
        delay = 0.5
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as http_response:
                    return json.loads(http_response.read().decode())
            except urllib.error.HTTPError as error:
                detail = error.read().decode(errors="replace")[:500]
                if error.code not in RETRYABLE_STATUSES or attempt == self.max_retries:
                    raise JevError(f"Jev HTTP {error.code}: {detail}", status=error.code) from error
                logger.warning("Jev HTTP %s, retrying in %.1fs", error.code, delay)
            except (urllib.error.URLError, TimeoutError) as error:
                if attempt == self.max_retries:
                    raise JevError(f"Jev unreachable: {error}") from error
                logger.warning("Jev unreachable (%s), retrying in %.1fs", error, delay)
            time.sleep(delay)
            delay *= 2
        raise JevError("retry loop exhausted")  # unreachable; keeps the type checker honest


type ScriptKey = str | tuple[str, str]


@dataclass
class ScriptedJev:
    """Deterministic backend for tests and demos.

    `script` maps a question id, or a `(question_id, substring_of_state)` pair for state-dependent
    answers, to a wire-format answer. Unscripted questions get a maximally uncertain answer so
    the pipeline degrades instead of crashing.
    """

    script: Mapping[ScriptKey, Mapping[str, Any]] = field(default_factory=dict)
    model: str = "jev-scripted"
    calls: int = 0
    questions_asked: int = 0

    def ask(self, state: State, questions: Mapping[str, Question]) -> Response:
        self.calls += 1
        self.questions_asked += len(questions)
        state_text = state if isinstance(state, str) else json.dumps(state)
        return Response(
            model=self.model,
            answers={
                key: parse_answer(self._lookup(key, state_text) or neutral_answer(question))
                for key, question in questions.items()
            },
        )

    def _lookup(self, question_id: str, state_text: str) -> Mapping[str, Any] | None:
        for key, value in self.script.items():
            if isinstance(key, tuple) and key[0] == question_id and key[1] in state_text:
                return value
        return self.script.get(question_id)


def neutral_answer(question: Question) -> dict[str, Any]:
    match question:
        case Noul():
            return {"type": "noul", "noul": 0.5}
        case Choice(criteria=criteria):
            options = list(criteria)
            share = 1.0 / max(len(options), 1)
            return {
                "type": "choice",
                "choice": options[0],
                "confidence": 0.0,
                "probabilities": dict.fromkeys(options, share),
            }
        case Score(criteria=levels):
            share = 1.0 / max(len(levels), 1)
            return {
                "type": "score",
                "score": (len(levels) - 1) / 2,
                "confidence": 0.0,
                "probabilities": {str(index): share for index in range(len(levels))},
            }


@dataclass(frozen=True, kw_only=True)
class Exchange:
    state: State
    questions: Mapping[str, Question]
    response: Response


@dataclass
class RecordingJev:
    """Wraps a backend and records every exchange, for tests and `--trace`."""

    inner: Jev
    log: list[Exchange] = field(default_factory=list)

    @property
    def model(self) -> str:
        return self.inner.model

    @property
    def calls(self) -> int:
        return len(self.log)

    @property
    def questions_asked(self) -> int:
        return sum(len(exchange.questions) for exchange in self.log)

    def ask(self, state: State, questions: Mapping[str, Question]) -> Response:
        response = self.inner.ask(state, questions)
        self.log.append(Exchange(state=state, questions=dict(questions), response=response))
        return response


def jev_from_env(*, offline: bool = False, model: str | None = None) -> HttpJev | None:
    """The configured HTTP backend, or None when offline was requested or no key is set."""
    if offline or not os.environ.get("TYPESAFE_API_KEY", "").strip():
        return None
    return HttpJev.from_env(model=model)
