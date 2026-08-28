import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path

from PySide6.QtWidgets import QApplication, QPushButton

from aid.paths import matlab_code, models_dir
from aid_gui.main_window import MainWindow
from aid_gui.menus import QuickStartDialog, _on_examples, _on_quick_start

CONTROL_LEGEND_LABELS = [
    "Interactive Controls:",
    "===================",
    "Scroll - Adjust Selection/Zoom",
    "Left Click - Select/Rotate",
    "Double Click - Adjust Profile",
    "Right Click - Drag Plot/Pan",
    " -> Model - Weight/Balance",
    " -> Background - Options",
    "Center/Shift Click - Drag Part",
    "Space Key - Assign to Variable",
    "Any Other Key - Isolate Part",
    "Background Image:",
    "Scroll - Scale Image",
    "Left Click - Drag Image",
    "Right Click - Options",
]


def _help_menu(window):
    return [a for a in window.menuBar().actions() if a.text() == "Help"][0].menu()


def test_help_submenu():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    help_m = _help_menu(w)
    labels = [a.text() for a in help_m.actions() if not a.isSeparator()]
    assert "Examples" in labels and "User's Manual" in labels
    assert "Quick Start" in labels


def test_control_legend_actions_disabled():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    help_m = _help_menu(w)
    by_text: dict[str, list] = {}
    for action in help_m.actions():
        if action.isSeparator():
            continue
        by_text.setdefault(action.text(), []).append(action)
    for label in CONTROL_LEGEND_LABELS:
        assert label in by_text, f"missing legend label: {label!r}"
        for action in by_text[label]:
            assert not action.isEnabled(), f"{label!r} should be disabled"
    manual = [a for a in help_m.actions() if a.text() == "User's Manual"]
    assert manual and manual[0].isEnabled()


def test_quick_start_dialog_constructs():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    dlg = QuickStartDialog(w)
    assert "Quick Start" in dlg.windowTitle()
    blob = dlg.body_text().lower()
    assert "load" in blob and "examples" in blob
    assert "datcom" in blob and "tornado" in blob and "avl" in blob
    assert "geometry" in blob and "stability" in blob and "aerodynamics" in blob
    buttons = dlg.findChildren(QPushButton)
    labels = [b.text().lower() for b in buttons]
    assert any("manual" in t or "documentation" in t or "pdf" in t for t in labels)


def test_quick_start_menu_constructs_dialog(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    constructed = []

    class Fake:
        def __init__(self, *args, **kwargs):
            constructed.append(args)

        def exec(self):
            return 0

    monkeypatch.setattr("aid_gui.menus.QuickStartDialog", Fake)
    _on_quick_start(w)
    assert constructed


def test_examples_opens_models_dir_jsonc(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    captured = {}
    cessna = models_dir() / "Cessna 172.jsonc"

    def fake_open(parent, title, directory, filt):
        captured["dir"] = directory
        captured["filter"] = filt
        return str(cessna), filt

    monkeypatch.setattr("aid_gui.menus.QFileDialog.getOpenFileName", fake_open)
    _on_examples(w)
    start = Path(captured["dir"])
    assert start == models_dir() or start.parent == models_dir()
    assert "jsonc" in captured["filter"].lower()
    assert ".mat" not in captured["filter"].lower()
    assert w.aircraft is not None
    assert w._aircraft_stem == "Cessna 172"


def test_examples_cancel_does_not_load(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()

    monkeypatch.setattr(
        "aid_gui.menus.QFileDialog.getOpenFileName",
        lambda *a, **k: ("", ""),
    )
    _on_examples(w)
    assert w.aircraft is None


def test_users_manual_opens_pdf(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    opened = []
    monkeypatch.setattr(
        "aid_gui.menus.QDesktopServices.openUrl", lambda url: opened.append(url)
    )
    [a for a in _help_menu(w).actions() if a.text() == "User's Manual"][0].trigger()
    assert opened
    path = opened[0].toLocalFile()
    assert Path(path).name == "AID_Documentation.pdf"
    assert Path(path) == matlab_code() / "AID_Documentation.pdf"
