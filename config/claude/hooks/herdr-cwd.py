#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from urllib.parse import quote


def osc7_current_directory(cwd: object) -> bytes | None:
    if not isinstance(cwd, str) or not os.path.isabs(cwd):
        return None
    uri = f"file://{quote(cwd, safe='/')}"
    return f"\x1b]7;{uri}\x1b\\".encode()


def main() -> int:
    if (
        os.environ.get("HERDR_ENV") != "1"
        or not os.environ.get("HERDR_SOCKET_PATH")
        or not os.environ.get("HERDR_PANE_ID")
    ):
        return 0
    try:
        payload = json.load(sys.stdin)
    except (OSError, json.JSONDecodeError):
        return 0
    if not isinstance(payload, dict) or payload.get("agent_id"):
        return 0
    cwd = payload.get("cwd")
    sequence = osc7_current_directory(cwd)
    if sequence is None or not isinstance(cwd, str):
        return 0
    try:
        with open("/dev/tty", "wb", buffering=0) as terminal:
            terminal.write(sequence)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
