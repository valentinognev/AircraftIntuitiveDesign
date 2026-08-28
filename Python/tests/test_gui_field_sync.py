import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from aid_gui.tabs import sync_fields_to_aircraft


def test_sync_writes_chrdr():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w._field_edits["WG.CHRDR"].setText("2.5")
    sync_fields_to_aircraft(w)
    assert w.aircraft.WG["CHRDR"] == 2.5


def test_sync_keeps_naca_as_string():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w._field_edits["HT.NACA"].setText("2412")
    sync_fields_to_aircraft(w)
    assert w.aircraft.HT["NACA"] == "2412"
    assert isinstance(w.aircraft.HT["NACA"], str)
