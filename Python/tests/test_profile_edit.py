import os

import numpy as np
import pytest

from aid.profile_edit import add_or_remove_point, mirror_surface, smooth_profile

def _bd():
    return {"NX": 3, "X": np.array([0.0, 1.0, 2.0]), "ZU": np.array([0.0, 0.5, 0.0]),
            "ZL": np.array([0.0, -0.4, 0.0]), "R": np.array([0.0, 0.4, 0.0])}

def test_side_insert_grows_nx():
    bd = add_or_remove_point(_bd(), 0.5, 0.2, view="side", thresh=0.01, manual=False)
    assert len(bd["X"]) == 4
    assert bd["NX"] == 4

def test_manual_click_on_station_deletes():
    bd = add_or_remove_point(_bd(), 1.0, 0.5, view="side", thresh=0.2, manual=True)
    assert len(bd["X"]) == 2

def test_mirror_upper_onto_lower():
    bd = mirror_surface(_bd(), source="upper", center=0.0)
    assert np.allclose(bd["ZL"], -bd["ZU"])

def test_flatten_sets_means():
    bd = smooth_profile(_bd(), flatten=True)
    assert np.allclose(bd["ZU"], np.mean([0.0, 0.5, 0.0]))


def test_apply_sets_body_area_to_pi_zu_squared():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QAbstractButton, QApplication

        QApplication.instance() or QApplication([])
    except Exception as exc:
        pytest.skip(f"Qt cannot start: {exc}")
    from aid_gui.profile_sketch_dialog import ProfileSketchDialog

    bd = _bd()
    bd["S"] = np.ones(2)
    dialog = ProfileSketchDialog(bd)
    dialog.show()
    add_or_remove_point(dialog.work, 0.5, 0.25, view="side", thresh=0.01, manual=False)
    dialog.sync_nx()
    assert len(dialog.work["X"]) == 4
    assert len(bd["S"]) == 2
    buttons = {b.text(): b for b in dialog.findChildren(QAbstractButton)}
    buttons["Apply"].click()
    assert len(bd["S"]) == len(bd["X"]) == 4
    assert np.allclose(bd["S"], np.pi * np.asarray(bd["ZU"], dtype=float) ** 2)
    dialog.close()


def test_dialog_apply_copies_stations():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QAbstractButton, QApplication

        QApplication.instance() or QApplication([])
    except Exception as exc:
        pytest.skip(f"Qt cannot start: {exc}")
    from aid_gui.profile_sketch_dialog import ProfileSketchDialog

    bd = _bd()
    before_zl = bd["ZL"].copy()
    dialog = ProfileSketchDialog(bd)
    dialog.show()
    buttons = {b.text(): b for b in dialog.findChildren(QAbstractButton)}
    assert {"Side", "Top", "Smooth", "Mirror upper", "Mirror lower", "Apply"} <= set(buttons)
    buttons["Mirror upper"].click()
    assert np.allclose(bd["ZL"], before_zl)
    buttons["Apply"].click()
    assert np.allclose(bd["X"], [0.0, 1.0, 2.0])
    assert np.allclose(bd["ZU"], [0.0, 0.5, 0.0])
    assert np.allclose(bd["ZL"], -bd["ZU"])
    assert np.allclose(bd["R"], [0.0, 0.4, 0.0])
    assert bd["NX"] == 3
    dialog.close()


def test_top_click_on_drawn_station_deletes_and_insert_sets_radius():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtTest import QTest
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
    except Exception as exc:
        pytest.skip(f"Qt cannot start: {exc}")
    from aid_gui.profile_sketch_dialog import ProfileSketchDialog

    dialog = ProfileSketchDialog(_bd())
    dialog.resize(480, 360)
    dialog.show()
    app.processEvents()
    assert dialog.thresh() == pytest.approx(0.1)
    px, py = dialog.data_to_pixel("top", 1.0, 0.4)
    point = QPoint(int(round(px)), int(round(py)))
    view, x, y = dialog.pixel_to_data(float(point.x()), float(point.y()))
    assert view == "top"
    assert dialog.station_at(view, x, y) is not None
    assert abs(y - 0.4) < dialog.thresh()
    QTest.mouseClick(dialog._canvas, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
    assert dialog.work["NX"] == 2
    assert np.allclose(dialog.work["X"], [0.0, 2.0])
    assert np.allclose(dialog.work["ZU"], [0.0, 0.0])
    assert np.allclose(dialog.work["ZL"], [0.0, 0.0])
    assert np.allclose(dialog.work["R"], [0.0, 0.0])
    dialog.close()

    dialog = ProfileSketchDialog(_bd())
    dialog.resize(480, 360)
    dialog.show()
    app.processEvents()
    px, py = dialog.data_to_pixel("top", 0.5, 0.15)
    point = QPoint(int(round(px)), int(round(py)))
    view, x, y = dialog.pixel_to_data(float(point.x()), float(point.y()))
    assert view == "top"
    assert dialog.station_at(view, x, y) is None
    QTest.mouseClick(dialog._canvas, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
    inserted = int(np.argmin(np.abs(dialog.work["X"] - x)))
    assert dialog.work["NX"] == 4
    assert dialog.work["R"][inserted] == pytest.approx(abs(y))
    assert np.allclose(dialog.work["ZL"], -dialog.work["ZU"])
    dialog.close()
