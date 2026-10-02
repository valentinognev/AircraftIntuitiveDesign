import math

import numpy as np

from aid.aircraft import Aircraft
from aid.atmosphere import atmosphere


def _last(val) -> float:
    return float(np.asarray(val).reshape(-1)[-1])


def _reynolds(pt: dict, atm: dict) -> float:
    if "Re" in atm:
        return float(atm["Re"])
    mach = atm.get("MACH", pt.get("MACH", 0.03))
    return float(atm["D"] * mach * atm["a"] / atm["V"])


def drag(pt: dict, unit: str, atm: dict, wg_sref: float) -> dict:
    re = _reynolds(pt, atm)

    if "NACA" in pt:
        tc = float(pt["TC"])
        s = _last(pt["S"])
        cbar = _last(pt["cbar"])

        s_wet = (1.977 + 0.52 * tc) * s

        x_tmax = 0.2
        l_factor = 2 if x_tmax < 0.3 else 1.2

        re_cbar = re * cbar
        if unit == "in":
            re_cbar /= 12
        cf = 0.455 / math.log10(re_cbar) ** 2.58

        rls = 1.3
        pt["CD0"] = cf * (1 + l_factor * tc + tc**4) * rls * s_wet / wg_sref
    else:
        zu = np.asarray(pt["ZU"], dtype=float)
        zl = np.asarray(pt["ZL"], dtype=float)
        r = np.asarray(pt["R"], dtype=float)
        x = np.asarray(pt["X"], dtype=float)

        h = (zu - zl) / 2
        p = 2 * math.pi * np.sqrt((h**2 + r**2) / 2)
        dx = x[1:] - x[:-1]
        s_wet = float(np.sum((p[:-1] + p[1:]) / 2 * dx))

        re_l = re * float(x[-1])
        if unit == "in":
            re_l /= 12
        cf = 0.455 / math.log10(re_l) ** 2.58

        l_d = float(x[-1]) / max(float(np.max(2 * r)), float(np.max(zu - zl)))
        pt["CD0"] = cf * (1 + 60 / l_d**3 + 0.0025 * l_d) * s_wet / wg_sref

    return pt


def _on(val) -> bool:
    return bool(val)


def _extra_parts(parts, n: int):
    if not isinstance(parts, list):
        return
    for pt in parts[:n]:
        if isinstance(pt, dict) and pt:
            yield pt


def aircraft_cd0(ac: Aircraft) -> float:
    """AID.m lines 882-902. Sum Drag() over wing, HT, VT, body, NP, NB when plot_cmp (and extra slots) are on.
    Twin if NP.Y or NB.Y0 is truthy. Return 1.25 * sum. Writes each part['CD0']."""
    alt = float(np.asarray(ac.AERO["ALT"]).reshape(-1)[0])
    mach = float(np.asarray(ac.AERO["MACH"]).reshape(-1)[0])
    atm = atmosphere(alt)
    atm["Q"] = 0.5 * atm["D"] * (mach * atm["a"]) ** 2
    if ac.unit == "in":
        atm["Q"] /= 144.0
    atm["Re"] = atm["D"] * mach * atm["a"] / atm["V"]
    sref = float(np.asarray(ac.WG["S"]).reshape(-1)[-1])

    total = 0.0
    primaries = (ac.WG, ac.HT, ac.VT, ac.BD)
    for i, pt in enumerate(primaries):
        if i < len(ac.plot_cmp) and _on(ac.plot_cmp[i]):
            drag(pt, ac.unit, atm, sref)
            total += float(pt["CD0"])
    for pt in _extra_parts(ac.NP, 4):
        drag(pt, ac.unit, atm, sref)
        if _on(pt.get("Y")):
            pt["CD0"] = float(pt["CD0"]) * 2
        total += float(pt["CD0"])
    for pt in _extra_parts(ac.NB, 2):
        drag(pt, ac.unit, atm, sref)
        if _on(pt.get("Y0")):
            pt["CD0"] = float(pt["CD0"]) * 2
        total += float(pt["CD0"])
    return 1.25 * total
