import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QDialog

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from aid_gui.mesh_dialog import MeshDialog


def _analyze_action(window, name: str):
    for action in window.menuBar().actions():
        if action.text() == "Analyze":
            for sub in action.menu().actions():
                if sub.text() == name:
                    return sub
    raise AssertionError(f"Analyze → {name} action not found")


def test_mesh_dialog_defaults_and_accept():
    app = QApplication.instance() or QApplication([])
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    dlg = MeshDialog(ac, "tornado")
    assert dlg.windowTitle() == "Wing Mesh Parameters"
    assert dlg.values() is None  # not yet accepted
    dlg.accept()
    assert dlg.result() == QDialog.DialogCode.Accepted
    assert dlg.values() == ("10", "5")


def test_mesh_dialog_reject_is_none():
    app = QApplication.instance() or QApplication([])
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    dlg = MeshDialog(ac, "avl")
    dlg.reject()
    assert dlg.values() is None


def test_run_tornado_cancel_skips(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))

    class Fake:
        def exec(self):
            return 0

        def values(self):
            return None

    monkeypatch.setattr("aid_gui.main_window.MeshDialog", lambda *a, **k: Fake())
    w.run_tornado()
    assert "tornado" not in w.last_results


def test_run_tornado_mesh_kwarg_skips_dialog(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    called = []
    monkeypatch.setattr("aid_gui.main_window.MeshDialog", lambda *a, **k: called.append(1))
    w.run_tornado(mesh=("10", "5"))
    assert called == []
    assert "tornado" in w.last_results


def test_menu_tornado_trigger_shows_mesh_dialog(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    constructed = []

    class Fake:
        def __init__(self, *args, **kwargs):
            constructed.append(args)

        def exec(self):
            return 0

        def values(self):
            return None

    monkeypatch.setattr("aid_gui.main_window.MeshDialog", Fake)
    _analyze_action(w, "Tornado").trigger()
    assert constructed
    assert constructed[0][1] == "tornado"
    assert "tornado" not in w.last_results


def test_mesh_dialog_flow5_defaults():
    app = QApplication.instance() or QApplication([])
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    dlg = MeshDialog(ac, "flow5")
    dlg.accept()
    assert dlg.values() == ("10", "10")


def test_menu_avl_trigger_shows_mesh_dialog(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    constructed = []

    class Fake:
        def __init__(self, *args, **kwargs):
            constructed.append(args)

        def exec(self):
            return 0

        def values(self):
            return None

    monkeypatch.setattr("aid_gui.main_window.MeshDialog", Fake)
    _analyze_action(w, "AVL").trigger()
    assert constructed
    assert constructed[0][1] == "avl"
    assert "avl" not in w.last_results
