from pathlib import Path

import numpy as np

from aid.naca_ordinates import naca4_ordinates
from aid.panel_method import panel_method
from aid.panel_points import read_airfoil_file


def test_symmetric_0012_panel_alpha0_near_zero():
    xy = naca4_ordinates("0012", 81)
    out = panel_method(xy, np.linspace(-4.0, 8.0, 7))
    assert abs(out["alpha0"]) < 0.5
    assert 5.5 < out["a0"] < 7.0  # per rad, near 2*pi
    assert abs(out["Cm_ac"]) < 0.02


def test_read_airfoil_file_two_columns(tmp_path: Path):
    p = tmp_path / "foil.dat"
    p.write_text("1.0 0.0\n0.0 0.0\n1.0 0.0\n")
    xy = read_airfoil_file(p)
    assert xy.shape == (3, 2)
