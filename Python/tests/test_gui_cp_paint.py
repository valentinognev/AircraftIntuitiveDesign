import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")
os.environ.setdefault("VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN", "1")

pytestmark = pytest.mark.skipif(
    os.environ.get("QT_QPA_PLATFORM") != "offscreen" and not os.environ.get("DISPLAY"),
    reason="no display",
)


def test_paint_cp_adds_named_mesh():
    from PySide6.QtWidgets import QApplication

    from aid_gui.view3d import View3D

    QApplication.instance() or QApplication([])
    view = View3D()
    xyz = np.array([[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]], dtype=float)
    cp = np.array([-0.5])
    view.paint_cp(xyz, cp)
    names = [a.name for a in view._plotter.actors.values()] if hasattr(view._plotter, "actors") else []
    assert "tornado_cp" in names
    assert view.cp_painted() is True
    view.clear_cp()
    assert view.cp_painted() is False
