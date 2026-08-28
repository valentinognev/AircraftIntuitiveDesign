"""Horizontal-tail downwash gradient and efficiency factor.

Port of ``Matlab/fsroot/code/Downwash.m``.
"""

from __future__ import annotations

import math

import numpy as np

from aid.aircraft import Aircraft
from aid.atmosphere import atmosphere
from aid.tornado_io import _swp_val


def _last(val) -> float:
    return float(np.asarray(val, dtype=float).reshape(-1)[-1])


def _dynamic_pressure(ac: Aircraft) -> float:
    aero = ac.AERO
    atm = atmosphere(float(aero["ALT"]))
    mach = float(np.asarray(aero["MACH"], dtype=float).reshape(-1)[0])
    q = 0.5 * atm["D"] * (mach * atm["a"]) ** 2
    if ac.unit == "in":
        q /= 144.0
    return q


def downwash(ac: Aircraft) -> dict:
    """Compute tail downwash gradient, efficiency, and wake geometry."""
    wg, ht, aero = ac.WG, ac.HT, ac.AERO

    ht_i = float(ht.get("i", -1))
    cbar_ht = _last(ht["cbar"])
    x_ac_ht = float(ht.get("x_ac", 0))
    xmac_ht = _last(ht.get("xmac", 0))
    wg_i = float(wg.get("i", 0) or 0)
    wg_chrdr = float(wg["CHRDR"])
    wg_x = float(wg["X"])
    wg_z = float(wg["Z"])

    ht_x = (
        float(ht["X"])
        + (xmac_ht + x_ac_ht * cbar_ht) * math.cos(math.radians(ht_i))
        - (wg_x + wg_chrdr * math.cos(math.radians(wg_i)))
    )
    ht_z = (
        float(ht["Z"])
        - (xmac_ht + x_ac_ht * cbar_ht) * math.sin(ht_i)
        - (wg_z - wg_chrdr * math.sin(wg_i))
    )

    h = (ht_x - ht_z * math.tan(math.radians(wg_i))) * math.sin(math.radians(wg_i)) + ht_z / math.cos(
        math.radians(wg_i)
    )
    l = (ht_x - ht_z * math.tan(math.radians(wg_i))) * math.cos(math.radians(wg_i)) + (
        wg_chrdr - (float(wg.get("Cm", 0)) + _last(wg["cbar"]) / 4.0)
    )

    ar = _last(wg["AR"])
    tr = _last(wg["TR"])
    b = float(wg["b"])
    swp_25 = _swp_val(wg, row=1, col=-1)

    k1 = 1.0 / ar - 1.0 / (1.0 + ar**1.7)
    k2 = (10.0 - 3.0 * tr) / 7.0
    k3 = (1.0 - h / b) / (2.0 * l / b) ** (1.0 / 3.0)
    dwash = 4.44 * (k1 * k2 * k3 * math.sqrt(math.cos(math.radians(swp_25)))) ** 1.19

    q = _dynamic_pressure(ac)
    cl = float(aero["WT"]) / (q * _last(wg["S"]))
    alpha = 0.0
    e = float(wg.get("e", 0.9))
    epsilon = 57.3 * 1.62 * cl / (math.pi * e * ar)

    tau = alpha + wg_i - epsilon
    z2 = ht_z - ht_x * math.tan(math.radians(tau))
    l_eta = ht_x / math.cos(math.radians(tau)) + z2 * math.sin(math.radians(tau))
    z_eta = z2 * math.cos(math.radians(tau))

    cbar = _last(wg["cbar"])
    cd0 = float(wg["CD0"])
    z_w = 0.68 * cbar * math.sqrt(cd0 * (0.15 + l_eta / cbar))

    if z_eta < z_w:
        dq0 = 2.42 * math.sqrt(cd0) / (0.3 + l_eta / cbar)
        dq = dq0 * math.cos(math.pi / 2.0 * z_eta / z_w) ** 2
        eta = 1.0 - dq
    else:
        eta = 1.0

    return {"dwash": dwash, "eta": eta, "Z_eta": z_eta, "Z_w": z_w}
