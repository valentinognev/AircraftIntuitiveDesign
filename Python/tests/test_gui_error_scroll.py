import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from aid_gui.tabs import clamp_value, nudge_field


def test_error_check_clamps_length():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.error_check = True
    w.settings.error_limits = (999.0, 89.0, 0.0)
    assert clamp_value(w, "WG.CHRDR", 5000) == 999.0
    w.settings.error_check = False
    assert clamp_value(w, "WG.CHRDR", 5000) == 5000.0


def test_nudge_length_uses_scroll_delta():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.scroll_delta = 0.5
    edit = w._field_edits["WG.CHRDR"]
    nudge_field(w, edit, +1)
    assert float(edit.text()) == 2.5


def test_error_check_zero_positions_unclamped():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.error_check = True
    w.settings.error_limits = (999.0, 89.0, 0.0)
    assert clamp_value(w, "WG.SSPNOP", 0) == 0
    assert clamp_value(w, "WG.Y", 0) == 0
