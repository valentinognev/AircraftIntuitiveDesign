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

def test_transparent_sets_opacity():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w.view3d.mesh_opacity() == 1.0
    _act(w, "Settings", "Plot Options", "Transparent").trigger()
    assert abs(w.view3d.mesh_opacity() - 0.3) < 1e-6
    _act(w, "Settings", "Plot Options", "Transparent").trigger()
    assert w.view3d.mesh_opacity() == 1.0

def test_show_axes_adds_actors():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    n0 = w.view3d.axis_actor_count()
    _act(w, "Settings", "Plot Options", "Show Axes").trigger()
    assert w.view3d.axis_actor_count() > n0
    assert w.view3d.is_parallel_projection() is True
    _act(w, "Settings", "Plot Options", "Show Axes").trigger()
    assert w.view3d.is_parallel_projection() is False

def test_shading_off_is_faceted():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w.view3d.smooth_shading() is True
    _act(w, "Settings", "Plot Options", "Interpolated Shading").trigger()
    assert w.view3d.smooth_shading() is False

def test_set_ac_color_red():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.settings.set_ac_color((1.0, 0.0, 0.0))
    assert w.view3d.mesh_color()[:3] == (1.0, 0.0, 0.0)

def test_project_dimensions_disables_angle():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    assert w.settings.angle is True
    _act(w, "Settings", "Plot Options", "Project Dimensions").trigger()
    assert w.settings.angle is False

def test_set_plot_res_changes_surface_count_path():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    w.load_aircraft(ac)
    n0 = w.view3d.mesh_count()
    w.settings.set_plot_res((20, 21, 11))
    w.view3d.plot_aircraft(ac, res=(20, 21, 11), angle=True)
    assert w.view3d.mesh_count() == n0
    assert w.settings.plot_res == (20, 21, 11)

def test_viz_res_changes_grid():
    from aid.viz import aircraft_surfaces
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    s_hi = aircraft_surfaces(ac, angle=True, res=(100, 101, 51))
    s_lo = aircraft_surfaces(ac, angle=True, res=(20, 21, 11))
    assert s_hi[0].x.shape[1] > s_lo[0].x.shape[1]

def test_set_plot_res_keeps_lift_overlay():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    w.set_plot_mode("Aerodynamics")
    app.processEvents()
    assert w.view3d.overlay_count() >= 2
    w.settings.set_plot_res((20, 21, 11))
    app.processEvents()
    assert w.view3d.overlay_count() >= 2
