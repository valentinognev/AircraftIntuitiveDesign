"""Port of Tornado coeff_create3.m (coefficients + derivatives)."""

from __future__ import annotations

import copy

import numpy as np

from aid.axes import to_frd
from aid.tornado.isa import isa_atmosphere
from aid.tornado.lattice import _config

__all__ = ["coeff_create"]


def _tarea(xyz: np.ndarray) -> np.ndarray:
    """Panel areas — port of nested tarea() in coeff_create3.m."""
    xyz = np.asarray(xyz, dtype=float)
    p1 = xyz[:, 0, :]
    p2 = xyz[:, 1, :]
    p3 = xyz[:, 2, :]
    p4 = xyz[:, 3, :]

    a = p2 - p1
    b = p4 - p1
    c = p2 - p3
    d = p4 - p3

    ar1 = np.linalg.norm(np.cross(b, a, axis=1), axis=1) / 2.0
    ar2 = np.linalg.norm(np.cross(c, d, axis=1), axis=1) / 2.0
    return ar1 + ar2


def _f_sonic_cp(state: dict) -> float:
    """Port of fSonicCP.m."""
    atm = isa_atmosphere(state["ALT"])
    sos = atm["a"]
    return 1.0 - sos**2 / float(state["AS"]) ** 2


def coeff_create(results: dict, lattice: dict, state: dict, ref: dict, geo: dict) -> dict:
    """Compute aerodynamic coefficients and derivatives from solver output."""
    results = copy.copy(results)

    q = 0.5 * float(state["rho"]) * float(state["AS"]) ** 2

    f = np.asarray(results["F"], dtype=float)
    force = np.asarray(results["FORCE"], dtype=float)
    moments = np.asarray(results["MOMENTS"], dtype=float)
    m = np.asarray(results["M"], dtype=float)
    normals = np.asarray(lattice["N"], dtype=float)
    xyz = np.asarray(lattice["XYZ"], dtype=float)

    npan = f.shape[0]
    n_deriv = force.shape[0]

    normal_force = np.einsum("ij,ij->i", f[:, 0, :], normals)
    panel_area = _tarea(xyz)
    stat_press = normal_force / panel_area
    cp = (stat_press / q).reshape(-1, 1)

    sonic_cp = _f_sonic_cp(state)
    sonic = np.flatnonzero(cp.ravel() < sonic_cp)
    sonicpanels = np.zeros(cp.shape, dtype=float)
    if sonic.size == 0:
        sonic_warning = 0
    else:
        sonic_warning = 1
        sonicpanels[sonic] = 1.0

    s_ref = float(ref["S_ref"])
    b_ref = float(ref["b_ref"])
    c_mac = float(ref["C_mac"])

    cx = force[:, 0] / (q * s_ref)
    cy = force[:, 1] / (q * s_ref)
    cz = force[:, 2] / (q * s_ref)

    alpha = float(state["alpha"])
    betha = float(state["betha"])
    b2w = np.array(
        [
            [
                np.cos(betha) * np.cos(alpha),
                -np.sin(betha),
                np.cos(betha) * np.sin(alpha),
            ],
            [
                np.cos(alpha) * np.sin(betha),
                np.cos(betha),
                np.sin(betha) * np.sin(alpha),
            ],
            [-np.sin(alpha), 0.0, np.cos(alpha)],
        ],
        dtype=float,
    )
    lemma = (b2w @ force.T).T

    d = lemma[:, 0]
    c_side = lemma[:, 1]
    lift = lemma[:, 2]

    cl = lift / (q * s_ref)
    cd = d / (q * s_ref)
    cc = c_side / (q * s_ref)

    cl_m = moments[:, 0] / (q * s_ref * b_ref)
    cm = moments[:, 1] / (q * s_ref * c_mac)
    cn = moments[:, 2] / (q * s_ref * b_ref)

    npan_per_wing = np.cumsum(
        np.sum((geo["nx"] + geo["fnx"]) * geo["ny"], axis=1) * (geo["symetric"] + 1)
    )
    index1 = 0
    cl_wing = []
    cd_wing = []
    cy_wing = []
    for i in range(int(geo["nwing"])):
        index2 = int(npan_per_wing[i])
        wing_force = np.sum(f[index1:index2, 0, :], axis=0)
        lemma2 = b2w @ wing_force
        cl_wing.append(lemma2[2] / (q * s_ref))
        cd_wing.append(lemma2[0] / (q * s_ref))
        cy_wing.append(lemma2[1] / (q * s_ref))
        index1 = index2

    delta = _config("delta")
    fac1 = b_ref / (2.0 * float(state["AS"]))
    fac2 = c_mac / (2.0 * float(state["AS"]))

    dcx = (cx - cx[0]) / delta
    dcy = (cy - cy[0]) / delta
    dcz = (cz - cz[0]) / delta
    dcl = (cl - cl[0]) / delta
    dcd = (cd - cd[0]) / delta
    dcc = (cc - cc[0]) / delta
    dcl_m = (cl_m - cl_m[0]) / delta
    dcm = (cm - cm[0]) / delta
    dcn = (cn - cn[0]) / delta

    out = {
        **results,
        "cp": cp,
        "sonicpanels": sonicpanels,
        "sonicWarning": sonic_warning,
        "L": float(lift[0]),
        "D": float(d[0]),
        "C": float(c_side[0]),
        "CX": float(cx[0]),
        "CY": float(cy[0]),
        "CZ": float(cz[0]),
        "CL": float(cl[0]),
        "CD": float(cd[0]),
        "CC": float(cc[0]),
        "Cl": float(cl_m[0]),
        "Cm": float(cm[0]),
        "Cn": float(cn[0]),
        "CLwing": np.asarray(cl_wing, dtype=float),
        "CDwing": np.asarray(cd_wing, dtype=float),
        "CYwing": np.asarray(cy_wing, dtype=float),
        "F": f[:, 0, :],
        "M": m[:, 0, :],
        "FORCE": force[0, :],
        "MOMENTS": moments[0, :],
        "CL_a": float(dcl[1]),
        "CD_a": float(dcd[1]),
        "CC_a": float(dcc[1]),
        "CX_a": float(dcx[1]),
        "CY_a": float(dcy[1]),
        "CZ_a": float(dcz[1]),
        "Cl_a": float(dcl_m[1]),
        "Cm_a": float(dcm[1]),
        "Cn_a": float(dcn[1]),
        "CL_b": float(dcl[2]),
        "CD_b": float(dcd[2]),
        "CC_b": float(dcc[2]),
        "CX_b": float(dcx[2]),
        "CY_b": float(dcy[2]),
        "CZ_b": float(dcz[2]),
        "Cl_b": float(dcl_m[2]),
        "Cm_b": float(dcm[2]),
        "Cn_b": float(dcn[2]),
        "CL_P": float(dcl[3] / fac1),
        "CD_P": float(dcd[3] / fac1),
        "CC_P": float(dcc[3] / fac1),
        "CX_P": float(dcx[3] / fac1),
        "CY_P": float(dcy[3] / fac1),
        "CZ_P": float(dcz[3] / fac1),
        "Cl_P": float(dcl_m[3] / fac1),
        "Cm_P": float(dcm[3] / fac1),
        "Cn_P": float(dcn[3] / fac1),
        "CL_Q": float(dcl[4] / fac2),
        "CD_Q": float(dcd[4] / fac2),
        "CC_Q": float(dcc[4] / fac2),
        "CX_Q": float(dcx[4] / fac2),
        "CY_Q": float(dcy[4] / fac2),
        "CZ_Q": float(dcz[4] / fac2),
        "Cl_Q": float(dcl_m[4] / fac2),
        "Cm_Q": float(dcm[4] / fac2),
        "Cn_Q": float(dcn[4] / fac2),
        "CL_R": float(dcl[5] / fac1),
        "CD_R": float(dcd[5] / fac1),
        "CC_R": float(dcc[5] / fac1),
        "CX_R": float(dcx[5] / fac1),
        "CY_R": float(dcy[5] / fac1),
        "CZ_R": float(dcz[5] / fac1),
        "Cl_R": float(dcl_m[5] / fac1),
        "Cm_R": float(dcm[5] / fac1),
        "Cn_R": float(dcn[5] / fac1),
    }

    if sonic_warning:
        out["sonicCP"] = sonic_cp
        out["sonicFraction"] = float(sonic.size / normals.shape[0])

    if n_deriv > 6:
        out["CL_d"] = dcl[6:]
        out["CD_d"] = dcd[6:]
        out["CC_d"] = dcc[6:]
        out["CX_d"] = dcx[6:]
        out["CY_d"] = dcy[6:]
        out["CZ_d"] = dcz[6:]
        out["Cl_d"] = dcl_m[6:]
        out["Cm_d"] = dcm[6:]
        out["Cn_d"] = dcn[6:]

    # Tornado's body frame is x aft, y right, z up, so CX/CZ and Cl/Cn -- and the
    # alpha, beta and control derivatives that inherit their channel's frame --
    # come out mirrored. The wind-axis CL/CD/CC/Cm, the p/q/r rate derivatives
    # (already standard) and the raw solver vectors are not in the map. `cp` is
    # built from FORCE before this point, so FORCE staying raw is what makes it
    # reproducible.
    return to_frd("tornado", out)
