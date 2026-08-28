import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow


def test_aero_mach_and_sspn():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert abs(w.field_value("AERO.MACH") - 0.03) < 1e-9
    assert abs(w.field_value("WG.SSPN") - 6.0) < 1e-9


def test_da20_load_skips_missing_optional_keys():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "DA20-C1.jsonc"))
    assert abs(w.field_value("AERO.MACH") - 0.09) < 1e-9
    assert abs(w.field_value("WG.SSPN") - 17.8333) < 1e-9
    assert "BD.ITYPE" not in w._field_edits
    assert "BD.N[0]" in w._field_edits
