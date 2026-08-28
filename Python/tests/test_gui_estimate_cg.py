import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
from PySide6.QtWidgets import QApplication
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow

def _act(w, *labels):
    obj = w.menuBar()
    for lab in labels[:-1]:
        obj = [a for a in obj.actions() if a.text() == lab][0].menu()
    return [a for a in obj.actions() if a.text() == labels[-1]][0]

def test_estimate_cg_disables_aero_and_tints():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w._field_edits["AERO.XCG"].isEnabled()
    _act(w, "Settings", "Estimate CG").trigger()
    assert not w._field_edits["AERO.XCG"].isEnabled()
    assert not w._field_edits["AERO.WT"].isEnabled()
    assert w.view3d.missing_cg_highlights() >= 1
    _act(w, "Settings", "Estimate CG").trigger()
    assert w._field_edits["AERO.XCG"].isEnabled()
