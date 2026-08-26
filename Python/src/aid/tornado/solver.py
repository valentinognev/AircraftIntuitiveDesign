"""Port of Tornado solver.m (VLM solver + fastdw + mega)."""

from __future__ import annotations

import copy

import numpy as np

from aid.tornado.boundary import set_boundary
from aid.tornado.isa import isa_atmosphere
from aid.tornado.lattice import _config

__all__ = ["solve"]

_ONE_BY_FOUR_PI = 1.0 / (4.0 * np.pi)


def _mega(r1: np.ndarray, r2: np.ndarray) -> np.ndarray:
    """Port of nested mega() in solver.m."""
    f1 = np.cross(r1, r2, axis=2)
    lf1 = np.sum(f1**2, axis=2)

    with np.errstate(divide="ignore", invalid="ignore"):
        f2 = f1 / lf1[..., np.newaxis]

        lr1 = np.sqrt(np.sum(r1**2, axis=2))
        lr2 = np.sqrt(np.sum(r2**2, axis=2))
        r1_hat = r1 / lr1[..., np.newaxis]
        r2_hat = r2 / lr2[..., np.newaxis]

        l1 = r2_hat - r1_hat
        r0 = r2 - r1
        radial_distance = np.sqrt(lf1 / np.sum(r0**2, axis=2))
        l2 = (
            r0[..., 0] * l1[..., 0]
            + r0[..., 1] * l1[..., 1]
            + r0[..., 2] * l1[..., 2]
        )
        dw = f2 * l2[..., np.newaxis]

    near = _config("near")
    mask = radial_distance < near
    dw2 = dw * (1.0 - mask[..., np.newaxis])
    dw2 = np.nan_to_num(dw2, nan=0.0, posinf=0.0, neginf=0.0)
    return dw2


def _fastdw(lattice: dict, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Port of fastdw() in solver.m (no waitbar)."""
    vortex = np.asarray(lattice["VORTEX"], dtype=float)
    colloc = np.asarray(lattice["COLLOC"], dtype=float)
    normals = np.asarray(lattice["N"], dtype=float)

    psize, vsize, _ = vortex.shape

    ldw = np.zeros((psize, psize, vsize - 1, 3))

    mcolloc = np.stack(
        [
            np.broadcast_to(colloc[:, 0:1], (psize, psize)),
            np.broadcast_to(colloc[:, 1:2], (psize, psize)),
            np.broadcast_to(colloc[:, 2:3], (psize, psize)),
        ],
        axis=2,
    )
    mn = np.stack(
        [
            np.broadcast_to(normals[:, 0:1], (psize, psize)),
            np.broadcast_to(normals[:, 1:2], (psize, psize)),
            np.broadcast_to(normals[:, 2:3], (psize, psize)),
        ],
        axis=2,
    )

    for j in range(1, vsize):
        seg = j - 1
        lr1 = np.stack(
            [
                np.tile(vortex[:, j - 1, 0], (psize, 1)),
                np.tile(vortex[:, j - 1, 1], (psize, 1)),
                np.tile(vortex[:, j - 1, 2], (psize, 1)),
            ],
            axis=2,
        )
        lr2 = np.stack(
            [
                np.tile(vortex[:, j, 0], (psize, 1)),
                np.tile(vortex[:, j, 1], (psize, 1)),
                np.tile(vortex[:, j, 2], (psize, 1)),
            ],
            axis=2,
        )
        r1 = lr1 - mcolloc
        r2 = lr2 - mcolloc
        ldw[:, :, seg, :] = _mega(r1, r2)

    ldw[np.isnan(ldw)] = 0.0
    dw = -np.sum(ldw, axis=2) * _ONE_BY_FOUR_PI
    dw_influence = np.sum(dw * mn, axis=2)

    if n == 1:
        return dw_influence, dw
    return dw_influence, dw


def solve(state: dict, geo: dict, lattice: dict) -> dict:
    """Solve VLM system; return gamma, panel forces, and moments."""
    lattice = copy.copy(lattice)
    state = copy.copy(state)
    geo = copy.copy(geo)

    vortex = np.asarray(lattice["VORTEX"], dtype=float)
    npan, vor_length, _ = vortex.shape
    b1 = vor_length // 2  # MATLAB 1-based index vor_length/2 → 0-based b1-1, b1

    w2, _ = _fastdw(lattice, 1)

    if "RHS" not in lattice:
        lattice = set_boundary(lattice, geo, state)

    rhs = np.asarray(lattice["RHS"], dtype=float)
    gamma = np.linalg.solve(w2, rhs.T)

    if int(state.get("pgcorr", 0)) == 1:
        atm = isa_atmosphere(state["ALT"])
        m = float(state["AS"]) / atm["a"]
        corr = 1.0 / np.sqrt(1.0 - m**2)
        gamma = gamma * corr

    p1 = vortex[:, b1 - 1, :]
    p2 = vortex[:, b1, :]
    lattice["COLLOC"] = (p1 + p2) / 2.0

    ref_point = np.asarray(geo["ref_point"], dtype=float)
    c3 = lattice["COLLOC"] - ref_point.reshape(1, 3)

    _w3, dw = _fastdw(lattice, 2)
    dwx = dw[:, :, 0]
    dwy = dw[:, :, 1]
    dwz = dw[:, :, 2]

    le = p2 - p1
    lle = np.sqrt(np.sum(le**2, axis=1))
    lehat = le / lle[:, np.newaxis]

    nofderiv = gamma.shape[1]
    alpha = state["alpha"]
    betha = state["betha"]
    wind1 = float(state["AS"]) * np.array(
        [
            np.cos(alpha) * np.cos(betha),
            -np.cos(alpha) * np.sin(betha),
            np.sin(alpha),
        ],
        dtype=float,
    )

    cg = np.asarray(geo["CG"] if "CG" in geo else geo["ref_point"], dtype=float)
    rot_rates = np.array([state["P"], state["Q"], state["R"]], dtype=float)
    rho = float(state["rho"])

    f = np.empty((npan, nofderiv, 3), dtype=float)
    for j in range(nofderiv):
        iw = np.column_stack(
            [
                dwx @ gamma[:, j],
                dwy @ gamma[:, j],
                dwz @ gamma[:, j],
            ]
        )
        g = gamma[:, j][:, np.newaxis] * lehat
        wind = wind1 - iw
        rot = np.cross(lattice["COLLOC"] - cg.reshape(1, 3), rot_rates)
        wind = wind + rot
        fprim = rho * np.cross(wind, g)
        f[:, j, :] = fprim * lle[:, np.newaxis]

    c3_full = np.broadcast_to(c3[:, np.newaxis, :], (npan, nofderiv, 3)).copy()
    m = np.cross(c3_full, f, axis=2)

    return {
        "gamma": gamma,
        "F": f,
        "FORCE": np.sum(f, axis=0),
        "M": m,
        "MOMENTS": np.sum(m, axis=0),
        "dwcond": float(np.linalg.cond(w2)),
    }
