"""Fuselage pitching-moment derivatives (Multhopp / Gilruth-White).

Port of ``Matlab/fsroot/code/Body_Stability.m``.
"""

from __future__ import annotations

import copy
import math

import numpy as np

from aid.aircraft import Aircraft


def _last(val) -> float:
    return float(np.asarray(val, dtype=float).reshape(-1)[-1])


def _gilruth_white(bd: dict, wg: dict) -> None:
    l_fus = float(np.asarray(bd["X"], dtype=float).reshape(-1)[-1])
    l = float(wg["X"]) + float(wg["CHRDR"]) / 4.0
    w = float(np.max(np.asarray(bd["R"], dtype=float))) * 2.0
    k = 0.002322 * math.exp(5.037 * l / l_fus)
    bd["Cm0"] = 0.0
    bd["Cma"] = k * w**2 * l_fus / (_last(wg["S"]) * _last(wg["cbar"]))


def _multhopp(ac: Aircraft, bd: dict) -> None:
    wg, ht, aero = ac.WG, ac.HT, ac.AERO
    x = np.asarray(bd["X"], dtype=float).reshape(-1)
    nx = int(bd["NX"])
    wg_x = float(wg["X"])
    wg_chrdr = float(wg["CHRDR"])

    le_candidates = np.where(x - wg_x > 0)[0]
    le = int(le_candidates[0]) if le_candidates.size else 0
    te_candidates = np.where(x - (wg_x + wg_chrdr) < 0)[0]
    te = int(te_candidates[-1]) if te_candidates.size else le
    if te < le:
        te = le

    cr_exp = x[te] - x[le]
    fwd = np.arange(0, le)
    aft = np.arange(te, nx - 1)
    if fwd.size == 0 or aft.size == 0 or cr_exp <= 0:
        _gilruth_white(bd, wg)
        return

    dx = x[1:] - x[:-1]
    x1 = x[le] - x[fwd] - dx[fwd] / 2.0
    x2 = x[aft] - dx[aft - 1] / 2.0 - x[te]
    r = np.asarray(bd["R"], dtype=float).reshape(-1)
    wf = r[1:] + r[:-1]
    la = x[-1] - x[te]

    de_da = np.zeros(nx - 1, dtype=float)
    if fwd.size > 1:
        de_da[fwd[:-1]] = 0.175 * (x1[:-1] / cr_exp) ** (-1.341)
    de_da[fwd[-1]] = 0.754 * (dx[fwd[-1]] / cr_exp) ** (-0.793)

    ac_a = getattr(ac, "a", None)
    if ac_a is not None:
        de_da = de_da * float(np.asarray(ac_a, dtype=float).reshape(-1)[0]) / 0.0785

    db_da1 = 1.0 + de_da
    de_da_tail = float(ht.get("dwash", 0.5))
    db_da2 = x2 / la * (1.0 - de_da_tail)

    db_da = np.concatenate([db_da1[fwd], db_da2])
    wf_seg = np.concatenate([wf[fwd], wf[aft]])
    dx_seg = np.concatenate([dx[fwd], dx[aft]])

    s_ref = _last(wg["S"])
    cbar = _last(wg["cbar"])
    bd["Cma"] = (
        math.pi**2 / (180.0 * 2.0 * s_ref * cbar) * float(np.sum(wf_seg**2 * db_da * dx_seg))
    )

    fineness = np.array([4, 6, 8, 10, 12, 14, 16, 18, 20], dtype=float)
    delta_k = np.array([0.78, 0.86, 0.91, 0.94, 0.955, 0.965, 0.97, 0.973, 0.975], dtype=float)
    am_poly = np.polyfit(fineness, delta_k, 4)
    bd["dk"] = float(np.polyval(am_poly, x[-1] / (2.0 * float(np.max(r)))))

    mach = np.array([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9], dtype=float)
    delta_cm = np.array([1, 1.01, 1.03, 1.07, 1.12, 1.2, 1.29, 1.44], dtype=float)
    cm_poly = np.polyfit(mach, delta_cm, 2)
    dm = float(np.polyval(cm_poly, float(np.asarray(aero["MACH"], dtype=float).reshape(-1)[0])))

    zu = np.asarray(bd["ZU"], dtype=float).reshape(-1)
    zl = np.asarray(bd["ZL"], dtype=float).reshape(-1)
    zc = (zu + zl) / 2.0
    dzc = zc[1:] - zc[:-1]
    dzc_seg = np.concatenate([dzc[fwd], dzc[aft]])
    alpha0l = float(np.asarray(wg.get("alpha0L", 0), dtype=float).reshape(-1)[0])
    aw = alpha0l - float(wg.get("i", 0) or 0)
    ib = -np.degrees(np.arctan(dzc_seg / dx_seg))
    cm0 = (
        bd["dk"] / (36.5 * s_ref * cbar) * float(np.sum(wf_seg**2 * (aw + ib) * dx_seg)) * dm
    )
    bd["Cm0"] = cm0 - bd["Cma"] * aw


def body_stability(ac: Aircraft, method: str) -> dict:
    """Return BD copy with ``Cma`` and ``Cm0`` from the chosen method."""
    bd = copy.deepcopy(ac.BD)
    if method == "Gilruth_White":
        _gilruth_white(bd, ac.WG)
    elif method == "Multhopp":
        _multhopp(ac, bd)
    else:
        raise ValueError(f"unknown body stability method: {method!r}")
    return bd
