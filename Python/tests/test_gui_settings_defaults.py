import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid_gui.main_window import MainWindow


def _act(w, *labels):
    obj = w.menuBar()
    for lab in labels[:-1]:
        obj = [a for a in obj.actions() if a.text() == lab][0].menu()
    return [a for a in obj.actions() if a.text() == labels[-1]][0]


def test_settings_enabled_matlab_defaults():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    scale = _act(w, "Settings", "Scale A/C Size")
    assert scale.isEnabled()
    assert not _act(w, "Settings", "Estimate CG").isChecked()
    assert _act(w, "Settings", "Plot Options", "Interpolated Shading").isChecked()
    assert _act(w, "Settings", "Plot Options", "Interpolated Shading").isEnabled()
    assert not _act(w, "Settings", "Plot Options", "Transparent").isChecked()
    assert _act(w, "Settings", "Calculations", "Multhopp's Method").isChecked()
    assert not _act(w, "Settings", "Calculations", "Trim Mode").isChecked()
    assert _act(w, "Settings", "Units", "ft-lb-kts").isChecked()
    assert not _act(w, "Settings", "Units", "in-oz-ft/s").isChecked()
    assert _act(w, "Settings", "Error Check").isChecked()
    assert not _act(w, "Settings", "Inputs/Outputs").isChecked()
    trans = _act(w, "Settings", "Plot Options", "Transparent")
    trans.trigger()
    assert trans.isChecked()
