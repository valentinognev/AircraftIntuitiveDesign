"""AID.m handbook sequence: geometry, section slopes, aero, drag, lateral, trim, dynamics."""

from __future__ import annotations

import math

import numpy as np
from scipy.interpolate import CubicSpline

from aid.aero import aero
from aid.aircraft import Aircraft
from aid.atmosphere import atmosphere
from aid.drag import aircraft_cd0
from aid.geometry import geometry
from aid.handbook_controls import stamp_control_geometry
from aid.lateral import lat_dir_corrections, lateral_dynamic, lateral_static
from aid.longitudinal_dynamic import longitudinal_dynamic
from aid.section_aero import section_slopes
from aid.stability import aircraft_stability
from aid.trim import trim_incidence


def apply_handbook(
    ac: Aircraft,
    *,
    angl: bool,
    slipstream: bool,
    slipstream_data: tuple[float, float],
    multhopp: bool,
    trim_mode: int,
    trim_fix: str,
) -> dict:
    """Order, matching AID.m:

    1. geometry() on WG, HT, VT (``type='v'``), and non-empty NP.
    2. section_slopes() on WG (indexes 0 and 1 if two NACA codes), HT index 0, VT index 0.
    3. aero() on WG and HT at MACH[0].
    4. stamp_control_geometry().
    5. aircraft_cd0() assigned to the returned 'CD0' (do not leave the stored-field sum).
    6. lat_dir_corrections, then lateral_static, then lateral_dynamic.
       Clb from lateral_static already includes WG['Clb_wing']; do not add it again.
    7. aircraft_stability(..., trim_mode=1 if trim_mode==1 else 0).
    8. If trim_mode==2, trim_incidence(..., fix=trim_fix), write i_wg/i_ht/alpha onto the
       aircraft, then recompute the lift terms via a second aircraft_stability call with
       trim_mode 0.
    9. longitudinal_dynamic on the stability scalars plus CLde/Cmde from stamp/handbook.

    ``trim_fix`` is ``'both'``, ``'wing'``, or ``'ht'`` and comes from which incidence box
    the user is editing. ``'wing'`` holds HT incidence and solves wing incidence;
    ``'ht'`` holds wing incidence and solves HT incidence. If neither box is the edit
    source, pass ``'ht'`` when ``ALSCHD`` has more than one value (MATLAB default
    ``HT.i = []``) and ``'both'`` when ``ALSCHD`` is a scalar. This function uses the
    ``trim_fix`` argument as given. ``MainWindow.apply_calculations`` passes ``'both'``.

    Returns the stability dict plus 'lateral' and 'dynamic'.
    """
    geometry(ac.WG, angl)
    geometry(ac.HT, angl)
    geometry(ac.VT, angl, "v")
    for pt in ac.NP or []:
        if isinstance(pt, dict) and pt:
            geometry(pt, angl)

    _section_pass(ac.WG)
    section_slopes(ac.HT, 0)
    section_slopes(ac.VT, 0)

    mach = float(np.asarray(ac.AERO["MACH"], dtype=float).reshape(-1)[0])
    aero(ac.WG, mach, angl)
    aero(ac.HT, mach, angl)
    stamp_control_geometry(ac)
    cd0 = aircraft_cd0(ac)

    _equivalent_diameter(ac)
    cl = _lateral_cl(ac)
    lat_dir_corrections(ac, mach)
    lateral = lateral_static(ac, angl, cl)
    lateral.update(lateral_dynamic(ac, cl, float(lateral["CYb"])))

    stability_trim = 1 if trim_mode == 1 else 0
    st = _stability(
        ac,
        slipstream=slipstream,
        slipstream_data=slipstream_data,
        multhopp=multhopp,
        trim_mode=stability_trim,
    )
    if trim_mode == 2:
        ac.HT["l"] = _ht_arm(ac)
        flags = list(ac.plot_cmp) + [0, 0, 0, 0]
        solved = trim_incidence(
            ac,
            htail=bool(flags[1]),
            body=bool(flags[3]),
            fix=trim_fix,
        )
        ac.WG["i"] = solved["i_wg"]
        ac.HT["i"] = solved["i_ht"]
        ac.AERO["alpha"] = solved["alpha"]
        alschd = np.asarray(ac.AERO["ALSCHD"], dtype=float).reshape(-1)
        if alschd.size == 1:
            ac.AERO["ALSCHD"] = solved["alpha"]
        st = _stability(
            ac,
            slipstream=slipstream,
            slipstream_data=slipstream_data,
            multhopp=multhopp,
            trim_mode=0,
        )
    st["CD0"] = cd0
    st["lateral"] = lateral
    st["dynamic"] = longitudinal_dynamic(_dynamic_state(ac, st))
    return st


