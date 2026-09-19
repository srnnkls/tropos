from __future__ import annotations

from dataclasses import dataclass

import pytest

from slint.chunks import Chunk, chunk_python, chunk_text
from slint.detectors import DETECTORS_BY_NAME, run_detector


@dataclass(frozen=True)
class DetectorCase:
    detector: str
    source: str
    expected_hits: int
    description: str


PYTHON_CASES = [
    DetectorCase(
        detector="staticmethod",
        source="class S:\n    @staticmethod\n    def f():\n        pass\n",
        expected_hits=1,
        description="staticmethod flagged",
    ),
    DetectorCase(
        detector="behavioral_inheritance",
        source="class Base:\n    pass\n\n\nclass Child(Base):\n    pass\n",
        expected_hits=1,
        description="behavioural base flagged",
    ),
    DetectorCase(
        detector="behavioral_inheritance",
        source="class MyError(ValueError):\n    pass\n\n\nclass P(Protocol):\n    pass\n",
        expected_hits=0,
        description="exceptions and protocols allowed",
    ),
    DetectorCase(
        detector="mutable_default_argument",
        source="def f(items=[], *, options=dict()):\n    pass\n",
        expected_hits=2,
        description="list literal and dict() defaults",
    ),
    DetectorCase(
        detector="network_call_without_timeout",
        source="import requests\n\n\ndef f(url):\n    requests.get(url)\n    requests.post(url, timeout=3)\n",
        expected_hits=1,
        description="only the call without timeout",
    ),
    DetectorCase(
        detector="blocking_io_in_async",
        source="async def f(url):\n    requests.get(url)\n    time.sleep(1)\n\n\ndef g():\n    time.sleep(1)\n",  # noqa: E501
        expected_hits=2,
        description="blocking calls inside async only",
    ),
    DetectorCase(
        detector="swallowed_exception",
        source="try:\n    risky()\nexcept Exception:\n    pass\n",
        expected_hits=1,
        description="except pass",
    ),
    DetectorCase(
        detector="positional_class_pattern",
        source=(
            "match m:\n    case Msg(None, None):\n        pass\n    case Msg(content=c):\n        pass\n"
            "    case str(s):\n        pass\n"
        ),
        expected_hits=1,
        description="positional class pattern, builtins exempt",
    ),
    DetectorCase(
        detector="section_divider_comment",
        source="# ==== Models ====\nx = 1\n# --------\n# a normal comment\n",
        expected_hits=2,
        description="divider comments",
    ),
    DetectorCase(
        detector="dict_any_parameter",
        source=(
            "def core(data: dict[str, Any]) -> None:\n    pass\n\n\n"
            "def parse_payload(data: dict[str, Any]) -> None:\n    pass\n"
        ),
        expected_hits=1,
        description="boundary parsers exempt",
    ),
    DetectorCase(
        detector="root_logger_configured",
        source="import logging\nlogging.basicConfig(level=logging.INFO)\n",
        expected_hits=1,
        description="basicConfig",
    ),
    DetectorCase(
        detector="test_class",
        source="class TestThing:\n    def test_a(self):\n        pass\n",
        expected_hits=1,
        description="test class",
    ),
    DetectorCase(
        detector="star_import",
        source="from os import *\n",
        expected_hits=1,
        description="star import",
    ),
    DetectorCase(
        detector="gather_without_error_handling",
        source=(
            "async def f():\n    await asyncio.gather(a(), b())\n"
            "    await asyncio.gather(a(), return_exceptions=True)\n"
        ),
        expected_hits=1,
        description="gather without return_exceptions",
    ),
    DetectorCase(
        detector="list_reassignment_instead_of_clear",
        source="class B:\n    def reset(self):\n        self.pending = []\n",
        expected_hits=1,
        description="reassigning instead of clear",
    ),
]


def _python_chunk(source: str) -> Chunk:
    return Chunk(
        id="x",
        file="m.py",
        kind="file",
        domain="code",
        language="python",
        text=source,
        start_line=1,
        end_line=source.count("\n") + 1,
    )


@pytest.mark.parametrize("case", PYTHON_CASES, ids=lambda c: c.description)
def test_python_detectors(case: DetectorCase):
    spec = DETECTORS_BY_NAME[case.detector]

    evidence = run_detector(spec, _python_chunk(case.source), {})

    assert len(evidence) == case.expected_hits


def test_missing_future_annotations_applies_to_module_chunks_with_imports():
    chunks = chunk_python("m.py", "import os\n\n\ndef f():\n    return os.name\n")
    module = next(chunk for chunk in chunks if chunk.kind == "module")

    evidence = run_detector(DETECTORS_BY_NAME["missing_future_annotations"], module, {})

    assert len(evidence) == 1


def test_evidence_lines_are_absolute_in_the_file():
    chunks = chunk_python("m.py", "import requests\n\n\ndef f(url):\n    return requests.get(url)\n")
    function = next(chunk for chunk in chunks if chunk.kind == "function")

    evidence = run_detector(DETECTORS_BY_NAME["network_call_without_timeout"], function, {})

    assert evidence[0].line == 5


PROSE_CASES = [
    DetectorCase(detector="em_dash", source="Fast — very fast.\n", expected_hits=1, description="em dash"),
    DetectorCase(
        detector="parenthetical",
        source="We shipped (finally) the thing.\n",
        expected_hits=1,
        description="aside",
    ),
    DetectorCase(
        detector="parenthetical",
        source="See [docs](https://example.com) now.\n",
        expected_hits=0,
        description="links exempt",
    ),
    DetectorCase(
        detector="semicolon", source="Ship it; then rest.\n", expected_hits=1, description="semicolon"
    ),
    DetectorCase(detector="exclamation", source="Great news!\n", expected_hits=1, description="exclamation"),
    DetectorCase(
        detector="second_person", source="You should read this.\n", expected_hits=1, description="you"
    ),
    DetectorCase(
        detector="first_person_plural", source="We shipped our thing.\n", expected_hits=1, description="we"
    ),
]


def _paragraph(source: str) -> Chunk:
    return Chunk(
        id="p",
        file="d.md",
        kind="paragraph",
        domain="prose",
        language="markdown",
        text=source.strip(),
        start_line=1,
        end_line=1,
    )


@pytest.mark.parametrize("case", PROSE_CASES, ids=lambda c: c.description)
def test_prose_detectors(case: DetectorCase):
    evidence = run_detector(DETECTORS_BY_NAME[case.detector], _paragraph(case.source), {})

    assert len(evidence) == case.expected_hits


def test_long_sentence_limit_comes_from_params():
    paragraph = _paragraph("One two three four five six seven eight nine ten eleven twelve.")

    default = run_detector(DETECTORS_BY_NAME["long_sentence"], paragraph, {})
    strict = run_detector(DETECTORS_BY_NAME["long_sentence"], paragraph, {"max_words": 10})

    assert default == []
    assert strict[0].message == "sentence has 12 words (limit 10)"


def test_heading_case_detectors_only_look_at_headings():
    heading = chunk_text("d.md", "# Weekly Platform Status\n\nWeekly Platform Status in a paragraph.\n")

    sentence_case = [run_detector(DETECTORS_BY_NAME["heading_not_sentence_case"], c, {}) for c in heading]
    title_case = run_detector(DETECTORS_BY_NAME["heading_not_title_case"], heading[0], {})

    assert [len(e) for e in sentence_case] == [1, 0]
    assert title_case == []
