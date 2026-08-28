"""Run Python lattice/solver on MATLAB-exported geo to isolate parity bugs."""

from __future__ import annotations

import sys

import numpy as np
from scipy.io import loadmat
from scipy.io.matlab import mat_struct

from aid.tornado.boundary import set_boundary
from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.solver import solve
from aid.paths import repo_root
from aid.tornado_io import _finalize_geo


def _mat_scalar(obj):
    arr = np.asarray(obj)
    if arr.size == 1:
        return arr.item()
    return arr


def _mat_row_list(arr: np.ndarray) -> list[np.ndarray]:
    arr = np.asarray(arr, dtype=float)
    return [arr[i].copy() for i in range(arr.shape[0])]


def mat_geo_to_py(mgeo) -> dict:
    g = {}
    g["nwing"] = int(_mat_scalar(mgeo.nwing))
    g["nelem"] = np.asarray(mgeo.nelem, dtype=int)
    g["symetric"] = np.asarray(mgeo.symetric, dtype=float)
    g["c"] = _mat_row_list(mgeo.c)
    g["T"] = _mat_row_list(mgeo.T)
    g["SW"] = _mat_row_list(mgeo.SW)
    g["dihed"] = _mat_row_list(mgeo.dihed)
    g["b"] = _mat_row_list(mgeo.b)
    g["startx"] = _mat_row_list(mgeo.startx)
    g["starty"] = _mat_row_list(mgeo.starty)
    g["startz"] = _mat_row_list(mgeo.startz)
    g["fnx"] = _mat_row_list(mgeo.fnx)
    g["fsym"] = _mat_row_list(mgeo.fsym)
    g["fc"] = _mat_row_list(mgeo.fc)
    g["flapped"] = _mat_row_list(mgeo.flapped)
    g["flap_vector"] = _mat_row_list(mgeo.flap_vector)
    g["meshtype"] = _mat_row_list(mgeo.meshtype)
    g["nx"] = _mat_row_list(mgeo.nx)
    g["ny"] = _mat_row_list(mgeo.ny)
    tw = np.asarray(mgeo.TW, dtype=float)
    g["TW"] = [tw[i : i + 1].copy() for i in range(tw.shape[0])]
    fi = np.asarray(mgeo.flap_id, dtype=float)
    g["flap_id"] = [fi[i].copy() for i in range(fi.shape[0])]
    g["foil"] = [[None]] * g["nwing"]
    return _finalize_geo(g)


def mat_state_to_py(mstate) -> dict:
    return {
        "AS": float(mstate.AS),
        "alpha": float(mstate.alpha),
        "betha": float(mstate.betha),
        "P": float(mstate.P),
        "Q": float(mstate.Q),
        "R": float(mstate.R),
        "alphadot": float(mstate.alphadot),
        "bethadot": float(mstate.bethadot),
        "ALT": float(mstate.ALT),
        "rho": float(mstate.rho),
        "pgcorr": float(mstate.pgcorr),
    }


def main(name: str) -> None:
    path = repo_root() / "Results" / "debug" / f"matlab_{name.lower().replace('-', '_')}_tornado.mat"
    if name == "DA20-C1":
        path = repo_root() / "Results" / "debug" / "matlab_da20_tornado.mat"
    elif name == "Navion":
        path = repo_root() / "Results" / "debug" / "matlab_navion_tornado.mat"

    m = loadmat(path, squeeze_me=True, struct_as_record=False)
    geo = mat_geo_to_py(m["geo"])
    state = mat_state_to_py(m["state"])
    mlatt = m["lattice"]
    mtres = m["tres"]

    lattice, ref = lattice_setup(geo, state, 0)
    xyz_diff = np.max(np.abs(lattice["XYZ"] - mlatt.XYZ))
    print(f"{name}: lattice XYZ diff on MATLAB geo = {xyz_diff:.6g}")

    lattice = set_boundary(lattice, geo, state)
    raw = solve(state, geo, lattice)
    tres = coeff_create(raw, lattice, state, ref, geo)
    print(f"{name}: CL py={tres['CL']:.6g} mat={float(mtres.CL):.6g}")


if __name__ == "__main__":
    for arg in sys.argv[1:] or ["Navion", "DA20-C1"]:
        main(arg)
