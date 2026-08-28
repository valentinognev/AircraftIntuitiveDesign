import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
os.environ.setdefault("VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN", "1")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QImage, QKeyEvent
from PySide6.QtWidgets import QApplication, QMenu, QPushButton, QTabWidget, QWidget

from aid.aircraft import load_jsonc
from aid.paths import models_dir
from aid_gui.main_window import MainWindow


def _window():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    w.load_aircraft(load_jsonc(models_dir() / "Cessna 172.jsonc"))
    return w


def _tab_widget(w):
    tw = getattr(w, "_tab_widget", None)
    if tw is not None:
        return tw
    for child in w.findChildren(QTabWidget):
        titles = [child.tabText(i) for i in range(child.count())]
        if "Body" in titles:
            return child
    raise AssertionError("no Body tab")


def _menu_labels(menu: QMenu) -> list[str]:
    return [a.text() for a in menu.actions() if not a.isSeparator() and a.text()]


def test_view_presets_change_camera():
    w = _window()
    orig = w.view3d.camera_xyz()
    w.view3d.apply_view("Side")
    side = w.view3d.camera_xyz()
    w.view3d.apply_view("Top")
    top = w.view3d.camera_xyz()
    w.view3d.apply_view("Front")
    front = w.view3d.camera_xyz()
    assert side != orig
    assert top != side
    assert front != top
    foc = w.view3d.camera_focus()
    assert abs(side[1] - foc[1]) > abs(side[0] - foc[0])
    assert abs(top[2] - foc[2]) > abs(top[0] - foc[0])
    assert abs(front[0] - foc[0]) > abs(front[1] - foc[1])


def test_context_menu_has_reset_view_background():
    w = _window()
    menu = w.view3d.plot_context_menu()
    assert isinstance(menu, QMenu)
    labels = _menu_labels(menu)
    assert "Reset Plot" in labels
    view_menu = next(a.menu() for a in menu.actions() if a.text() == "View")
    bg_menu = next(a.menu() for a in menu.actions() if a.text() == "Background")
    assert _menu_labels(view_menu) == ["Side", "Top", "Front"]
    bg_labels = _menu_labels(bg_menu)
    assert "Load" in bg_labels and "Hide" in bg_labels


def test_isolate_then_reset_restores_visibility():
    w = _window()
    names = list(w.view3d.mesh_part_names())
    n0 = w.view3d.mesh_count()
    vis0 = w.view3d.mesh_visibility()
    assert n0 > 1
    assert all(vis0)
    w.view3d.isolate_part("wing")
    vis = w.view3d.mesh_visibility()
    assert w.view3d.mesh_count() == n0
    assert any(not shown for shown in vis)
    for shown, name in zip(vis, names, strict=True):
        if name.startswith("wing") or name in ("F", "A", "WG", "WGtip"):
            assert shown, name
        else:
            assert not shown, name
    w.view3d.reset_plot()
    assert w.view3d.mesh_count() == n0
    assert all(w.view3d.mesh_visibility())


def _assert_body_isolated(w):
    names = list(w.view3d.mesh_part_names())
    vis = w.view3d.mesh_visibility()
    assert any(not shown for shown in vis)
    for shown, name in zip(vis, names, strict=True):
        if name == "BD" or name.startswith("BD"):
            assert shown, name
        else:
            assert not shown, name


def _select_body_tab(w):
    tw = _tab_widget(w)
    body = next(i for i in range(tw.count()) if tw.tabText(i) == "Body")
    tw.setCurrentIndex(body)
    return tw


def test_isolate_hotkey_uses_selected_tab():
    w = _window()
    _select_body_tab(w)
    focused = w.focusWidget()
    if focused is not None:
        focused.clearFocus()
    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_I, Qt.KeyboardModifier.NoModifier, "i")
    w.keyPressEvent(event)
    _assert_body_isolated(w)


def test_isolate_hotkey_on_plotter_widget():
    w = _window()
    _select_body_tab(w)
    host = w.view3d.plotter_widget()
    assert isinstance(host, QWidget)
    host.setFocus()
    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_I, Qt.KeyboardModifier.NoModifier, "i")
    assert QApplication.sendEvent(host, event)
    _assert_body_isolated(w)


def test_background_load_hide_1x1_png(tmp_path):
    w = _window()
    png = tmp_path / "bg.png"
    img = QImage(1, 1, QImage.Format.Format_RGB32)
    img.fill(0xFFFFFF)
    assert img.save(str(png), "PNG")
    assert not w.view3d.background_visible()
    w.view3d.load_background(str(png))
    assert w.view3d.background_visible()
    w.view3d.hide_background()
    assert not w.view3d.background_visible()


def test_profile_dialog_writes_bd_x():
    from aid_gui.profile_sketcher import ProfileSketcherDialog

    w = _window()
    orig = [float(v) for v in w.aircraft.BD["X"]]
    dlg = ProfileSketcherDialog(w.aircraft.BD)
    dlg.set_station_value(0, "X", orig[0] + 1.25)
    dlg.apply_to(w.aircraft.BD)
    assert abs(float(w.aircraft.BD["X"][0]) - (orig[0] + 1.25)) < 1e-9
    assert abs(float(w.aircraft.BD["X"][1]) - orig[1]) < 1e-9


def test_body_tab_has_adjust_button():
    w = _window()
    tw = _tab_widget(w)
    body = next(tw.widget(i) for i in range(tw.count()) if tw.tabText(i) == "Body")
    buttons = {b.text(): b for b in body.findChildren(QPushButton)}
    assert "Adjust" in buttons
