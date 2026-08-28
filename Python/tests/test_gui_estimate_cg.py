import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")

from PySide6.QtWidgets import QApplication, QDialog

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.estimate_cg import ComponentCgDialog, column_for_surface, recompute_aero_cg
from aid_gui.main_window import MainWindow


def _act(w, *labels):
    obj = w.menuBar()
    for lab in labels[:-1]:
        obj = [a for a in obj.actions() if a.text() == lab][0].menu()
    return [a for a in obj.actions() if a.text() == labels[-1]][0]


def _window():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    return w


def test_estimate_cg_disables_aero_and_tints():
    w = _window()
    assert w._field_edits["AERO.XCG"].isEnabled()
    _act(w, "Settings", "Estimate CG").trigger()
    assert not w._field_edits["AERO.XCG"].isEnabled()
    assert not w._field_edits["AERO.WT"].isEnabled()
    assert not w._field_edits["AERO.ZCG"].isEnabled()
    assert w.view3d.missing_cg_highlights() >= 1
    _act(w, "Settings", "Estimate CG").trigger()
    assert w._field_edits["AERO.XCG"].isEnabled()
    assert w._field_edits["AERO.ZCG"].isEnabled()


def test_estimate_cg_stores_3x10_table():
    w = _window()
    _act(w, "Settings", "Estimate CG").trigger()
    data = w.aircraft.cg_data
    assert data is not None
    assert len(data) == 3
    assert all(len(row) == 10 for row in data)
    assert all(float(v) == 0.0 for row in data for v in row)
    assert w.settings.estimate_cg is True


def test_estimate_cg_two_columns_mass_weighted_xcg():
    w = _window()
    _act(w, "Settings", "Estimate CG").trigger()
    w.apply_component_cg(0, x=1.0, z=0.1, wt=2.0)
    w.apply_component_cg(1, x=5.0, z=0.3, wt=6.0)
    data = w.aircraft.cg_data
    assert float(data[0][0]) == 1.0
    assert float(data[2][0]) == 2.0
    assert float(data[0][1]) == 5.0
    assert float(data[2][1]) == 6.0
    x0 = float(w.aircraft.WG["X"])
    x1 = float(w.aircraft.HT["X"])
    z0 = float(w.aircraft.WG["Z"])
    z1 = float(w.aircraft.HT["Z"])
    wt = 8.0
    xcg = ((1.0 + x0) * 2.0 + (5.0 + x1) * 6.0) / wt
    zcg = ((0.1 + z0) * 2.0 + (0.3 + z1) * 6.0) / wt
    assert abs(float(w.aircraft.AERO["WT"]) - wt) < 1e-9
    assert abs(float(w.aircraft.AERO["XCG"]) - xcg) < 1e-9
    assert abs(float(w.aircraft.AERO["ZCG"]) - zcg) < 1e-9
    assert abs(float(w._field_edits["AERO.XCG"].text()) - xcg) < 1e-6
    assert abs(float(w._field_edits["AERO.WT"].text()) - wt) < 1e-6


def test_mac_does_not_clamp_estimated_xcg():
    w = _window()
    w._mac_checkbox.setChecked(True)
    _act(w, "Settings", "Estimate CG").trigger()
    w.apply_component_cg(0, x=1.0, z=0.0, wt=2.0)
    w.apply_component_cg(1, x=5.0, z=0.0, wt=6.0)
    x0 = float(w.aircraft.WG["X"])
    x1 = float(w.aircraft.HT["X"])
    xcg = ((1.0 + x0) * 2.0 + (5.0 + x1) * 6.0) / 8.0
    mac_te = x0 + float(w.aircraft.WG["xmac"]) + float(w.aircraft.WG["cbar"])
    assert xcg > mac_te
    assert abs(float(w.aircraft.AERO["XCG"]) - xcg) < 1e-9
    assert abs(float(w._field_edits["AERO.XCG"].text()) - xcg) < 1e-6


def test_recompute_aero_cg_formula_without_apex_on_empty_np():
    w = _window()
    w.aircraft.cg_data = [[0.0] * 10 for _ in range(3)]
    w.aircraft.cg_data[0][0] = 1.0
    w.aircraft.cg_data[2][0] = 3.0
    w.aircraft.cg_data[0][3] = 2.0
    w.aircraft.cg_data[2][3] = 1.0
    assert recompute_aero_cg(w.aircraft) is True
    x0 = float(w.aircraft.WG["X"])
    x3 = float(w.aircraft.BD["X"][0])
    wt = 4.0
    xcg = ((1.0 + x0) * 3.0 + (2.0 + x3) * 1.0) / wt
    assert abs(float(w.aircraft.AERO["XCG"]) - xcg) < 1e-9
    assert abs(float(w.aircraft.AERO["WT"]) - wt) < 1e-9


