from __future__ import annotations


class SlintError(Exception):
    """Base for all slint failures that should surface to the user as a message, not a traceback."""


class JevError(SlintError):
    """The decision model could not be reached or rejected the request."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


class CompileError(SlintError):
    """A guide could not be turned into requirements."""


class ArtifactError(SlintError):
    """A compiled artifact is missing, corrupt or incompatible with this runtime."""
