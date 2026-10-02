import math

import numpy as np

from aid.tornado.viscous import viscous_correction


def _one_strip():
    """Smallest one-panel, one-strip wing that reaches totalliftcoeff."""
    xyz = np.zeros((1, 5, 3), dtype=float)
    xyz[0, 0] = (0.0, 0.0, 0.0)
    xyz[0, 1] = (0.0, 1.0, 0.0)
    xyz[0, 2] = (1.0, 1.0, 0.0)
    xyz[0, 3] = (1.0, 0.0, 0.0)
    xyz[0, 4] = (0.0, 0.0, 0.0)

    geo = {
        "nwing": 1,
        "nelem": np.array([1]),
        "symetric": np.array([0.0]),
        "ny": np.array([[1.0]]),
        "nx": np.array([[1.0]]),
        "fnx": np.array([[0.0]]),
        "b": np.array([[1.0]]),
        "c": np.array([[1.0]]),
        "T": np.array([[1.0]]),
        "starty": np.array([[0.0]]),
        "startz": np.array([[0.0]]),
        "foil": [[[None, None]]],
    }
    state = {
        "alpha": 0.0,
        "betha": 0.0,
        "AS": 50.0,
        "rho": 1.225,
        "ALT": 0.0,
    }
    lattice = {
        "XYZ": xyz,
        "N": np.array([[0.0, 0.0, 1.0]]),
        "COLLOC": np.array([[0.5, 0.5, 0.0]]),
    }
    results = {"F": np.zeros((1, 3), dtype=float)}
    ref = {"S_ref": 1.0, "C_mac": 1.0}
    return geo, state, lattice, results, ref


def test_one_strip_totalliftcoeff_is_finite():
    geo, state, lattice, results, ref = _one_strip()
    out = viscous_correction(geo, state, lattice, results, ref)
    assert math.isfinite(out["totalliftcoeff"])


def _cambered_stored_loop(n_side: int = 11) -> np.ndarray:
    """Closed loop in the order geo foil arrays use: lower TE→LE, then upper LE→TE.

    The lower half is camber-free thickness. The upper half adds positive camber,
    so the two halves are not mirrors.
    """
    beta = np.linspace(0.0, np.pi, n_side)
    x = 0.5 * (1.0 - np.cos(beta))
    thickness = 0.06 * np.sin(beta)
    camber = 0.04 * np.sin(beta)
    y_lower = -thickness
    y_upper = thickness + camber
    lower = np.column_stack((x[::-1], y_lower[::-1]))
    upper = np.column_stack((x[1:], y_upper[1:]))
    return np.vstack((lower, upper))


def test_stored_closed_loop_foil_passes_upper_surface_on_top(monkeypatch):
    foil = _cambered_stored_loop()
    geo, state, lattice, results, ref = _one_strip()
    geo["foil"] = [[[foil, foil]]]
    captured: dict = {}

    def _capture_section(z, alpha_rad, reynolds):
        captured["z"] = np.asarray(z, dtype=float).copy()
        return {
            "cl": 0.0,
            "cd": 0.01,
            "cm": 0.0,
            "upperbl": np.zeros(6),
            "lowerbl": np.zeros(6),
        }

    monkeypatch.setattr("aid.tornado.viscous.pablo", _capture_section)
    viscous_correction(geo, state, lattice, results, ref)

    z = captured["z"]
    n_up = int(round(z[0, 0]))
    n_lo = int(round(z[0, 1]))
    upper = z[1 : 1 + n_up]
    lower = z[1 + n_up : 1 + n_up + n_lo]
    iu = int(np.argmin(np.abs(upper[:, 0] - 0.5)))
    il = int(np.argmin(np.abs(lower[:, 0] - 0.5)))
    assert upper[iu, 1] > 0.05
    assert lower[il, 1] < 0.0
    assert upper[iu, 1] > lower[il, 1]
