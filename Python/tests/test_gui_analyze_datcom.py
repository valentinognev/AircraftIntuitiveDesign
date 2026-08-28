import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow


def test_run_datcom_populates_cl():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.run_datcom()
    assert "cl" in w.last_results["datcom"]
    assert len(w.last_results["datcom"]["cl"]) >= 3
    # AID.m GUI DATCOM (body-corrected SSPNE), not batch gold −0.1558
    assert w.last_results["datcom"]["cm"][-1] == pytest.approx(-0.1286, abs=0.01)
    datcom = w.last_results["datcom"]
    assert datcom.get("high_lift"), "DATCOM high-lift table missing (SYMFLP/ASYFLP not written?)"
    assert "epslon" in datcom
    assert datcom.get("sections")


def test_run_datcom_f16_clamps_mach_and_returns_cl(monkeypatch):
    app = QApplication.instance() or QApplication([])
    warnings, criticals = [], []

    def fake_warning(parent, title, text):
        warnings.append((title, text))
        return QMessageBox.StandardButton.Ok

    def fake_critical(parent, title, text):
        criticals.append((title, text))
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr("aid_gui.main_window.QMessageBox.warning", fake_warning)
    monkeypatch.setattr("aid_gui.main_window.QMessageBox.critical", fake_critical)
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "F-16.jsonc"), source_stem="F-16")
    w.run_datcom()
    assert "datcom" in w.last_results
    assert len(w.last_results["datcom"]["cl"]) >= 3
    assert not criticals
    assert warnings
    assert warnings[0][0] == "DATCOM"
    blob = warnings[0][1].lower()
    assert "0.6" in blob
    assert "stmach" in blob or "clamped" in blob


def test_run_avl_check_io_uses_run_avl_full(monkeypatch):
    """Inputs/Outputs preview must still retry AVL spacing (T-34C needs it)."""
    app = QApplication.instance() or QApplication([])
    full_calls = []
    previews = []

    def fake_full(ac, mesh, workdir):
        full_calls.append(tuple(mesh))
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        (workdir / "geometry.avl").write_text("AVL\n")
        (workdir / "geometry.run").write_text("CASE\n")
        (workdir / "geometry.st").write_text("ST\n")
        return {"CLa": 5.073}

    def fake_preview(parent, title, path):
        previews.append((title, Path(path).name))

    monkeypatch.setattr("aid_gui.main_window.run_avl_full", fake_full)
    monkeypatch.setattr("aid_gui.main_window.show_io_file_preview", fake_preview)
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Beechcraft T-34C.jsonc"))
    w.settings.check_io = True
    w.run_avl(mesh=("10", "10"))
    assert full_calls == [("10", "10")]
    assert w.last_results["avl"]["CLa"] == pytest.approx(5.073)
    shown = [name for _title, name in previews]
    assert "geometry.avl" in shown
    assert "geometry.run" in shown
