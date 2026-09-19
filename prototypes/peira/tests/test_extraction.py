from __future__ import annotations

from pathlib import Path

from peira.chunks import Chunk
from peira.extraction import extract_features, extract_heuristically, extract_with_jev
from peira.features import CODE_FEATURES, PROSE_FEATURES
from peira.jev import RecordingJev, ScriptedJev


def _paragraph(text: str, position: str = "body") -> Chunk:
    return Chunk(
        id=f"p{abs(hash(text))}",
        file="d.md",
        kind="paragraph",
        domain="prose",
        language="markdown",
        text=text,
        start_line=1,
        end_line=1,
        position=position,  # type: ignore[arg-type]
    )


def test_jev_extraction_asks_every_prose_feature_in_one_call():
    jev = RecordingJev(
        inner=ScriptedJev(
            script={"hedging": {"type": "score", "score": 2.4, "confidence": 0.7, "probabilities": {}}}
        )
    )

    features = extract_with_jev(_paragraph("It might perhaps be so."), jev)

    assert jev.calls == 1
    assert set(jev.log[0].questions) == {spec.name for spec in PROSE_FEATURES}
    assert features.values["hedging"].value == 2.4
    assert features.extractor == "jev"


def test_heuristic_extraction_covers_the_whole_vocabulary():
    prose = extract_heuristically(_paragraph("Plain statement. Another plain statement."))
    code = extract_heuristically(
        Chunk(
            id="c",
            file="m.py",
            kind="function",
            domain="code",
            language="python",
            text="def f():\n    pass",
            start_line=1,
            end_line=2,
        )
    )

    assert set(prose.values) == {spec.name for spec in PROSE_FEATURES}
    assert set(code.values) == {spec.name for spec in CODE_FEATURES}


def test_heuristic_extraction_scores_hedge_words():
    hedged = extract_heuristically(_paragraph("It might perhaps possibly be somewhat true, arguably."))
    plain = extract_heuristically(_paragraph("The build is green. Deploy at noon."))

    assert hedged.values["hedging"].value > plain.values["hedging"].value  # type: ignore[operator]


def test_extraction_cache_avoids_repeat_model_calls(tmp_path: Path):
    jev = RecordingJev(inner=ScriptedJev())
    chunk = _paragraph("Cache me.")

    first = extract_features([chunk], jev, tmp_path)
    second = extract_features([chunk], jev, tmp_path)

    assert (first.extracted, first.cached) == (1, 0)
    assert (second.extracted, second.cached) == (0, 1)
    assert jev.calls == 1


def test_cache_is_keyed_by_model(tmp_path: Path):
    chunk = _paragraph("Cache me.")

    extract_features([chunk], RecordingJev(inner=ScriptedJev(model="a")), tmp_path)
    other = extract_features([chunk], RecordingJev(inner=ScriptedJev(model="b")), tmp_path)

    assert other.extracted == 1
