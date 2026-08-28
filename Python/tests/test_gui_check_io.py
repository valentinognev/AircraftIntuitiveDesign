import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.io_dialogs import apply_tornado_state, format_io_preview
from aid_gui.main_window import MainWindow


def _act(w, *labels):
    obj = w.menuBar()
    for lab in labels[:-1]:
        obj = [a for a in obj.actions() if a.text() == lab][0].menu()
    return [a for a in obj.actions() if a.text() == labels[-1]][0]


def test_check_io_vlm_mode_kwarg():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.check_io = True
    w.run_tornado(mesh=("10", "5"), vlm_mode=1)
    assert w.last_results["tornado"].get("vlm_mode") == 1


def test_check_io_off_ignores_vlm_mode_kwarg():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.check_io = False
    w.run_tornado(mesh=("10", "5"), vlm_mode=1)
    assert "vlm_mode" not in w.last_results["tornado"]


def test_format_io_preview_first_twenty_lines(tmp_path: Path):
    path = tmp_path / "sample.dat"
    path.write_text("\n".join(f"line {i}" for i in range(30)))
    preview = format_io_preview(path)
    lines = preview.splitlines()
    assert len(lines) == 20
    assert lines[0] == "line 0"
    assert lines[-1] == "line 19"


def test_apply_tornado_state_overrides():
    state = {"AS": 50.0, "alpha": 0.1, "beta": 0.0}
    updated = apply_tornado_state(state, {"AS": 55.0})
    assert updated["AS"] == 55.0
    assert updated["alpha"] == 0.1


def test_settings_inputs_outputs_menu_wires_check_io():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    action = _act(w, "Settings", "Inputs/Outputs")
    assert not w.settings.check_io
    action.trigger()
    assert w.settings.check_io
    action.trigger()
    assert not w.settings.check_io
