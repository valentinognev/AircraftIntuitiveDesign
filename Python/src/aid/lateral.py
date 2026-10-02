"""Lateral-directional handbook derivatives.

Ports Lat_Dir_Corrections.m, Lateral_Static_Stability.m, and
Lateral_Dynamic_Stability.m. Numeric tables are copied verbatim.
"""

from __future__ import annotations

import copy
import math

import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator

from aid.aircraft import Aircraft
from aid.atmosphere import atmosphere

# --- Lat_Dir_Corrections.m Figure 5.3.1.1-22A (effective AR) ---
_F22AX = (
    0, 0.125, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25,
    2.50, 3.00, 3.25, 3.50, 3.75, 4.00, 5.00, 7.00,
)
_F22AX2 = (1.0, 0.6)
_F22AY = (
    (0, 0.40, 0.720, 0.990, 1.19, 1.32, 1.40, 1.46, 1.50, 1.5,
     1.4, 1.42, 1.27, 1.21, 1.17, 1.13, 1.10, 1.04, 1.02),
    (0, 0.70, 0.940, 1.18, 1.35, 1.46, 1.54, 1.60, 1.63, 1.64,
     1.60, 1.53, 1.36, 1.28, 1.21, 1.16, 1.13, 1.06, 1.02),
)

# Figure 5.3.1.1-22B
_F22BX = (0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 1.0)
_F22BX2 = (0.5, 0.6, 0.7, 0.8)
_F22BY = (
    (1.05, 0.94, 0.90, 0.87, 0.86, 0.87, 0.90, 0.93, 0.98, 1.06, 1.16, 1.29, 1.70),
    (1.15, 1.00, 0.95, 0.90, 0.89, 0.90, 0.92, 0.96, 1.01, 1.08, 1.18, 1.31, 1.70),
    (1.22, 1.05, 0.99, 0.94, 0.92, 0.92, 0.95, 0.98, 1.03, 1.10, 1.20, 1.33, 1.70),
    (1.29, 1.09, 1.02, 0.97, 0.94, 0.94, 0.96, 1.00, 1.06, 1.12, 1.22, 1.36, 1.70),
)

# Figure 5.3.1.1-22C
_F5322X = (0.0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 1.2, 1.4, 1.6, 2.0)
_F5322Y = (0.0, 0.29, 0.52, 0.70, 0.77, 0.83, 0.87, 0.98, 1.04, 1.07, 1.13)

# Figure 5.1.2.1-27, ClB/CL sweep. Outer index is taper (1, 0.5, 0).
_F5121X3 = (1.0, 0.5, 0.0)
_F5121X2 = (1.0, 2.0, 4.0, 6.0, 8.0)
_F5121X = (-20, 0, 20, 30, 40, 50, 55, 60)
_F5121Y = (
    (
        (0.0014, 0.0, -0.00125, -0.002, -0.0027, -0.0036, -0.004, -0.0044),
        (0.0015, 0.0, -0.00145, -0.0022, -0.003, -0.0041, -0.005, -0.00595),
        (0.0016, 0.0, -0.0016, -0.0024, -0.0033, -0.0047, -0.0057, -0.0071),
        (0.0016, 0.0, -0.0016, -0.0024, -0.0035, -0.0049, -0.006, -0.0074),
        (0.0016, 0.0, -0.0016, -0.0027, -0.0035, -0.0049, -0.006, -0.0074),
    ),
    (
        (0.0012, 0.0, -0.0012, -0.0019, -0.0026, -0.0034, -0.0039, -0.0044),
        (0.0013, 0.0, -0.0013, -0.0021, -0.003, -0.0043, -0.00515, -0.0064),
        (0.0015, 0.0, -0.0014, -0.0024, -0.0036, -0.005, -0.00605, -0.0075),
        (0.00165, 0.0, -0.0016, -0.0025, -0.0038, -0.0054, -0.0066, -0.0082),
        (0.0018, 0.0, -0.00175, -0.0027, -0.004, -0.0058, -0.007, -0.0089),
    ),
    (
        (0.00105, 0.0, -0.001, -0.0016, -0.0023, -0.003, -0.0035, -0.0038),
        (0.0012, 0.0, -0.0013, -0.0021, -0.0031, -0.00435, -0.00505, -0.0062),
        (0.0014, 0.0, -0.00165, -0.00245, -0.0036, -0.0052, -0.0061, -0.0078),
        (0.00167, 0.0, -0.0017, -0.0028, -0.004, -0.00595, -0.00715, -0.009),
        (0.0018, 0.0, -0.0018, -0.00295, -0.0042, -0.0062, -0.0078, -0.010),
    ),
)

