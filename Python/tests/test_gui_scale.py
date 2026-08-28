import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow
from aid_gui.settings import ScaleDialog


def _wing_area(wg) -> float:
    s = wg["S"]
    if isinstance(s, (list, tuple)):
        return float(s[-1])
    return float(s)


def test_apply_scale_doubles_lengths_and_recomputes_geometry():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    s0 = _wing_area(w.aircraft.WG)
    w.apply_scale(2.0)
    assert abs(w.field_value("WG.SSPN") - 12.0) < 1e-9
    assert abs(w.field_value("AERO.MACH") - 0.03) < 1e-9
    assert _wing_area(w.aircraft.WG) > s0


def test_scale_dialog_accept_and_reject():
    app = QApplication.instance() or QApplication([])
    dlg = ScaleDialog()
    dlg.accept()
    assert dlg.factor() == 1.0
    dlg = ScaleDialog()
    dlg.reject()
    assert dlg.factor() is None
