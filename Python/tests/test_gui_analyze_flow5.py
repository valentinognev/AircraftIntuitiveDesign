import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
from PySide6.QtWidgets import QApplication, QDialog
from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow


def test_run_flow5_stores_cl_table(monkeypatch):
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    monkeypatch.setattr("aid_gui.main_window.MeshDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("aid_gui.main_window.MeshDialog.values", lambda self: ("10", "10"))
    from aid import flow5_io
    fake = {"alpha": [-4.0, 0.0], "CL": [0.1, 0.2], "CD": [0.01, 0.02], "Cm": [0.0, -0.1]}
    monkeypatch.setattr(flow5_io, "run_flow5", lambda ac, mesh, **k: fake)
    monkeypatch.setattr("aid_gui.main_window.run_flow5", lambda ac, mesh, **k: fake)
    w.run_flow5(("10", "10"))
    assert "flow5" in w.last_results
    assert w.last_results["flow5"]["CL"][1] == 0.2