def _section_pass(pt: dict) -> None:
    naca = pt.get("NACA")
    section_slopes(pt, 0)
    if isinstance(naca, (list, tuple)) and len(naca) >= 2 and naca[1]:
        section_slopes(pt, 1)


def _stability(ac: Aircraft, **kwargs) -> dict:
    return aircraft_stability(ac, **kwargs)


def _last(val) -> float:
    return float(np.asarray(val, dtype=float).reshape(-1)[-1])


def _per_rad(a: float) -> float:
    if a > 1.0:
        return a * math.pi / 180.0
    return a


def _equivalent_diameter(ac: Aircraft) -> None:
    """AID.m lines 730-732. The Cessna .mat does not store BD.d_eq."""
    bd, wg = ac.BD, ac.WG
    if "X" not in bd or "S" not in bd or "CHRDR" not in wg:
        return
    x = np.asarray(bd["X"], dtype=float).reshape(-1)
    area = np.asarray(bd["S"], dtype=float).reshape(-1)
    n = min(x.size, area.size)
    x, area = x[:n], area[:n]
    if n < 2:
        return
    order = np.argsort(x, kind="mergesort")
    x, area = x[order], area[order]
    uniq = np.empty(x.shape[0], dtype=bool)
    uniq[0] = True
    uniq[1:] = np.diff(x) > 0.0
    x, area = x[uniq], area[uniq]
    if x.size < 2:
        return
    spl = CubicSpline(x, area, extrapolate=True)
    s_le = float(spl(float(wg["X"])))
    s_te = float(spl(float(wg["X"]) + float(wg["CHRDR"])))
    mean = max((s_le + s_te) / 2.0, 0.0)
    bd["d_eq"] = 2.0 * math.sqrt(mean / math.pi)


def _lateral_cl(ac: Aircraft) -> float:
    """CL lat_dir_corrections will read. Set AERO.CL from weight when both are absent."""
    if ac.WG.get("CL") is not None:
        return _last(ac.WG["CL"])
    if ac.AERO.get("CL") is not None:
        return _last(ac.AERO["CL"])
    alt = float(np.asarray(ac.AERO["ALT"], dtype=float).reshape(-1)[0])
    mach = float(np.asarray(ac.AERO["MACH"], dtype=float).reshape(-1)[0])
    atm = atmosphere(alt)
    q = 0.5 * atm["D"] * (mach * atm["a"]) ** 2
    if ac.unit == "in":
        q /= 144.0
    cl = float(ac.AERO["WT"]) / (q * _last(ac.WG["S"]))
    ac.AERO["CL"] = cl
    return cl


def _ht_arm(ac: Aircraft) -> float:
    """AID.m HT.l: X + x_ac*cbar(end) + xmac - XCG."""
    ht = ac.HT
    return (
        float(ht["X"])
        + float(ht["x_ac"]) * _last(ht["cbar"])
        + _last(ht.get("xmac", 0.0))
        - float(ac.AERO["XCG"])
    )


def _dynamic_state(ac: Aircraft, st: dict) -> dict:
    """Stability scalars plus Controls.m CLde and Cmde."""
    wg, ht = ac.WG, ac.HT
    cbar = _last(wg["cbar"])
    s_ref = _last(wg["S"])
    ht_s = _last(ht["S"])
    ht_l = _ht_arm(ac)
    ht_a = _per_rad(float(ht["a"]))
    eta = float(ht.get("eta", 0.9))
    tau = float(ac.E.get("tau", 0.0) or 0.0)
    clde = ht_a * eta * ht_s / s_ref * tau
    cmde = -ht_l / cbar * clde
    return {
        "WT": st["WT"],
        "YI": float(np.asarray(ac.AERO["YI"], dtype=float).reshape(-1)[0]),
        "MACH": st["MACH"],
        "ALT": st["ALT"],
        "Q": st["Q"],
        "a_sound": st["a_sound"],
        "S": st["S"],
        "cbar": cbar,
        "CD0": st["CD0"],
        "K": st["K"],
        "CL": st["CL"],
        "CLa": st["CLa"],
        "Cma": st["Cma"],
        "CLde": clde,
        "Cmde": cmde,
        "ht_a": ht_a,
        "eta": eta,
        "ht_V": ht_s * ht_l / (s_ref * cbar),
        "dwash": float(ht.get("dwash", 0.5)),
        "ht_l": ht_l,
    }
