import math

import numpy as np

from aid.aero import aero


def test_unswept_ar6_helmbold_then_pi_over_180():
    # Aero.m: a = 2*pi*AR/(2+sqrt(AR^2+4)) at M=0, then a *= pi/180.
    # a0 >= 1 is left as per rad, so k = a0/(2*pi) = 1.
    ar = 6.0
    raw = 2 * math.pi * ar / (2 + math.sqrt(ar**2 + 4))
    pt = {
        "a0": [2 * math.pi],
        "alpha0": [0.0],
        "Cm_ac": [0.0],
        "AR": [ar],
        "TR": [1.0],
        "swp": np.zeros((4, 1)),
        "TC": 0.12,
        "TWISTA": 0.0,
        "CHRDR": 1.0,
        "xmac": 0.25,
        "cbar": [1.0],
        "SSPNOP": 0.0,
        "DHDADI": 0.0,
        "DHDADO": 0.0,
        "SSPN": 3.0,
    }
    out = aero(pt, mach=0.0, angl=False)
    assert abs(float(np.asarray(out["a"]).reshape(-1)[-1]) - raw * math.pi / 180) < 1e-9
    assert abs(float(np.asarray(out["alpha0L"]).reshape(-1)[-1])) < 1e-8


def test_zero_twist_keeps_alpha0():
    pt = {
        "a0": [2 * math.pi, 2 * math.pi],
        "alpha0": [-2.0, -1.0],
        "Cm_ac": [-0.04, -0.04],
        "AR": [8.0],
        "TR": [0.5],
        "swp": np.zeros((4, 1)),
        "TC": 0.12,
        "TWISTA": 0.0,
        "CHRDR": 5.0,
        "xmac": 0.4,
        "cbar": [4.0],
        "SSPNOP": 0.0,
        "DHDADI": 0.0,
        "DHDADO": 0.0,
        "SSPN": 10.0,
    }
    out = aero(pt, mach=0.2, angl=False)
    # mean of the two section alpha0 values when twist correction is zero
    assert abs(float(out["alpha0L"]) - (-1.5)) < 1e-6
    assert "x_ac" in out


def test_mach_one_and_above_write_x_ac():
    # Lift slope is non-finite at Mach >= 1. Aero.m still assigns x_ac.
    for mach in (1.0, 1.2):
        pt = {
            "a0": [2 * math.pi],
            "alpha0": [0.0],
            "Cm_ac": [0.0],
            "AR": [6.0],
            "TR": [1.0],
            "swp": np.zeros((4, 1)),
            "TC": 0.12,
            "TWISTA": 0.0,
            "CHRDR": 1.0,
            "xmac": 0.25,
            "cbar": [1.0],
            "SSPNOP": 0.0,
            "DHDADI": 0.0,
            "DHDADO": 0.0,
            "SSPN": 3.0,
        }
        out = aero(pt, mach=mach, angl=False)
        assert "x_ac" in out
