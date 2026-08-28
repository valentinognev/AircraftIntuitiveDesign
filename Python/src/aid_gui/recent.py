from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

RECENT_MAX = 5
_KEY = "recentFiles"


def default_settings() -> QSettings:
    return QSettings("AircraftIntuitiveDesign", "AID")


def _as_list(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw] if raw else []
    return [str(p) for p in raw if p]


def recent_paths(settings: QSettings | None = None) -> list[str]:
    s = default_settings() if settings is None else settings
    out: list[str] = []
    for path in _as_list(s.value(_KEY, [])):
        if Path(path).is_file() and path not in out:
            out.append(path)
        if len(out) >= RECENT_MAX:
            break
    return out


def remember_recent(path: str | Path, settings: QSettings | None = None) -> list[str]:
    s = default_settings() if settings is None else settings
    resolved = str(Path(path).resolve())
    rest = [p for p in _as_list(s.value(_KEY, [])) if p != resolved]
    out = [resolved, *rest][:RECENT_MAX]
    s.setValue(_KEY, out)
    s.sync()
    return out
