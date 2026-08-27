"""Port of Tornado setboundary5.m (function boundary)."""

from __future__ import annotations

import copy

import numpy as np

from aid.tornado.lattice import _config, flap_indices, lattice_setup

__all__ = ["set_boundary"]


def _wind_vector(state: dict, v: float) -> np.ndarray:
    alpha = state["alpha"]
    betha = state["betha"]
    return v * np.array(
        [
            np.cos(alpha) * np.cos(betha),
            -np.cos(alpha) * np.sin(betha),
            np.sin(alpha),
        ],
        dtype=float,
    )


def _bc_column(lattice: dict, geo: dict, state: dict, v: float, npan: int) -> np.ndarray:
    cg = geo["CG"] if "CG" in geo else np.asarray(geo["ref_point"], dtype=float)
    wind = _wind_vector(state, v)
    wind_tiled = np.broadcast_to(wind, (npan, 3))
    colloc = np.asarray(lattice["COLLOC"], dtype=float)
    rot_rates = np.array([state["P"], state["Q"], state["R"]], dtype=float)
    rot = np.cross(colloc - cg.reshape(1, 3), rot_rates)
    veloc = wind_tiled + rot
    n_arr = np.asarray(lattice["N"], dtype=float)
    return np.sum(n_arr * veloc, axis=1)


def set_boundary(lattice: dict, geo: dict, state: dict) -> dict:
    """Assemble VLM boundary-condition RHS columns (MATLAB setboundary5 / boundary)."""
    lattice = copy.copy(lattice)
    state = copy.copy(state)

    npan = int(lattice["COLLOC"].shape[0])
    v = float(state["AS"])
    delta = _config("delta")

    if "CG" not in geo:
        geo = {**geo, "CG": np.asarray(geo["ref_point"], dtype=float)}

    n_flaps = int(np.sum(np.asarray(geo["flapped"], dtype=float)))
    n_cols = 6 + n_flaps
    bc = np.empty((npan, n_cols), dtype=float)

    bc[:, 0] = _bc_column(lattice, geo, state, v, npan)

    state["alpha"] = state["alpha"] + delta
    bc[:, 1] = _bc_column(lattice, geo, state, v, npan)
    state["alpha"] = state["alpha"] - delta

    state["betha"] = state["betha"] + delta
    bc[:, 2] = _bc_column(lattice, geo, state, v, npan)
    state["betha"] = state["betha"] - delta

    state["P"] = state["P"] + delta
    bc[:, 3] = _bc_column(lattice, geo, state, v, npan)
    state["P"] = state["P"] - delta

    state["Q"] = state["Q"] + delta
    bc[:, 4] = _bc_column(lattice, geo, state, v, npan)
    state["Q"] = state["Q"] - delta

    state["R"] = state["R"] + delta
    bc[:, 5] = _bc_column(lattice, geo, state, v, npan)
    state["R"] = state["R"] - delta

    i_idx, k_idx = flap_indices(geo)

    for rudder in range(len(i_idx)):
        k, i = int(k_idx[rudder]), int(i_idx[rudder])
        geo_work = copy.deepcopy(geo)
        geo_work["flap_vector"][k, i] = geo_work["flap_vector"][k, i] + delta
        flap_lattice, _ref = lattice_setup(geo_work, state, 0)
        bc[:, 6 + rudder] = _bc_column(flap_lattice, geo, state, v, npan)

    # MATLAB solver.m: rhs = (setboundary5(...))'  →  (n_cols, npan)
    lattice["RHS"] = bc.T
    return lattice
