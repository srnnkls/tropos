"""slint compiles human-written rules into a policy artifact and lints code and prose against it."""

from slint.errors import ArtifactError, CompileError, JevError, SlintError

__version__ = "0.1.0"

__all__ = ["ArtifactError", "CompileError", "JevError", "SlintError", "__version__"]