# Figure 5.1.2.1-28-A, Mach sweep factor.
_F128AX2 = (2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0)
_F228AX = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
_F28AY = (
    (1, 1, 1, 1, 1, 1, 1, 1, 0.995, 0.990),
    (1, 1, 1, 1, 1, 1, 1.01, 1.03, 1.03, 1.02),
    (1, 1, 1.01, 1.015, 1.025, 1.05, 1.08, 1.09, 1.10, 1.10),
    (1.0, 1.01, 1.015, 1.02, 1.05, 1.09, 1.115, 1.16, 1.20, 1.21),
    (1.0, 1.01, 1.02, 1.04, 1.07, 1.12, 1.17, 1.24, 1.32, 1.36),
    (1.0, 1.01, 1.05, 1.07, 1.12, 1.18, 1.27, 1.40, 1.58, 1.70),
    (1.0, 1.02, 1.05, 1.10, 1.15, 1.23, 1.37, 1.54, 1.84, 2.08),
)

# Figure 5.2.2.1-26, fuselage Kf.
_F5221X2 = (4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0)
_F5221X = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6)
_F5221Y = (
    (1.0, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.990, 0.970),
    (1.0, 1.00, 1.00, 1.00, 1.00, 1.00, 0.980, 0.948, 0.911),
    (1.0, 1.00, 1.00, 1.00, 0.997, 0.971, 0.933, 0.883, 0.827),
    (1.0, 1.00, 1.00, 0.991, 0.963, 0.922, 0.870, 0.811, 0.746),
    (1.0, 1.00, 0.995, 0.970, 0.932, 0.884, 0.829, 0.764, 0.695),
    (1.0, 1.00, 0.977, 0.944, 0.899, 0.845, 0.780, 0.715, 0.641),
    (1.0, 0.985, 0.960, 0.921, 0.870, 0.812, 0.745, 0.670, 0.592),
)

# Figure 5.1.2.1-28-B, aspect-ratio contribution.
_F5151X2 = (0.0, 0.5, 1.0)
_F5151X = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0)
_F5151Y = (
    (-0.00580, -0.00345, -0.00235, -0.00145, -0.00100,
     -0.00045, -0.00025, 0.00005, 0.00040),
    (-0.00800, -0.00555, -0.00400, -0.00300, -0.00235,
     -0.00140, -0.00100, -0.00065, -0.00020),
    (-0.01130, -0.00800, -0.00595, -0.00465, -0.00370,
     -0.00255, -0.00182, -0.00147, -0.00097),
)

# Figure 5.1.2.1-30b, twist factor.
_TWIST_X2 = (0.0, 0.4, 0.6, 1.0)
_TWIST_X1 = (3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0)
_TWIST_Y = (
    (-0.0000192, -0.0000222, -0.0000238, -0.0000231, -0.0000230,
     -0.0000241, -0.0000260, -0.0000284, -0.0000328),
    (-0.0000220, -0.0000287, -0.0000323, -0.0000335, -0.0000339,
     -0.0000342, -0.0000350, -0.0000370, -0.0000420),
    (-0.0000233, -0.0000300, -0.0000335, -0.0000350, -0.0000366,
     -0.0000370, -0.0000375, -0.0000400, -0.0000470),
    (-0.0000233, -0.0000300, -0.0000335, -0.0000350, -0.0000366,
     -0.0000370, -0.0000375, -0.0000400, -0.0000470),
)

