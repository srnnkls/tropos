from __future__ import annotations

import pytest

from peira.errors import JevError
from peira.jev import (
    Choice,
    Noul,
    RecordingJev,
    Score,
    ScriptedJev,
    neutral_answer,
    parse_answer,
    parse_response,
)


def test_noul_wire_format_omits_empty_criteria():
    assert Noul(instructions="Is it urgent?").to_wire() == {"type": "noul", "instructions": "Is it urgent?"}


def test_choice_wire_format_keeps_null_descriptions():
    wire = Choice(instructions="Tone?", criteria={"calm": None, "angry": None}).to_wire()

    assert wire == {"type": "choice", "instructions": "Tone?", "criteria": {"calm": None, "angry": None}}


def test_score_wire_format_lists_levels_in_order():
    wire = Score(instructions="Severity?", criteria=("low", "high")).to_wire()

    assert wire["criteria"] == ["low", "high"]


def test_parse_response_types_each_answer():
    raw = {
        "model": "jev-latest",
        "answers": {
            "a": {"type": "noul", "noul": 0.93},
            "b": {"type": "choice", "choice": "x", "confidence": 0.8, "probabilities": {"x": 0.9, "y": 0.1}},
            "c": {
                "type": "score",
                "score": 1.3,
                "confidence": 0.5,
                "probabilities": {"0": 0.0, "1": 0.7, "2": 0.3},
            },
        },
        "usage": {"input_tokens": 10, "output_tokens": 3},
    }

    response = parse_response(raw, fallback_model="jev")

    assert response.answers["a"].type == "noul"
    assert response.answers["b"].type == "choice"
    assert response.answers["c"].type == "score"
    assert response.usage.input_tokens == 10


def test_unknown_answer_shape_raises_jev_error():
    with pytest.raises(JevError, match="unrecognised answer shape"):
        parse_answer({"type": "essay", "text": "..."})


def test_scripted_backend_answers_by_question_id_and_state_substring():
    jev = ScriptedJev(
        script={
            "urgent": {"type": "noul", "noul": 0.1},
            ("urgent", "ASAP"): {"type": "noul", "noul": 0.95},
        }
    )

    calm = jev.ask("all fine", {"urgent": Noul(instructions="urgent?")})
    hot = jev.ask("please help ASAP", {"urgent": Noul(instructions="urgent?")})

    assert calm.answers["urgent"].type == "noul" and calm.answers["urgent"].noul == 0.1  # type: ignore[union-attr]
    assert hot.answers["urgent"].noul == 0.95  # type: ignore[union-attr]


def test_unscripted_questions_get_maximally_uncertain_answers():
    choice = neutral_answer(Choice(instructions="?", criteria={"a": None, "b": None}))
    score = neutral_answer(Score(instructions="?", criteria=("lo", "mid", "hi")))

    assert choice["confidence"] == 0.0
    assert score["score"] == 1.0


def test_recording_backend_counts_calls_and_questions():
    recorder = RecordingJev(inner=ScriptedJev())

    recorder.ask("s", {"a": Noul(instructions="a"), "b": Noul(instructions="b")})
    recorder.ask("t", {"c": Noul(instructions="c")})

    assert recorder.calls == 2
    assert recorder.questions_asked == 3
