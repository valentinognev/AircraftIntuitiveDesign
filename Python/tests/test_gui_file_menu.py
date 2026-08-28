import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from aid_gui.menus import _on_load
from aid_gui.recent import remember_recent


def _file_menu(window):
    return [a for a in window.menuBar().actions() if a.text() == "File"][0].menu()


def _recent_menu(window):
    file_menu = _file_menu(window)
    recent = [a for a in file_menu.actions() if a.text() == "Recent"]
    assert recent, "File menu missing Recent"
    return recent[0].menu()


def _settings(tmp_path: Path) -> QSettings:
    return QSettings(str(tmp_path / "recent.ini"), QSettings.Format.IniFormat)


def test_file_menu_actions():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    labels = [a.text() for a in _file_menu(w).actions() if not a.isSeparator()]
    assert labels[:3] == ["New", "Load", "Save"]
    assert "Recent" in labels


def test_recent_submenu_lists_remembered_file(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    s = _settings(tmp_path)
    monkeypatch.setattr("aid_gui.recent.default_settings", lambda: s)
    cessna = models_dir() / "Cessna 172.jsonc"
    remember_recent(cessna, settings=s)
    w = MainWindow()
    labels = [a.text() for a in _recent_menu(w).actions() if not a.isSeparator()]
    assert labels == ["Cessna 172.jsonc"]


def test_recent_action_loads_aircraft(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    s = _settings(tmp_path)
    monkeypatch.setattr("aid_gui.recent.default_settings", lambda: s)
    cessna = models_dir() / "Cessna 172.jsonc"
    remember_recent(cessna, settings=s)
    w = MainWindow()
    action = [a for a in _recent_menu(w).actions() if a.text() == "Cessna 172.jsonc"][0]
    action.trigger()
    assert w.aircraft is not None
    assert w._aircraft_stem == "Cessna 172"


def test_load_records_recent(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    s = _settings(tmp_path)
    monkeypatch.setattr("aid_gui.recent.default_settings", lambda: s)
    w = MainWindow()
    cessna = models_dir() / "Cessna 172.jsonc"

    monkeypatch.setattr(
        "aid_gui.menus.QFileDialog.getOpenFileName",
        lambda *a, **k: (str(cessna), "JSONC Files (*.jsonc)"),
    )
    _on_load(w)
    labels = [a.text() for a in _recent_menu(w).actions() if not a.isSeparator()]
    assert labels == ["Cessna 172.jsonc"]
    assert w.aircraft is not None
