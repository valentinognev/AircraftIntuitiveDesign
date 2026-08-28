import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from PySide6.QtCore import QSettings

from aid_gui.recent import remember_recent, recent_paths


def _settings(tmp_path: Path) -> QSettings:
    return QSettings(str(tmp_path / "recent.ini"), QSettings.Format.IniFormat)


def test_remember_puts_path_first(tmp_path: Path):
    a = tmp_path / "a.jsonc"
    b = tmp_path / "b.jsonc"
    a.write_text("{}")
    b.write_text("{}")
    s = _settings(tmp_path)
    remember_recent(a, settings=s)
    remember_recent(b, settings=s)
    assert recent_paths(settings=s) == [str(b.resolve()), str(a.resolve())]


def test_remember_duplicate_moves_to_front(tmp_path: Path):
    a = tmp_path / "a.jsonc"
    b = tmp_path / "b.jsonc"
    a.write_text("{}")
    b.write_text("{}")
    s = _settings(tmp_path)
    remember_recent(a, settings=s)
    remember_recent(b, settings=s)
    remember_recent(a, settings=s)
    assert recent_paths(settings=s) == [str(a.resolve()), str(b.resolve())]


def test_remember_caps_at_five(tmp_path: Path):
    s = _settings(tmp_path)
    paths = []
    for i in range(6):
        p = tmp_path / f"{i}.jsonc"
        p.write_text("{}")
        paths.append(p)
        remember_recent(p, settings=s)
    got = recent_paths(settings=s)
    assert len(got) == 5
    assert got[0] == str(paths[-1].resolve())
    assert str(paths[0].resolve()) not in got


def test_recent_paths_drops_missing(tmp_path: Path):
    a = tmp_path / "a.jsonc"
    b = tmp_path / "gone.jsonc"
    a.write_text("{}")
    b.write_text("{}")
    s = _settings(tmp_path)
    remember_recent(a, settings=s)
    remember_recent(b, settings=s)
    b.unlink()
    assert recent_paths(settings=s) == [str(a.resolve())]
