"""Handbook control derivatives from Controls.m, per degree.

Stored surface deflections are not read or written. Each probe row carries the
same slope. Drag is omitted. Aileron yaw is omitted.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.interpolate import CubicSpline

from aid.aircraft import Aircraft
from aid.control_deriv import blank_row, iter_rows

# Perkins and Hage Figure 5-33. Linear interpolation; ratio clamped to the table.
_S_RATIO = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7)
_TAU = (0.0, 0.25, 0.4, 0.5, 0.58, 0.65, 0.71, 0.76)

# DATCOM Figure 6.1.4.1-15, Controls.m lines 30–42 (cubic spline).
_ETA = tuple(i / 10 for i in range(11))
_KB0 = (0, 0.155, 0.305, 0.44, 0.56, 0.675, 0.775, 0.86, 0.93, 0.98, 1)
_KB1 = (0, 0.125, 0.25, 0.375, 0.495, 0.6, 0.705, 0.8, 0.89, 0.95, 1)


def _last(val) -> float:
    return float(np.asarray(val, dtype=float).reshape(-1)[-1])


def _per_deg(a: float) -> float:
    """Same rule as stability._per_deg: values above 1 are per radian."""
    if a > 1:
        return a * math.pi / 180.0
    return a


def _span_legal(surf: dict) -> bool:
    """Outboard span must lie beyond inboard, with both chord stations set."""
    for key in ("SPANFI", "SPANFO", "CHRDFI", "CHRDFO"):
        if key not in surf or surf[key] is None:
            return False
    try:
        spanfi = float(surf["SPANFI"])
        spanfo = float(surf["SPANFO"])
        float(surf["CHRDFI"])
        float(surf["CHRDFO"])
    except (TypeError, ValueError):
        return False
    return spanfo > spanfi


def _control_area(surf: dict) -> float:
    return 0.5 * (float(surf["CHRDFI"]) + float(surf["CHRDFO"])) * (
        float(surf["SPANFO"]) - float(surf["SPANFI"])
    )


def _tau(area: float, parent_area: float) -> float:
    ratio = area / parent_area
    if ratio < 0.0:
        ratio = 0.0
    elif ratio > 0.7:
        ratio = 0.7
    return float(np.interp(ratio, _S_RATIO, _TAU))


def _aileron_kb(ail: dict, wg: dict) -> float:
    sspn = float(wg["SSPN"])
    taper = float(wg["TR"])
    kb0 = CubicSpline(_ETA, _KB0, extrapolate=True)
    kb1 = CubicSpline(_ETA, _KB1, extrapolate=True)
    eta_in = float(ail["SPANFI"]) / sspn
    eta_out = float(ail["SPANFO"]) / sspn
    kb_in = float(kb0(eta_in)) + taper * (float(kb1(eta_in)) - float(kb0(eta_in)))
    kb_out = float(kb0(eta_out)) + taper * (float(kb1(eta_out)) - float(kb0(eta_out)))
    return kb_out - kb_in


def _x_cg(wg: dict) -> float:
    if wg.get("x_cg") is not None:
        return _last(wg["x_cg"])
    return 0.25


def _missing_key(block: dict, *keys: str) -> str | None:
    for key in keys:
        if block.get(key) is None:
            return key
    return None


def handbook_controls(ac: Aircraft, deltas_deg=None) -> list[dict]:
    """Per-degree handbook derivatives for each surface and probe angle."""
    wg = ac.WG
    s_w = _last(wg["S"])
    cbar = _last(wg["cbar"])
    a_w = _per_deg(float(wg["a"]))
    span = float(wg["b"])
    x_cg = _x_cg(wg)

    flap_ok = _span_legal(ac.F)
    cl_df = cm_df = None
    if flap_ok:
        flap = ac.F
        tau_f = _tau(_control_area(flap), s_w)
        flap_l = (cbar - 0.5 * (float(flap["CHRDFI"]) + float(flap["CHRDFO"]))) - x_cg
        cl_df = a_w * tau_f
        cm_df = -a_w * tau_f * flap_l / cbar

    ail_ok = _span_legal(ac.A)
    cl_da = None
    if ail_ok:
        ail = ac.A
        cl_da = a_w * _tau(_control_area(ail), s_w) * _aileron_kb(ail, wg)

    ht = ac.HT
    elev_missing = _missing_key(ht, "l")
    elev_ok = elev_missing is None and _span_legal(ac.E)
    cl_de = cm_de = None
    if elev_ok:
        tau_e = _tau(_control_area(ac.E), _last(ht["S"]))
        eta = 0.9 if ht.get("eta") is None else float(ht["eta"])
        a_h = _per_deg(float(ht["a"]))
        cl_de = a_h * eta * _last(ht["S"]) / s_w * tau_e
        cm_de = -float(ht["l"]) / cbar * cl_de

    vt = ac.VT
    rudder_missing = _missing_key(vt, "l", "a")
    rudder_ok = rudder_missing is None and _span_legal(ac.R)
    cy_dr = cl_dr = cn_dr = None
    if rudder_ok:
        tau_r = _tau(_control_area(ac.R), _last(vt["S"]))
        a_v = _per_deg(float(vt["a"]))
        cy_dr = float(vt["k"]) * a_v * float(vt["swash"]) * _last(vt["S"]) / s_w * tau_r
        cl_dr = cy_dr * float(vt["h"]) / span
        cn_dr = -cy_dr * float(vt["l"]) / span

    rows: list[dict] = []
    for surface, delta in iter_rows(deltas_deg):
        if surface == "flap":
            if flap_ok:
                row = blank_row(surface, delta, available=True)
                row["CL"] = cl_df
                row["Cm"] = cm_df
            else:
                row = blank_row(surface, delta, available=False, reason="illegal span")
        elif surface == "aileron":
            if ail_ok:
                row = blank_row(surface, delta, available=True)
                row["Cl"] = cl_da
            else:
                row = blank_row(surface, delta, available=False, reason="illegal span")
        elif surface == "elevator":
            if elev_missing is not None:
                row = blank_row(surface, delta, available=False, reason="HT.l missing")
            elif not elev_ok:
                row = blank_row(surface, delta, available=False, reason="illegal span")
            else:
                row = blank_row(surface, delta, available=True)
                row["CL"] = cl_de
                row["Cm"] = cm_de
        else:
            if rudder_missing is not None:
                row = blank_row(
                    surface,
                    delta,
                    available=False,
                    reason=f"VT.{rudder_missing} missing",
                )
            elif not rudder_ok:
                row = blank_row(surface, delta, available=False, reason="illegal span")
            else:
                row = blank_row(surface, delta, available=True)
                row["CY"] = cy_dr
                row["Cl"] = cl_dr
                row["Cn"] = cn_dr
        rows.append(row)
    return rows