def test_estimate_cg_recomputes_on_field_edit():
    w = _window()
    _act(w, "Settings", "Estimate CG").trigger()
    w.apply_component_cg(0, x=1.0, z=0.0, wt=2.0)
    w.apply_component_cg(1, x=5.0, z=0.0, wt=6.0)
    w._field_edits["WG.X"].setText("3.0")
    w.apply_field_edit()
    x1 = float(w.aircraft.HT["X"])
    xcg = ((1.0 + 3.0) * 2.0 + (5.0 + x1) * 6.0) / 8.0
    assert abs(float(w.aircraft.WG["X"]) - 3.0) < 1e-9
    assert abs(float(w.aircraft.AERO["XCG"]) - xcg) < 1e-9


def test_estimate_cg_recomputes_on_toggle_if_weights():
    w = _window()
    w.aircraft.cg_data = [[0.0] * 10 for _ in range(3)]
    w.aircraft.cg_data[0][0] = 1.0
    w.aircraft.cg_data[2][0] = 4.0
    _act(w, "Settings", "Estimate CG").trigger()
    expected = 1.0 + float(w.aircraft.WG["X"])
    assert abs(float(w.aircraft.AERO["XCG"]) - expected) < 1e-9
    assert abs(float(w.aircraft.AERO["WT"]) - 4.0) < 1e-9
    assert abs(float(w._field_edits["AERO.XCG"].text()) - expected) < 1e-6


def test_component_cg_dialog_numeric_values():
    app = QApplication.instance() or QApplication([])
    dlg = ComponentCgDialog("Wing", defaults=(1.5, 0.25, 4.0), unit="ft")
    assert dlg.windowTitle() == "Wing Weight"
    assert dlg.values() is None
    dlg.accept()
    assert dlg.result() == QDialog.DialogCode.Accepted
    assert dlg.values() == (1.5, 0.25, 4.0)


def test_pick_part_opens_dialog_and_stores_column(monkeypatch):
    w = _window()
    _act(w, "Settings", "Estimate CG").trigger()
    constructed = []

    class Fake:
        def __init__(self, *args, **kwargs):
            constructed.append((args, kwargs))

        def exec(self):
            return QDialog.DialogCode.Accepted

        def values(self):
            return (1.0, 0.0, 2.0)

    monkeypatch.setattr("aid_gui.main_window.ComponentCgDialog", Fake)
    w.pick_estimate_cg_part("wing")
    assert constructed
    assert float(w.aircraft.cg_data[0][0]) == 1.0
    assert float(w.aircraft.cg_data[2][0]) == 2.0
    assert "XCG" in w.aircraft.WG


def test_on_mesh_picked_maps_actor_not_first_part():
    w = _window()
    _act(w, "Settings", "Estimate CG").trigger()
    picked: list[str] = []
    w.view3d.set_part_click_handler(lambda name: picked.append(name))
    parts = w.view3d._mesh_part_names
    actors = w.view3d._mesh_actor_names
    ht_idx = next(i for i, name in enumerate(parts) if name.startswith("HT"))
    assert ht_idx != 0
    w.view3d.set_pointer_xy(10.0, 10.0)
    w.view3d._on_mesh_picked(actors[ht_idx])
    w.view3d.set_pointer_xy(11.0, 10.0)
    w.view3d.finish_pick()
    assert picked == [parts[ht_idx]]
    picked.clear()

    class Unnamed:
        name = "StructuredGrid"

    w.view3d.set_pointer_xy(10.0, 10.0)
    w.view3d._on_mesh_picked(Unnamed())
    w.view3d.finish_pick()
    assert picked == []


def test_mesh_pick_ignores_pointer_drag():
    w = _window()
    _act(w, "Settings", "Estimate CG").trigger()
    picked: list[str] = []
    w.view3d.set_part_click_handler(lambda name: picked.append(name))
    parts = w.view3d._mesh_part_names
    actors = w.view3d._mesh_actor_names
    ht_idx = next(i for i, name in enumerate(parts) if name.startswith("HT"))
    w.view3d.set_pointer_xy(10.0, 10.0)
    w.view3d._on_mesh_picked(actors[ht_idx])
    assert picked == []
    w.view3d.set_pointer_xy(40.0, 50.0)
    w.view3d.finish_pick()
    assert picked == []


def test_np_tip_surface_names_map_to_extra_planform_columns(monkeypatch):
    assert column_for_surface("NP{1}tip") == 4
    assert column_for_surface("NP{2}tip") == 5
    assert column_for_surface("NP{3}tip") == 6
    assert column_for_surface("NP{1}") == 4
    w = _window()
    _act(w, "Settings", "Estimate CG").trigger()
    titles = []

    class Fake:
        def __init__(self, *args, **kwargs):
            titles.append(args[0] if args else "")

        def exec(self):
            return QDialog.DialogCode.Rejected

        def values(self):
            return None

    monkeypatch.setattr("aid_gui.main_window.ComponentCgDialog", Fake)
    w.pick_estimate_cg_part("NP{1}tip")
    assert titles == ["Wing 2"]
