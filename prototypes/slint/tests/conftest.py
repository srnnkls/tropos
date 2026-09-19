from __future__ import annotations

from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def examples_dir() -> Path:
    return EXAMPLES


@pytest.fixture
def writing_guide() -> Path:
    return EXAMPLES / "guides" / "writing-guide.md"


@pytest.fixture
def networking_spec() -> Path:
    return EXAMPLES / "guides" / "networking-spec.md"


@pytest.fixture
def status_update() -> Path:
    return EXAMPLES / "sources" / "status-update.md"


@pytest.fixture
def client_source() -> Path:
    return EXAMPLES / "sources" / "client.py"
