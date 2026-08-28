import copy

import numpy as np
from aid.aircraft import load_jsonc
from aid.lifting_line import _interp1, lifting_line
from aid.paths import models_dir
from aid.viz import planform_stations


def _tapered_cessna(*, twist: float = 0.0):
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    wg = dict(ac.WG)
    wg["CHRDTP"] = 1.0
    wg["TWISTA"] = twist
    ac = copy.copy(ac)
    ac.WG = wg
    return ac


def test_tapered_wing_interp_chord_root_to_tip():
    ac = _tapered_cessna()
    y, c, _dx, _dz, _theta = planform_stations(ac.WG, 25, angle=True, kind="wing")
    y0 = float(y[-1])
    n_pts = y.size
    theta = np.arange(1, n_pts + 1) / n_pts * np.pi / 2.0
    y1 = -np.cos(theta) * y0
    y_neg = -y
    c_on_y1 = _interp1(y1, y_neg, c)
    i_root = int(np.argmin(np.abs(y1)))
    i_tip = int(np.argmax(np.abs(y1)))
    assert c_on_y1[i_root] > c_on_y1[i_tip]
    assert c_on_y1[i_root] > 1.5
    assert c_on_y1[i_tip] < 1.2


def test_tapered_wing_lifting_line_sanity():
    ac = _tapered_cessna()
    y, c, _dx, _dz, theta = planform_stations(ac.WG, 25, angle=True, kind="wing")
    out = lifting_line(ac, y, c, theta)
    assert float(out["CL"]) > 0
    assert 0.8 < float(out["e"]) <= 1.0


def test_kinked_wing_lifting_line_runs():
    ac = load_jsonc(models_dir() / "DA20-C1.jsonc")
    y, c, _dx, _dz, theta = planform_stations(ac.WG, 25, angle=True, kind="wing")
    out = lifting_line(ac, y, c, theta)
    assert out["Cl"].shape == out["y"].shape
    assert 0.5 < float(out["e"]) <= 1.0


def test_cessna_lifting_line_elliptic_peak():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    y, c, _dx, _dz, theta = planform_stations(ac.WG, 25, angle=True, kind="wing")
    out = lifting_line(ac, y, c, theta)
    assert out["y"][0] < 0 < out["y"][-1]
    assert abs(out["y"][0] + out["y"][-1]) < 1e-6
    i_root = int(np.argmin(np.abs(out["y"])))
    assert out["Cl_ideal"][i_root] > out["Cl_ideal"][0]
    assert out["scale"] == np.max(np.abs(out["Cl_ideal"]))
    assert 0.8 < float(out["e"]) <= 1.0
    assert out["Cl"].shape == out["y"].shape
