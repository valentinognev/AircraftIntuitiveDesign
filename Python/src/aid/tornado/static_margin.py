"""Port of Tornado fFindstaticmargin.m (neutral-point Newton iteration)."""

from __future__ import annotations

import numpy as np

from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.solver import solve

__all__ = ["StaticMarginError", "find_static_margin"]


class StaticMarginError(RuntimeError):
    pass


def _default_run(geo: dict, state: dict, c_mac_box: dict) -> dict:
    """lattice_setup(..., mode=1) → solve → coeff_create. Viscous correction off."""
    lattice, ref = lattice_setup(geo, state, 1)
    results = solve(state, geo, lattice)
    results = coeff_create(results, lattice, state, ref, geo)
    c_mac_box["value"] = ref["C_mac"]
    return results


def _c_mac(results: dict, c_mac_box: dict) -> float:
    if "C_mac" in results:
        return float(results["C_mac"])
    return float(c_mac_box["value"])


def find_static_margin(
    geo: dict,
    state: dict,
    *,
    max_iter: int = 10,
    tol: float = 1e-5,
    run=None,
) -> dict:
    """Port fFindstaticmargin.m.

    Mutates geo['ref_point'][0] during the iteration and leaves it at the
    converged aerodynamic center. run(geo, state) -> results with CL_a and Cm_a.
    Default run builds a lattice (solvertype/mode 1), solves, and calls coeff_create.
    Returns {'ac': ndarray (3,), 'h': ndarray (3,)} with
    h = (ac - CG) / C_mac from the last lattice ref (or results['C_mac']).
    Raises StaticMarginError after max_iter without abs(Cm_a/CL_a) < tol.

    The baseline ratio is CL_a/Cm_a; later iterations use Cm_a/CL_a, matching
    fFindstaticmargin.m lines 19 and 35.
    """
    c_mac_box: dict = {"value": None}
    if run is None:
        def run(g, s, _box=c_mac_box):
            return _default_run(g, s, _box)

    results = run(geo, state)
    # MATLAB line 19: baseline uses the reciprocal of the later residual.
    var0 = float(results["CL_a"]) / float(results["Cm_a"])
    step = 0.5
    i = 0
    while True:
        i += 1
        with np.errstate(invalid="ignore", over="ignore"):
            geo["ref_point"][0] = geo["ref_point"][0] + step
        results = run(geo, state)
        var1 = float(results["Cm_a"]) / float(results["CL_a"])
        with np.errstate(divide="ignore", invalid="ignore"):
            dvar_dstep = np.divide(var1 - var0, step)
            step = float(np.divide(-var1, dvar_dstep))
        if abs(var1) < tol:
            ac = np.asarray(geo["ref_point"], dtype=float).copy()
            cg = np.asarray(geo["CG"], dtype=float)
            h = (ac - cg) / _c_mac(results, c_mac_box)
            return {"ac": ac, "h": np.asarray(h, dtype=float)}
        if i == max_iter:
            raise StaticMarginError("Max iterations in fFindstaticmargin")
        var0 = var1
