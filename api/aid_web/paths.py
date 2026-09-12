import re
from pathlib import Path

from aid.paths import models_dir

_NAME_RE = re.compile(r"^[A-Za-z0-9._ -]+$")


class ModelPathError(ValueError):
    """Invalid model name (traversal or charset)."""


def MODELS_DIR() -> Path:
    return models_dir()


def resolve_model(name: str) -> Path:
    if ".." in name or "/" in name or "\\" in name:
        raise ModelPathError("path traversal")
    if not _NAME_RE.fullmatch(name):
        raise ModelPathError("invalid name")
    path = MODELS_DIR() / f"{name}.jsonc"
    root = MODELS_DIR().resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ModelPathError("path traversal")
    return path
