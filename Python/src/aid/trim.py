"""Incidence trim from Longitudinal_Static_Stability.m (trim == 2)."""

from __future__ import annotations

import math

import numpy as np

from aid.aircraft import Aircraft
from aid.atmosphere import atmosphere


def _last(val) -> float:
    return float(np.asarray(val, dtype=float).reshape(-1)[-1])


def _per_deg(a: float) -> float:
    if a > 1:
        return a * math.pi / 180.0
    return a


def _scalar_delta(val) -> float | None:
    """Length-1 flap or elevator deflection; None when it is not a scalar."""
    if val is None:
        return None
    if isinstance(val, (list, tuple, np.ndarray)):
        arr = np.asarray(val, dtype=float).reshape(-1)
        if arr.size != 1:
            return None
        return float(arr[0])
    return float(val)


def _finite(val) -> float | None:
    try:
        x = float(val)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return x


def trim_incidence(ac: Aircraft, *, htail: bool, body: bool, fix: str) -> dict:
    """Solve wing incidence, tail incidence, and/or angle of attack.

    ``fix`` is ``'both'``, ``'wing'``, or ``'ht'``. Does not write back onto *ac*.
    """
    wg, ht, bd, aero = ac.WG, ac.HT, ac.BD, ac.AERO
    cbar = _last(wg["cbar"])
    s_w = _last(wg["S"])
    xmac = _last(wg.get("xmac", 0.0))
    x_cg = (float(aero["XCG"]) - float(wg["X"]) - xmac) / cbar
    x_ac = float(wg["x_ac"])
    arm = x_cg - x_ac

    aw = _per_deg(float(wg["a"]))
    ht_a = _per_deg(float(ht["a"]))
    eta = float(ht.get("eta", 0.9))
    dwash = float(ht.get("dwash", 0.5))
    tlt = ht_a * eta * _last(ht["S"]) / s_w
    ht_l = float(ht.get("l", 0.0))
    a0l = float(wg.get("alpha0L", 0.0))

    cla = aw + (tlt * (1.0 - dwash) if htail else 0.0)
    cma = aw * arm
    if htail:
        cma -= tlt * ht_l / cbar * (1.0 - dwash)
    if body and "Cma" in bd:
        cma += float(bd["Cma"])

    atm = atmosphere(float(np.asarray(aero["ALT"], dtype=float).reshape(-1)[0]))
    q = 0.5 * atm["D"] * (float(np.asarray(aero["MACH"], dtype=float).reshape(-1)[0]) * atm["a"]) ** 2
    if ac.unit == "in":
        q /= 144.0
    cl = float(aero["WT"]) / (q * s_w)

    f_delta = _scalar_delta(ac.F.get("DELTA"))
    flap = 0.0
    flap_mom = 0.0
    if f_delta is not None:
        flap = aw * f_delta * float(ac.F.get("tau", 0.0))
        flap_mom = flap * float(ac.F.get("l", 0.0)) / cbar
    e_delta = _scalar_delta(ac.E.get("DELTA"))
    elev = tlt * e_delta * float(ac.E.get("tau", 0.0)) if e_delta is not None else 0.0

    # CL = (aw - TLT*dwash)*i_w + TLT*i_h + CLa*aoa + const_lift
    lift_c = np.array([aw - tlt * dwash, tlt, cla], dtype=float)
    lift_const = -aw * a0l + flap + tlt * dwash * a0l + elev
    # 0 = Cm0_wg + Cm0_ht + body + Cma*aoa
    moment_c = np.array(
        [aw * arm + (ht_l / cbar) * tlt * dwash, -(ht_l / cbar) * tlt, cma],
        dtype=float,
    )
    moment_const = (
        float(wg.get("Cm", 0.0))
        - aw * arm * a0l
        - flap_mom
        - (ht_l / cbar) * (tlt * dwash * a0l + elev)
    )
    if body and "Cm0" in bd:
        moment_const += float(bd["Cm0"])

    if fix == "both":
        known = {"alpha": float(np.asarray(aero["ALSCHD"], dtype=float).reshape(-1)[0])}
        free = ("i_wg", "i_ht")
    elif fix == "wing":
        known = {"i_ht": float(ht.get("i", 0.0))}
        free = ("i_wg", "alpha")
    elif fix == "ht":
        known = {"i_wg": float(wg.get("i", 0.0))}
        free = ("i_ht", "alpha")
    else:
        raise ValueError("fix must be 'both', 'wing', or 'ht'")

    index = {"i_wg": 0, "i_ht": 1, "alpha": 2}
    matrix = np.zeros((2, 2))
    rhs = np.array([cl - lift_const, -moment_const], dtype=float)
    for name, value in known.items():
        rhs[0] -= lift_c[index[name]] * value
        rhs[1] -= moment_c[index[name]] * value
    for col, name in enumerate(free):
        matrix[0, col] = lift_c[index[name]]
        matrix[1, col] = moment_c[index[name]]

    solved = {name: float(value) for name, value in known.items()}
    try:
        values = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError:
        values = np.full(2, np.nan)
    for name, value in zip(free, values, strict=True):
        solved[name] = float(value)

    error = 0
    i_wg = _finite(solved["i_wg"])
    if i_wg is None or abs(i_wg) > 60.0:
        i_wg = 0.0
        error = 1
    i_ht = _finite(solved["i_ht"])
    if i_ht is None or abs(i_ht) > 60.0:
        i_ht = 0.0
        error = 2
    alpha = _finite(solved["alpha"])
    if alpha is None:
        alpha = 0.0
        error = 3

    return {"i_wg": i_wg, "i_ht": i_ht, "alpha": alpha, "error": error, "CL": cl}