# Figure 5.1.2.1-29, dihedral. Outer index is taper, inner is half-chord sweep.
_F5129X3 = (0.0, 0.5, 1.0)
_F5129X2 = (0.0, 40.0, 60.0)
_F5129X = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0)
_F5129Y = (
    (
        (0.0, -0.000052, -0.000088, -0.000110, -0.000134, -0.000153,
         -0.000168, -0.000190, -0.000200),
        (0.0, -0.000048, -0.000085, -0.000108, -0.000128, -0.000141,
         -0.000153, -0.000173, -0.000178),
        (0.0, -0.000040, -0.000073, -0.000095, -0.000108, -0.000119,
         -0.000127, -0.000135, -0.000138),
    ),
    (
        (0.0, -0.000052, -0.000098, -0.000132, -0.000162, -0.000186,
         -0.000208, -0.000240, -0.000260),
        (0.0, -0.000050, -0.000096, -0.000124, -0.000105, -0.000107,
         -0.000188, -0.000217, -0.000230),
        (0.0, -0.000050, -0.000087, -0.000111, -0.000129, -0.000142,
         -0.000153, -0.000166, -0.000170),
    ),
    (
        (0.0, -0.000050, -0.000096, -0.000133, -0.000167, -0.000193,
         -0.000216, -0.000252, -0.000280),
        (0.0, -0.000050, -0.000095, -0.000129, -0.000155, -0.000178,
         -0.000197, -0.000225, -0.000245),
        (0.0, -0.000050, -0.000088, -0.000113, -0.000132, -0.000147,
         -0.000159, -0.000172, -0.000180),
    ),
)

