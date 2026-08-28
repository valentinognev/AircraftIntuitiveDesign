"""Handbook longitudinal static stability from stored planform/aero fields.

Ports ``AID.m`` CG/MAC text and ``Longitudinal_Static_Stability.m`` (trim off).
"""

from __future__ import annotations

import math

import numpy as np

from aid.aircraft import Aircraft
from aid.atmosphere import atmosphere
from aid.body_stability import body_stability
from aid.downwash import downwash


def _last(val) -> float:
    return float(np.asarray(val, dtype=float).reshape(-1)[-1])


def _per_deg(a: float) -> float:
    if a > 1:
        return a * math.pi / 180.0
    return a


def _scalar_delta(val) -> float | None:
    if val is None or isinstance(val, (list, tuple, np.ndarray)):
        arr = np.asarray(val).reshape(-1) if val is not None else np.array([])
        if arr.size != 1:
            return None
        return float(arr[0])
    return float(val)


def _control_derivatives(ac: Aircraft, *, eta: float, ht_l: float) -> tuple[float, float]:
    """Elevator lift and pitching-moment derivatives (Controls.m)."""
    wg, ht, elev = ac.WG, ac.HT, ac.E
    wg_a = _per_deg(float(wg["a"]))
    ht_a = _per_deg(float(ht["a"]))
    s_ref = _last(wg["S"])
    cbar = _last(wg["cbar"])
    tau = float(elev.get("tau", 0) or 0)
    clde = ht_a * eta * _last(ht["S"]) / s_ref * tau
    cmde = -ht_l / cbar * clde
    return clde, cmde


def apply_stability_settings(
    ac: Aircraft,
    *,
    slipstream: bool = False,
    slipstream_data: tuple[float, float] = (0.5, 0.9),
    multhopp: bool = True,
) -> None:
    """Apply Calculations menu slipstream and body-method settings to *ac*."""
    if slipstream:
        dw = downwash(ac)
        ac.HT["dwash"] = dw["dwash"]
        ac.HT["eta"] = dw["eta"]
    else:
        ac.HT["dwash"] = float(slipstream_data[0])
        ac.HT["eta"] = float(slipstream_data[1])

    method = "Multhopp" if multhopp else "Gilruth_White"
    bd = body_stability(ac, method)
    ac.BD["Cma"] = bd["Cma"]
    ac.BD["Cm0"] = bd["Cm0"]


def _lift_moment_terms(
    ac: Aircraft,
    *,
    wg: dict,
    ht: dict,
    bd: dict,
    aero: dict,
    htail: bool,
    body: bool,
    cbar: float,
    s_ref: float,
    x_cg: float,
    x_ac: float,
    wg_a: float,
    tlt: float,
    dwash: float,
    cla: float,
    ht_l: float,
    cl: float,
    alschd: np.ndarray,
    k_w: float,
    kt: float,
) -> dict:
    """Lift and moment at current incidence/controls (Longitudinal_Static_Stability.m fall-through)."""
    i_w = float(wg.get("i", 0) or 0)
    i_h = float(ht.get("i", 0) or 0)
    a0l = float(wg.get("alpha0L", wg.get("alpha0", 0)) or 0)
    wg_cl0 = wg_a * (i_w - a0l)
    f_delta = _scalar_delta(ac.F.get("DELTA"))
    if f_delta is not None:
        wg_cl0 += wg_a * f_delta * float(ac.F.get("tau", 0) or 0)
    ht_cl0 = tlt * (i_h - dwash * (i_w - a0l)) if htail else 0.0
    e_delta = _scalar_delta(ac.E.get("DELTA"))
    if htail and e_delta is not None:
        ht_cl0 += tlt * e_delta * float(ac.E.get("tau", 0) or 0)
    cl0 = wg_cl0 + (ht_cl0 if htail else 0.0)

    if alschd.size == 1:
        alpha = float(alschd[0])
    else:
        alpha = (cl - cl0) / cla if cla else 0.0

    cl_wg = wg_a * (i_w - a0l) + wg_a * alpha
    z_wg = (float(aero.get("ZCG", 0) or 0) - float(wg["Z"])) / cbar
    l_ac = ht_l + cbar * (x_cg - x_ac)
    num = (1 + kt) * x_ac - cl_wg * (1 / (180 / math.pi * wg_a) - 2 * k_w) * z_wg
    if htail:
        num += kt * l_ac / cbar
    if body and "Cma" in bd and cla:
        num -= float(bd["Cma"]) / cla
    n0 = num / (1 + kt) if (1 + kt) else x_ac
    cm_cl = x_cg - n0

    wg_cm = float(wg.get("Cm", 0) or 0)
    wg_cm0 = wg_cm + wg_a * (i_w - a0l) * (x_cg - x_ac)
    if f_delta is not None and "l" in ac.F:
        wg_cm0 -= wg_a * f_delta * float(ac.F.get("tau", 0) or 0) * float(ac.F["l"]) / cbar
    ht_cm0 = -ht_l / cbar * ht_cl0 if htail else 0.0
    cm0 = wg_cm0 + ht_cm0
    if body and "Cm0" in bd:
        cm0 += float(bd["Cm0"])

    if cm_cl > 0:
        line2 = "Aircraft is unstable"
    else:
        line2 = f"Aircraft is {abs(cm_cl) * 100:.0f}% stable"

    return {
        "N0": n0,
        "Cm_CL": cm_cl,
        "CL0": cl0,
        "Cm0": cm0,
        "alpha": alpha,
        "summary": [f"CG at {x_cg * 100:.0f}% MAC:", line2],
    }


