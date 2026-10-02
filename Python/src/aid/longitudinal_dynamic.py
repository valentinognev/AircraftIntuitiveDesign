"""Longitudinal dynamic stability derivatives and modes.

Port of ``Matlab/fsroot/code/Longitudinal_Dynamic_Stability.m``.
``prop = 1`` (``CXu = -CDu - 3*CD``). No plots.
"""

from __future__ import annotations

import numpy as np

_G = 32.17


def longitudinal_dynamic(state: dict) -> dict:
    """Body-axis A, B and short-period / phugoid eigenvalues.

    ``state`` keys: WT, YI, MACH, ALT, Q, a_sound, S, cbar, CD0, K, CL, CLa,
    Cma, CLde, Cmde, ht_a, eta, ht_V, dwash, ht_l.
    Fixed zeros: CDu, CXadot, CXq, CXt, CXde, CZt, Cmu. g = 32.17.
    """
    prop = 1

    m = float(state["WT"]) / _G
    iy = float(state["YI"])
    mach = float(state["MACH"])
    u = mach * float(state["a_sound"])
    q = float(state["Q"])
    s = float(state["S"])
    cbar = float(state["cbar"])
    cl = float(state["CL"])
    cla = float(state["CLa"])
    k = float(state["K"])

    cd = float(state["CD0"]) + k * cl**2
    cda = 2.0 * k * cl * cla

    cdu = 0.0
    if prop:
        cxu = -cdu - 3.0 * cd
    else:
        cxu = -cdu - 2.0 * cd
    cxa = cl - cda
    cxadot = 0.0
    cxq = 0.0
    cxt = 0.0
    cxde = 0.0

    xu = cxu * q * s / (m * u)
    xa = cxa * q * s / m

    clu = mach**2 / (1.0 - mach**2) * cl
    czu = -clu - 2.0 * cl
    cza = -cla - cd
    ht_a = float(state["ht_a"])
    eta = float(state["eta"])
    ht_v = float(state["ht_V"])
    dwash = float(state["dwash"])
    ht_l = float(state["ht_l"])
    cladop = 2.0 * ht_a * eta * ht_v * dwash * 1.1
    czadot = -cladop
    clq = 2.0 * ht_a * eta * ht_v * 1.1
    czq = -clq
    czde = -float(state["CLde"])
    czt = 0.0

    zu = czu * q * s / (m * u)
    za = cza * q * s / m

    cmu = 0.0
    cma = float(state["Cma"])
    cmadot = -2.0 * ht_a * eta * ht_v * dwash * ht_l / cbar * 1.1
    cmq = -2.0 * ht_a * eta * ht_v * ht_l / cbar * 1.1
    cmde = float(state["Cmde"])

    mu = cmu * q * s * cbar / (iy * u)
    ma = cma * q * s * cbar / iy
    madot = cmadot * q * s * cbar**2 / (2.0 * iy * u)
    mq = cmq * q * s * cbar**2 / (2.0 * iy * u)

    c1 = cbar / (2.0 * u)
    m1 = 2.0 * m / (q / u * s)
    iy1 = iy / (q * s * cbar)
    zeta1 = (cxadot * c1) / (m1 - czadot * c1)
    zeta2 = (cmadot * c1) / (m1 - czadot * c1)

    a = np.zeros((4, 4))
    a[0, 0] = (cxu + zeta1 * czu) / m1
    a[0, 1] = (cxa + zeta1 * cza) / m1
    a[0, 2] = (cxq * cl + zeta1 * (m1 + czq * c1)) / m1
    a[0, 3] = (cxt + zeta1 * czt) / m1
    a[1, 0] = czu / (m1 - czadot * c1)
    a[1, 1] = cza / (m1 - czadot * c1)
    a[1, 2] = (m1 + czq * c1) / (m1 - czadot * c1)
    a[1, 3] = czt / (m1 - c1 * czadot * c1)
    a[2, 0] = (cmu + zeta2 * czu) / iy1
    a[2, 1] = (cma + zeta2 * cza) / iy1
    a[2, 2] = (cmq * cl + zeta2 * (m1 + czq * c1)) / iy1
    a[2, 3] = zeta2 * czt / iy1
    a[3, 2] = 1.0

    b = np.zeros((4, 1))
    b[0, 0] = (cxde + zeta1 * czde) / m1
    b[1, 0] = czde / (m1 - c1 * czadot)
    b[2, 0] = (cmde + zeta2 * czde) / iy1

    ashort = np.array(
        [
            [za / u, 1.0],
            [ma + (madot * za) / u, mq + madot],
        ]
    )
    aphu = np.array(
        [
            [xu, _G],
            [-zu / u, 0.0],
        ]
    )

    return {
        "A": a,
        "B": b,
        "short_period": np.linalg.eigvals(ashort),
        "phugoid": np.linalg.eigvals(aphu),
        "Xu": xu,
        "Xa": xa,
        "Zu": zu,
        "Za": za,
        "Mu": mu,
        "Ma": ma,
        "Mq": mq,
        "Madot": madot,
        "CDu": cdu,
        "CDa": cda,
        "CLu": clu,
        "CLadot": cladop,
        "CLq": clq,
        "CD": cd,
        "CL": cl,
    }
