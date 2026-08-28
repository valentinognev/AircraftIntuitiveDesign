import math
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow


def test_slipstream_off_uses_userdata():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    w.settings.slipstream = False
    w.stability_for_display()
    assert abs(w.aircraft.HT["dwash"] - 0.5) < 1e-9
    assert abs(w.aircraft.HT["eta"] - 0.9) < 1e-9


def test_multhopp_toggle_changes_cma():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.multhopp = True
    c1 = w.stability_for_display()["Cma"]
    w.settings.multhopp = False
    c2 = w.stability_for_display()["Cma"]
    assert c1 != c2


def test_trim_mode_one_sets_elevator_delta():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.set_trim(1, 30)
    w.apply_trim()
    delta = float(w.aircraft.E["DELTA"])
    assert delta != 0.0
    assert math.isfinite(delta)
    w.stability_for_display()
    assert float(w.aircraft.E["DELTA"]) == pytest.approx(delta)
    w.apply_trim()
    assert float(w.aircraft.E["DELTA"]) == pytest.approx(delta)