def _trim_elevator(ac: Aircraft, st: dict, *, ht_l: float, htail: bool) -> None:
    """Trim mode 1: solve elevator deflection (Longitudinal_Static_Stability.m)."""
    if not htail:
        return
    _, cmde = _control_derivatives(ac, eta=float(ac.HT.get("eta", 0.9)), ht_l=ht_l)
    if cmde == 0:
        return
    cm_total = st["Cm0"] + st["Cma"] * st["alpha"]
    if abs(cm_total) < 1e-3:
        return
    e_delta = _scalar_delta(ac.E.get("DELTA")) or 0.0
    cm = cm_total - cmde * e_delta
    ac.E["DELTA"] = -cm / cmde


def aircraft_stability(
    ac: Aircraft,
    *,
    slipstream: bool | None = None,
    slipstream_data: tuple[float, float] = (0.5, 0.9),
    multhopp: bool | None = None,
    trim_mode: int = 0,
) -> dict:
    """Return CG fraction, static margin, CL/Cm slopes, CD0, and summary lines."""
    if slipstream is not None or multhopp is not None:
        apply_stability_settings(
            ac,
            slipstream=bool(slipstream) if slipstream is not None else False,
            slipstream_data=slipstream_data,
            multhopp=True if multhopp is None else bool(multhopp),
        )

    wg, ht, bd, aero = ac.WG, ac.HT, ac.BD, ac.AERO
    flags = list(ac.plot_cmp) + [0, 0, 0, 0]
    htail = bool(flags[1])
    body = bool(flags[3])

    cbar = _last(wg["cbar"])
    s_ref = _last(wg["S"])
    xmac = _last(wg.get("xmac", 0))
    x_cg = (float(aero["XCG"]) - float(wg["X"]) - xmac) / cbar

    wg_a = _per_deg(float(wg["a"]))
    ht_a = _per_deg(float(ht["a"]))
    eta = float(ht.get("eta", 0.9))
    dwash = float(ht.get("dwash", 0.5))
    tlt = ht_a * eta * _last(ht["S"]) / s_ref
    cla = wg_a + tlt * (1 - dwash) if htail else wg_a

    x_ac = float(wg["x_ac"])
    ht_l = float(ht.get("l", 0))
    if "X" in ht and "x_ac" in ht:
        ht_l = (
            float(ht["X"])
            + float(ht["x_ac"]) * _last(ht["cbar"])
            + _last(ht.get("xmac", 0))
            - float(aero["XCG"])
        )

    cma = wg_a * (x_cg - x_ac)
    if htail:
        cma -= tlt * ht_l / cbar * (1 - dwash)
    if body and "Cma" in bd:
        cma += float(bd["Cma"])

    atm = atmosphere(float(np.asarray(aero["ALT"]).reshape(-1)[0]))
    q = 0.5 * atm["D"] * (float(np.asarray(aero["MACH"]).reshape(-1)[0]) * atm["a"]) ** 2
    if ac.unit == "in":
        q /= 144.0
    cl = float(aero["WT"]) / (q * s_ref)

    alschd = np.asarray(aero["ALSCHD"], dtype=float).reshape(-1)
    k_w = float(wg.get("K", 1 / (math.pi * float(wg.get("e", 1)) * _last(wg["AR"]))))
    kt = tlt / wg_a * (1 - dwash) if htail and wg_a else 0.0

    lm = _lift_moment_terms(
        ac,
        wg=wg,
        ht=ht,
        bd=bd,
        aero=aero,
        htail=htail,
        body=body,
        cbar=cbar,
        s_ref=s_ref,
        x_cg=x_cg,
        x_ac=x_ac,
        wg_a=wg_a,
        tlt=tlt,
        dwash=dwash,
        cla=cla,
        ht_l=ht_l,
        cl=cl,
        alschd=alschd,
        k_w=k_w,
        kt=kt,
    )
    cl0 = lm["CL0"]
    alpha = lm["alpha"]
    n0 = lm["N0"]
    cm_cl = lm["Cm_CL"]
    cm0 = lm["Cm0"]
    summary = lm["summary"]

    cd0 = 0.0
    if flags[0]:
        cd0 += float(wg.get("CD0", 0) or 0)
    if htail:
        cd0 += float(ht.get("CD0", 0) or 0)
    if flags[2]:
        cd0 += float(ac.VT.get("CD0", 0) or 0)
    if body:
        cd0 += float(bd.get("CD0", 0) or 0)
    for pt in ac.NP:
        if pt and "CD0" in pt:
            extra = float(pt["CD0"])
            if pt.get("Y"):
                extra *= 2
            cd0 += extra
    cd0 *= 1.25

    result = {
        "x_cg": x_cg,
        "N0": n0,
        "Cm_CL": cm_cl,
        "CL": cl,
        "CL0": cl0,
        "CLa": cla,
        "Cma": cma,
        "Cm0": cm0,
        "alpha": alpha,
        "CD0": cd0,
        "K": k_w,
        "S": s_ref,
        "WT": float(aero["WT"]),
        "MACH": float(np.asarray(aero["MACH"]).reshape(-1)[0]),
        "ALT": float(np.asarray(aero["ALT"]).reshape(-1)[0]),
        "unit": ac.unit,
        "Q": q,
        "D": atm["D"],
        "a_sound": atm["a"],
        "summary": summary,
    }

    if trim_mode == 1:
        _trim_elevator(ac, result, ht_l=ht_l, htail=htail)
        result.update(
            _lift_moment_terms(
                ac,
                wg=wg,
                ht=ht,
                bd=bd,
                aero=aero,
                htail=htail,
                body=body,
                cbar=cbar,
                s_ref=s_ref,
                x_cg=x_cg,
                x_ac=x_ac,
                wg_a=wg_a,
                tlt=tlt,
                dwash=dwash,
                cla=cla,
                ht_l=ht_l,
                cl=cl,
                alschd=alschd,
                k_w=k_w,
                kt=kt,
            )
        )

    return result