# Figure 5.2.2.1-30A, Mach dihedral factor.
_F5130X2 = (2.0, 4.0, 6.0, 8.0, 10.0)
_F5130X = (0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
_F5130Y = (
    (1.0, 1.01, 1.018, 1.02, 1.023, 1.03, 1.04, 1.05, 1.057),
    (1.0, 1.012, 1.03, 1.045, 1.06, 1.085, 1.118, 1.16, 1.19),
    (1.0, 1.015, 1.045, 1.07, 1.1, 1.14, 1.197, 1.27, 1.33),
    (1.0, 1.018, 1.05, 1.085, 1.125, 1.19, 1.26, 1.39, 1.485),
    (1.0, 1.02, 1.058, 1.097, 1.148, 1.215, 1.325, 1.495, 1.635),
)

# Figure 5.2.3.1-8, wing-body Kn.
_F5231X2A = (20.0, 14.0, 10.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.5)
_F5231XA = (0.20, 0.8)
_F5231YA = (
    (0.10, 1.88),
    (0.40, 2.21),
    (0.74, 2.60),
    (0.98, 2.80),
    (1.30, 3.13),
    (1.61, 3.50),
    (2.00, 3.88),
    (2.50, 4.40),
    (2.99, 5.00),
    (3.45, 5.40),
)
_F5231X2B = (0.8, 1.0, 1.2, 1.4, 1.6)
_F5231XB = (0.0, 3.0, 6.0)
_F5231YB = (
    (0.0, 2.35, 4.68),
    (0.0, 3.00, 6.00),
    (0.0, 3.60, 7.25),
    (0.0, 4.18, 8.50),
    (0.0, 4.79, 9.50),
)
_F5231X2C = (0.5, 0.6, 0.8, 1.0, 2.0)
_F5231XC = (0.0, 6.0)
_F5231YC = (
    (-0.00048, 0.00251),
    (-0.00048, 0.00350),
    (-0.00048, 0.00477),
    (-0.00048, 0.00559),
    (-0.00048, 0.00641),
)

# Lateral_Static_Stability.m lines 45–69. Not the effective-AR tables above.
_AVB = (0, 1.18, 1.45, 1.6, 1.62, 1.5, 1.36, 1.2, 1.15, 1.1, 1.08, 1.06, 1.05, 1.05, 1.05)
_BV_H = tuple(0.5 * i for i in range(15))  # 0:0.5:7
_AVHB = (1.2, 1.1, 1, 0.95, 0.91, 0.9, 0.92, 0.98, 1.09, 1.35, 1.7)
_ZH_BV = tuple(0.1 * i for i in range(11))  # 0:0.1:1
_KH = (0, 0.28, 0.5, 0.7, 0.82, 0.92, 0.98, 1.03, 1.07, 1.1, 1.12)
_S_RATIO = tuple(0.2 * i for i in range(11))  # 0:0.2:2


def _last(val) -> float:
    return float(np.asarray(val, dtype=float).reshape(-1)[-1])


def _cosd(deg: float) -> float:
    return math.cos(math.radians(deg))


def _sind(deg: float) -> float:
    return math.sin(math.radians(deg))


def _tand(deg: float) -> float:
    return math.tan(math.radians(deg))


def _swp(wg: dict, row: int) -> float:
    """MATLAB swp(row, end). Row is 1-based: 2 is c/4, 3 is c/2."""
    swp = np.asarray(wg["swp"], dtype=float)
    if swp.ndim == 1:
        swp = swp.reshape(-1, 1)
    return float(swp[row - 1, -1])


def _interp1(x, y, xq, kind: str = "linear", extrap: bool = False) -> float:
    """MATLAB interp1, including spline / pchip / linear / nearest."""
    xs = np.asarray(x, dtype=float).reshape(-1)
    ys = np.asarray(y, dtype=float).reshape(-1)
    query = float(xq)
    if xs.size != ys.size:
        raise ValueError("interp1 x and y lengths differ")
    if xs.size < 2:
        raise ValueError("interp1 needs at least two samples")
    if xs[0] > xs[-1]:
        xs = xs[::-1].copy()
        ys = ys[::-1].copy()
    inside = bool(xs[0] <= query <= xs[-1])
    if kind == "nearest":
        if not inside and not extrap:
            return float("nan")
        dist = np.abs(xs - query)
        index = int(np.flatnonzero(dist == dist.min())[-1])
        return float(ys[index])
    if not inside and not extrap:
        return float("nan")
    if kind == "linear":
        if query <= xs[0]:
            i = 0
        elif query >= xs[-1]:
            i = xs.size - 2
        else:
            i = int(np.searchsorted(xs, query, side="right") - 1)
            i = min(max(i, 0), xs.size - 2)
        span = xs[i + 1] - xs[i]
        t = 0.0 if span == 0 else (query - xs[i]) / span
        return float(ys[i] + t * (ys[i + 1] - ys[i]))
    if kind == "spline":
        return float(CubicSpline(xs, ys, bc_type="not-a-knot", extrapolate=True)(query))
    if kind == "pchip":
        return float(PchipInterpolator(xs, ys, extrapolate=True)(query))
    raise ValueError(f"unsupported interp1 kind {kind}")


def _aircraft_cl(ac: Aircraft) -> float:
    """MATLAB AC.CL. Wing CL on the aircraft, else AERO.CL."""
    if ac.WG.get("CL") is not None:
        return _last(ac.WG["CL"])
    if ac.AERO.get("CL") is not None:
        return _last(ac.AERO["CL"])
    raise KeyError("lat_dir_corrections needs WG['CL'] or AERO['CL'] (MATLAB AC.CL)")


def _reynolds_per_length(ac: Aircraft, mach: float) -> float:
    """ATM.Re = D * M * a / V. ALT defaults to sea level when unset."""
    aero = ac.AERO
    if aero.get("Re") is not None:
        return float(aero["Re"])
    alt = aero.get("ALT", 0.0)
    if alt is None:
        alt = 0.0
    atm = atmosphere(float(np.asarray(alt, dtype=float).reshape(-1)[0]))
    return float(atm["D"] * mach * atm["a"] / atm["V"])


def _alpha_deg(ac: Aircraft) -> float:
    """AC.alpha. Lateral runs before longitudinal trim, so the default is 0."""
    alpha = ac.AERO.get("alpha")
    if alpha is None:
        return 0.0
    return float(np.asarray(alpha, dtype=float).reshape(-1)[0])


def _x_cg(ac: Aircraft) -> float:
    """AID.m: (XCG - WG.X - WG.xmac) / cbar, the fraction of MAC."""
    wg = ac.WG
    return (float(ac.AERO["XCG"]) - float(wg["X"]) - float(wg["xmac"])) / _last(wg["cbar"])


def _avb_over_av(trv: float, bv_2r1: float) -> float:
    if trv <= 0.6:
        avb = _interp1(_F22AX, _F22AY[1], bv_2r1, "spline", extrap=False)
    elif trv <= 1.0:
        curves = [_interp1(_F22AX, row, bv_2r1, "spline", extrap=False) for row in _F22AY]
        avb = _interp1(_F22AX2, curves, trv, "linear", extrap=False)
    else:
        avb = 1.0
    if trv > 1.0:
        avb = 1.0
    return avb


def _avhb_over_avb(xact_cv: float, zh_bv: float) -> float:
    zh = 0.0 if zh_bv < 0.0 else zh_bv
    if xact_cv <= 0.5:
        return _interp1(_F22BX, _F22BY[0], zh, "spline", extrap=False)
    if xact_cv <= 1.0:
        curves = [_interp1(_F22BX, row, zh, "spline", extrap=False) for row in _F22BY]
        return _interp1(_F22BX2, curves, xact_cv, "linear", extrap=False)
    raise ValueError("Xact_cv above 1 is not defined in Lat_Dir_Corrections.m")


def _clb_sweep(ar: float, tr: float, sweep_c2: float, mach: float, lf_bw: float) -> tuple[float, float, float]:
    clbcl2 = []
    for taper_rows in _F5121Y:
        clbcl1 = [
            _interp1(_F5121X, row, sweep_c2, "spline", extrap=True) for row in taper_rows
        ]
        clbcl2.append(_interp1(_F5121X2, clbcl1, ar, "linear", extrap=True))
    clb_cl = _interp1(_F5121X3, clbcl2, tr, "spline", extrap=False)

    mcos = mach * _cosd(sweep_c2)
    a_cos = ar / _cosd(sweep_c2)
    kml = [_interp1(_F228AX, row, mcos, "spline", extrap=True) for row in _F28AY]
    clb_km = _interp1(_F128AX2, kml, a_cos, "linear", extrap=True)

    kf1 = [_interp1(_F5221X, row, lf_bw, "spline", extrap=True) for row in _F5221Y]
    clb_kf = _interp1(_F5221X2, kf1, a_cos, "spline", extrap=True)
    return clb_cl, clb_km, clb_kf


def _clb_ar(ar: float, tr: float) -> float:
    if ar > 8.0:
        vals = [_interp1(_F5151X, row, ar, "linear", extrap=True) for row in _F5151Y]
        return _interp1(_F5151X2, vals, tr, "linear", extrap=False) / 6.0
    vals = [_interp1(_F5151X, row, ar, "spline", extrap=False) for row in _F5151Y]
    return _interp1(_F5151X2, vals, tr, "linear", extrap=False)


def _clb_ts(ar: float, tr: float) -> float:
    y1 = [_interp1(_TWIST_X1, row, ar, "spline", extrap=True) for row in _TWIST_Y]
    return _interp1(_TWIST_X2, y1, tr, "linear", extrap=True)


def _clb_dihedral_factor(ar: float, tr: float, sweep_c2: float, mach: float) -> tuple[float, float]:
    clbg1 = []
    for taper_rows in _F5129Y:
        clbg2 = [
            _interp1(_F5129X, row, ar, "spline", extrap=True) for row in taper_rows
        ]
        clbg1.append(_interp1(_F5129X2, clbg2, sweep_c2, "spline", extrap=True))
    clb_gu = _interp1(_F5129X3, clbg1, tr, "spline", extrap=False)

    mcos = mach * _cosd(sweep_c2)
    a_cos = ar / _cosd(sweep_c2)
    kmg1 = [_interp1(_F5130X, row, mcos, "spline", extrap=True) for row in _F5130Y]
    kmg = _interp1(_F5130X2, kmg1, a_cos, "linear", extrap=True)
    return clb_gu, kmg


def _body_kn(x, height, radii, xcg: float) -> float:
    lf = float(x[-1] - x[0])
    sbs = float(np.trapezoid(height, x))
    h1 = _interp1(x, height, 0.25 * lf, "linear", extrap=False)
    h2 = _interp1(x, height, 0.75 * lf, "linear", extrap=False)
    hf_max = float(np.max(height))
    wf_max = 2.0 * float(np.max(radii))
    xm_lf = xcg / lf
    lf_sb = lf**2 / sbs
    h1_h2 = math.sqrt(h1 / h2)
    hf_wf = hf_max / wf_max

    figby1 = [_interp1(_F5231XA, row, xm_lf, "linear", extrap=True) for row in _F5231YA]
    figby = _interp1(_F5231X2A, figby1, lf_sb, "spline", extrap=True)
    figcx1 = [_interp1(_F5231XB, row, figby, "linear", extrap=True) for row in _F5231YB]
    figcx = _interp1(_F5231X2B, figcx1, h1_h2, "spline", extrap=True)
    kn1 = [_interp1(_F5231XC, row, figcx, "linear", extrap=True) for row in _F5231YC]
    kn1 = [0.0 if not math.isfinite(val) else val for val in kn1]
    return _interp1(_F5231X2C, kn1, hf_wf, "spline", extrap=True)


def _project_vtail(ac: Aircraft, angl: bool) -> None:
    """Replace VT with the projected HT when the body is off and the HT has dihedral."""
    if ac.plot_cmp[3]:
        return
    ht = ac.HT
    dhdadi = float(ht.get("DHDADI") or 0.0)
    dhdado = float(ht.get("DHDADO") or 0.0)
    if not dhdadi and not dhdado:
        return
    sspnop = float(ht.get("SSPNOP") or 0.0)
    sspn = float(ht["SSPN"])
    if angl:
        if sspnop:
            proj = (sspnop * _sind(dhdadi) + (sspn - sspnop) * _sind(dhdadi)) / sspn
        else:
            proj = _sind(dhdadi)
    elif sspnop:
        proj = (sspnop * _tand(dhdadi) + (sspn - sspnop) * _tand(dhdadi)) / sspn
    else:
        proj = _tand(dhdadi)
    vt = copy.deepcopy(ht)
    factor = float(proj)
    if isinstance(vt.get("S"), list):
        vt["S"] = [float(v) * factor for v in vt["S"]]
    else:
        vt["S"] = float(vt["S"]) * factor
    vt["b"] = float(vt["b"]) * factor
    ac.VT = vt


def lat_dir_corrections(ac: Aircraft, mach: float) -> dict:
    """Port Lat_Dir_Corrections.m. Writes VT['AReff'] and BD['Cnb'].

    Returns {'Clb_wing': float}, ClB_sweep+ClB_AR+ClB_twist+ClB_dihedral.
    Also stores that value on WG['Clb_wing'] so lateral_static can add it.
    """
    wg = ac.WG
    vt = ac.VT
    bd = ac.BD
    cl = _aircraft_cl(ac)
    x = np.asarray(bd["X"], dtype=float)
    zu = np.asarray(bd["ZU"], dtype=float)
    zl = np.asarray(bd["ZL"], dtype=float)
    radii = np.asarray(bd["R"], dtype=float)
    height = zu - zl

    av = _last(vt["AR"])
    trv = _last(vt["TR"])
    bv_2r1 = float(radii[-2] + radii[-1])
    st_sv = _last(vt["S"]) / _last(wg["S"])
    zh_bv = float(vt["Z"]) - (float(np.sum(zu[-2:])) / 2 + float(np.sum(zl[-2:])) / 2) / 2
    xact_cv = 0.25

    ar = _last(wg["AR"])
    span = float(wg["b"])
    tr = _last(wg["TR"])
    sweep_c2 = _swp(wg, 3)
    lf_tip = float(wg["Xtip"]) + float(wg["CHRDTP"]) / 2 - float(x[0])

    avb_av = _avb_over_av(trv, bv_2r1)
    avhb_avb = _avhb_over_avb(xact_cv, zh_bv)
    kh = _interp1(_F5322X, _F5322Y, st_sv, "pchip", extrap=False)
    if bv_2r1 <= 2.0:
        kv = 0.75
    elif bv_2r1 < 3.5:
        kv = 0.75 + 0.1667 * (bv_2r1 - 2.0)
    else:
        kv = 1.0
    aeff = av * avb_av * (1.0 + kh * (avhb_avb - 1.0))
    vt["AReff"] = aeff
    # Kv (figure 22D) is computed in the MATLAB file and not used in Aeff.
    _ = kv

    clb_cl, clb_km, clb_kf = _clb_sweep(ar, tr, sweep_c2, mach, lf_tip / span)
    clb_sweep = cl * clb_cl * clb_km * clb_kf
    clb_ar = cl * _clb_ar(ar, tr)
    clb_twist = -float(wg["TWISTA"]) * _tand(_swp(wg, 2)) * _clb_ts(ar, tr)
    clb_gu, kmg = _clb_dihedral_factor(ar, tr, sweep_c2, mach)
    clb_dihedral = float(wg["gamma"]) * clb_gu * kmg
    clb_dihedral = clb_dihedral - 0.0005 * math.sqrt(ar) * (float(bd["d_eq"]) / span) ** 2
    clb_wing = clb_sweep + clb_ar + clb_twist + clb_dihedral
    wg["Clb_wing"] = clb_wing

    sbs = float(np.trapezoid(height, x))
    lf = float(x[-1] - x[0])
    re = _reynolds_per_length(ac, mach)
    krl = 0.205 * math.log(re * lf) - 1.833
    kn = _body_kn(x, height, radii, float(ac.AERO["XCG"]))
    bd["Cnb"] = -kn * krl * sbs * lf / (_last(wg["S"]) * span)
    return {"Clb_wing": clb_wing}


def lateral_static(ac: Aircraft, angl: bool, cl: float) -> dict:
    """Port Lateral_Static_Stability.m.

    Writes VT['a'], VT['k'], VT['swash'], VT['h'], VT['l'] (and hp, lp).
    Clb is Clb_wing plus the fuselage and vertical-tail terms.
    """
    _project_vtail(ac, angl)
    wg = ac.WG
    ht = ac.HT
    vt = ac.VT
    bd = ac.BD
    aero = ac.AERO

    alpha = _alpha_deg(ac)
    hp = float(vt["Z"]) + float(vt["ymac"]) - float(aero["ZCG"])
    lp = float(vt["X"]) + float(vt["xmac"]) + _last(vt["cbar"]) / 4.0 - float(aero["XCG"])
    h = hp * _cosd(alpha) - lp * _sind(alpha)
    tail_l = lp * _cosd(alpha) + hp * _sind(alpha)
    vt["hp"] = hp
    vt["lp"] = lp
    vt["h"] = h
    vt["l"] = tail_l

    x = np.asarray(bd["X"], dtype=float)
    zu = np.asarray(bd["ZU"], dtype=float)
    zl = np.asarray(bd["ZL"], dtype=float)
    height = zu - zl
    vt_x = float(vt["X"])
    d1 = _interp1(x, height, vt_x, "linear", extrap=False)
    d2 = _interp1(x, height, vt_x, "linear", extrap=True)
    diameter = (d1 + d2) / 2.0
    span_ratio = float(vt["b"]) / diameter
    # Lateral_Static_Stability.m line 40 uses VT.b/2, not b/d.
    if span_ratio < 2.0:
        k = 0.75
    elif span_ratio < 3.5:
        k = 0.75 + (float(vt["b"]) / 2.0 - 2.0) / 6.0
    else:
        k = 1.0
    vt["k"] = k

    avb_av = _interp1(_BV_H, _AVB, span_ratio, "spline", extrap=True)

    if bd.get("dk") is None:
        bd["dk"] = 1.0
    z_ref = float(np.mean((zu + zl) / 2.0))
    z_wing = float(wg["Z"]) - z_ref
    if z_wing > 0.0:
        kwb = 1.85 * z_wing / float(np.max(zu - z_ref))
    else:
        kwb = -1.5 * z_wing / float(np.max(z_ref - zl))
    radii = np.asarray(bd["R"], dtype=float)
    imax = int(np.flatnonzero(radii == np.max(radii))[-1])
    x1 = float(x[imax])
    nx = int(bd["NX"])
    x0_pos = _interp1(
        x, np.arange(1, nx + 1, dtype=float),
        0.378 * float(x[-1]) + 0.527 * x1,
        "nearest",
        extrap=False,
    )
    s0 = float(np.asarray(bd["S"], dtype=float).reshape(-1)[int(round(x0_pos)) - 1])
    s_w = _last(wg["S"])
    gamma = float(wg["gamma"])
    cyb_wb = 2.0 * math.pi / 180.0 * kwb * float(bd["dk"]) * s0 / s_w - 0.0001 * gamma

    avhb_av = _interp1(_ZH_BV, _AVHB, float(ht["Z"]) / float(vt["b"]), "spline", extrap=True)
    k_h = _interp1(_S_RATIO, _KH, _last(ht["S"]) / _last(vt["S"]), "spline", extrap=True)

    swp_c4 = _swp(wg, 2)
    swp_c2 = _swp(wg, 3)
    mach = float(np.asarray(aero["MACH"], dtype=float).reshape(-1)[0])
    b_pg = math.sqrt(1.0 - mach**2 * _cosd(swp_c4) ** 2)
    k2d = _last(ht["a0"]) / (2.0 * math.pi)
    ar_eff = _last(vt["AR"]) * avb_av * (1.0 + k_h * (avhb_av - 1.0))
    vt_a = 2.0 * math.pi * ar_eff / (
        2.0 + math.sqrt((ar_eff * b_pg / k2d) ** 2 * (1.0 + _tand(swp_c2) ** 2 / b_pg**2) + 4.0)
    )
    vt_a = vt_a * math.pi / 180.0
    vt["a"] = vt_a

    ar = _last(wg["AR"])
    vt["swash"] = (
        0.724
        + 3.06 * _last(vt["S"]) / s_w / (1.0 + _cosd(swp_c4))
        + 0.4 * z_wing / float(np.max(height))
        + 0.009 * ar
    )
    cyb_v = -k * vt_a * float(vt["swash"]) * _last(vt["S"]) / s_w
    cyb = cyb_wb + cyb_v

    cnb_gamma = -0.075 * gamma * cl * math.pi**2 / 180.0**2
    cswp = _cosd(swp_c4)
    sswp = _sind(swp_c4)
    tswp = sswp / cswp
    x_cg = _x_cg(ac)
    sweep_term = (
        1.0 / (4.0 * math.pi * ar)
        - tswp / (math.pi * ar * (ar + 4.0 * cswp))
        * (
            cswp
            - ar / 2.0
            - ar**2 / (8.0 * cswp)
            - 6.0 * (x_cg - float(wg["x_ac"])) * sswp / ar
        )
    )
    cnb_sweep = cl**2 * math.pi / 180.0 * sweep_term
    cnb_sweep = (
        (ar + 4.0 * cswp)
        / (ar * b_pg + 4.0 * cswp)
        * (ar**2 * b_pg**2 + 4.0 * ar * b_pg * cswp - 8.0 * cswp**2)
        / (ar**2 + 4.0 * ar * cswp - 8.0 * cswp**2)
        * cnb_sweep
    )
    cnb = cnb_gamma + cnb_sweep + float(bd["Cnb"]) - cyb_v * tail_l / float(wg["b"])

    fcl = (zu + zl) / 2.0
    z_bd = _interp1(x, fcl, float(wg["X"]) + float(wg["CHRDR"]) / 4.0, "linear", extrap=False)
    z_wg = z_bd - float(wg["Z"])
    raw_wing = wg.get("Clb_wing")
    clb_wing = 0.0 if raw_wing is None else float(raw_wing)
    clb = clb_wing + 1.2 * math.sqrt(ar) * math.pi / 180.0 * 2.0 * z_wg * float(bd["d_eq"]) / float(wg["b"]) ** 2
    clb = clb + cyb_v * h / float(wg["b"])

    return {"CYb": cyb, "Cnb": cnb, "Clb": clb, "Clda": 0.1, "Cnda": 0.1}


def lateral_dynamic(ac: Aircraft, cl: float, cyb: float) -> dict:
    """Port Lateral_Dynamic_Stability.m. Returns CYp, CYr, Clp, Clr, Cnp, Cnr."""
    wg = ac.WG
    vt = ac.VT
    ar = _last(wg["AR"])
    swp_c4 = _swp(wg, 2)
    span = float(wg["b"])
    tr = _last(wg["TR"])
    cyp = (
        cl * (ar + _cosd(swp_c4)) / (ar + 4.0 * _cosd(swp_c4)) * _tand(swp_c4)
        + 2.0 * cyb / span * (float(vt["h"]) - float(vt["hp"]))
    )
    cyr = -2.0 * cyb * float(vt["l"]) / span
    clp = -float(wg["a"]) / 12.0 * (1.0 + 3.0 * tr) / (1.0 + tr)
    clr = cl / 4.0 - 2.0 * cyb * float(vt["l"]) * float(vt["h"]) / span**2
    cnp = -cl / 8.0 - 2.0 * cyb * float(vt["l"]) * (float(vt["h"]) - float(vt["hp"])) / span**2
    cnr = -2.0 * float(vt["a"]) * float(vt["swash"]) * _last(vt["S"]) / _last(wg["S"]) * (float(vt["l"]) / span) ** 2
    return {"CYp": cyp, "CYr": cyr, "Clp": clp, "Clr": clr, "Cnp": cnp, "Cnr": cnr}
