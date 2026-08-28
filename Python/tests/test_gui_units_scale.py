# Python/tests/test_gui_units_scale.py
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

def test_units_no_scale_converts_weight_only():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    chrdr = ac.WG["CHRDR"]
    wt = float(ac.AERO["WT"])
    w.apply_units(to_in=True, scale_size=False)
    assert w.aircraft.unit == "in"
    assert w.aircraft.WG["CHRDR"] == chrdr
    assert w.aircraft.AERO["WT"] == wt / 12

def test_units_scale_size_multiplies_lengths():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    w.apply_units(to_in=True, scale_size=True)
    assert w.aircraft.unit == "in"
    assert w.aircraft.WG["CHRDR"] == 24

def test_load_resets_units_menu_from_aircraft():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    w.apply_units(to_in=True, scale_size=False)
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w.settings.action(("Units", "ft-lb-kts")).isChecked()
    assert w.aircraft.unit == "ft"