def stability_lines(st: dict, n: int = 100) -> dict:
    alim = [min(-10.0, st["alpha"]), max(20.0, st["alpha"])]
    alpha = np.linspace(alim[0], alim[1], n)
    cla, cma = st["CLa"], st["Cm_CL"] * st["CLa"]
    return {
        "alpha": alpha,
        "CL": st["CL0"] + cla * alpha,
        "Cm": st["Cm0"] + cma * alpha,
        "CL_trim": st["CL0"] + cla * st["alpha"],
        "Cm_trim": st["Cm0"] + cma * st["alpha"],
    }


def drag_vs_speed(st: dict) -> dict:
    """Port of AID.m Aerodynamics drag plot (stall to 1.2 V_tr)."""
    d = st["D"]
    s = st["S"]
    v_stall = math.sqrt(st["WT"] / (d * s))
    v_tr = st["MACH"] * st["a_sound"]
    if st["unit"] == "in":
        v_stall *= 12
    if 1.2 * max(v_tr, 1e-9) / st["a_sound"] > 1:
        v_max = 0.9 * st["a_sound"]
    elif 1.2 * v_tr > v_stall:
        v_max = 1.2 * v_tr
    else:
        v_max = 2 * v_stall
    v = np.linspace(v_stall, v_max, 80)
    q = 0.5 * d * v**2
    if st["unit"] == "in":
        q = q / 144.0
    cl = st["WT"] / (q * s)
    if st["unit"] == "in":
        cl = cl * 144.0
    cdi = st["K"] * cl**2
    d0 = st["CD0"] * q * s
    di = cdi * q * s
    kts = st["unit"] != "in"
    v_plot = v / 1.68781 if kts else v
    v_tr_plot = v_tr / 1.68781 if kts else v_tr
    return {
        "v": v_plot,
        "D_i": di,
        "D_0": d0,
        "D": d0 + di,
        "v_tr": v_tr_plot,
        "xlabel": "Velocity (knots)" if kts else "Velocity (ft/s)",
        "cd_eq": f"{st['CD0']:.3f} + {st['K']:.3f}",
    }
