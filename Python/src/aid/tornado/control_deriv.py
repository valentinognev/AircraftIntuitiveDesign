"""Tornado control-surface derivatives at a probe deflection."""

from __future__ import annotations

from copy import deepcopy

import numpy as np

from aid.aircraft import Aircraft
from aid.control_deriv import (
    H_DEG,
    blank_row,
    central_difference,
    iter_rows,
    with_probe,
)
from aid.tornado.boundary import set_boundary
from aid.tornado.coeff import coeff_create
from aid.tornado.lattice import lattice_setup
from aid.tornado.solver import solve
from aid.tornado_io import _span_legal, tornado_io

_WING_NAME = {
    "flap": "Wing",
    "aileron": "Wing",
    "elevator": "HT",
    "rudder": "VT",
}
_PARENT = {
    "flap": "WG",
    "aileron": "WG",
    "elevator": "HT",
    "rudder": "VT",
}


def tornado_controls(
    ac: Aircraft,
    deltas_deg=None,
    mesh: tuple[str, str] = ("4", "2"),
) -> list[dict]:
    rows = []
    for surface, delta in iter_rows(deltas_deg):
        rows.append(_row_at_probe(ac, surface, delta, mesh))
    return rows


def _row_at_probe(ac: Aircraft, surface: str, delta: float, mesh: tuple[str, ...]) -> dict:
    reason = _unavailable_reason(ac, surface)
    if reason:
        return blank_row(surface, delta, available=False, reason=reason)

    probed = with_probe(ac, surface, delta)
    geo, state = tornado_io(probed, mesh, force_controls=True)
    state["alpha"] = _first_alpha(ac)
    _keep_fixed_chordwise_panel(geo)
    strips = _surface_strips(geo, ac, surface)
    if not strips:
        return blank_row(surface, delta, available=False, reason="surface not on lattice")
    if surface == "aileron":
        for wing, part in strips:
            geo["fsym"][wing, part] = 0.0

    plus = _coefficients(geo, state, strips, H_DEG)
    minus = _coefficients(geo, state, strips, -H_DEG)
    row = blank_row(surface, delta, available=True)
    row.update(central_difference(plus, minus, H_DEG))
    return row


def _unavailable_reason(ac: Aircraft, surface: str) -> str:
    block = {"flap": ac.F, "aileron": ac.A, "elevator": ac.E, "rudder": ac.R}[surface]
    if not _span_legal(block):
        return "illegal span"
    parent = getattr(ac, _PARENT[surface])
    if not isinstance(parent, dict) or not parent:
        return "missing parent planform"
    try:
        sspn = float(np.asarray(parent.get("SSPN", 0), dtype=float).reshape(-1)[0])
    except (TypeError, ValueError, IndexError):
        return "missing parent planform"
    if not np.isfinite(sspn) or sspn <= 0:
        return "missing parent planform"
    return ""


def _keep_fixed_chordwise_panel(geo: dict) -> None:
    """Meshed strips need nx >= 1.

    Tail chordwise count at mesh ("4", "2") is 1. A legal control then takes
    that panel (fnx = 1, nx = 0). The lattice meshes the fixed part with
    ``arange(nx + 1) / nx`` and warns. Leave fnx alone so the flap remains.
    """
    nx = np.asarray(geo["nx"], dtype=float)
    nelem = np.asarray(geo["nelem"], dtype=int)
    for wing, n_part in enumerate(nelem):
        for part in range(int(n_part)):
            if int(nx[wing, part]) <= 0:
                nx[wing, part] = 1.0


def _first_alpha(ac: Aircraft) -> float:
    alschd = np.asarray(ac.AERO["ALSCHD"], dtype=float).reshape(-1)
    return float(np.deg2rad(alschd[0]))


def _control_column(ac: Aircraft, surface: str) -> int | None:
    if surface in ("flap", "aileron"):
        order = [name for name, block in (("flap", ac.F), ("aileron", ac.A)) if _span_legal(block)]
    elif surface == "elevator":
        order = ["elevator"] if _span_legal(ac.E) else []
    else:
        order = ["rudder"] if _span_legal(ac.R) else []
    if surface not in order:
        return None
    return order.index(surface)


def _surface_strips(geo: dict, ac: Aircraft, surface: str) -> list[tuple[int, int]]:
    column = _control_column(ac, surface)
    names = list(geo.get("name") or [])
    wing_name = _WING_NAME[surface]
    if column is None or wing_name not in names:
        return []
    wing = names.index(wing_name)
    flap_id = np.asarray(geo["flap_id"])
    if flap_id.ndim != 3 or column >= flap_id.shape[2] or wing >= flap_id.shape[0]:
        return []
    parts = np.flatnonzero(flap_id[wing, :, column] == column + 1)
    return [(wing, int(part)) for part in parts]


def _coefficients(geo: dict, state: dict, strips: list[tuple[int, int]], step_deg: float) -> dict:
    stepped = deepcopy(geo)
    step_rad = float(np.deg2rad(step_deg))
    for wing, part in strips:
        stepped["flap_vector"][wing, part] = stepped["flap_vector"][wing, part] + step_rad
    lattice, ref = lattice_setup(stepped, state, 0)
    lattice = set_boundary(lattice, stepped, state)
    raw = solve(state, stepped, lattice)
    coeffs = coeff_create(raw, lattice, state, ref, stepped)
    # No to_frd("tornado", ...) here on purpose. These Cl/Cn are read straight out
    # of coeff_create, which already returns Forward-Right-Down, so wrapping this
    # dict would flip them twice and re-mirror the very quantity the F-R-D work
    # exists to fix. CL/CD/Cm are wind-axis and CY is the CC side force; none of
    # the four is in the map in any case.
    return {
        "CL": float(coeffs["CL"]),
        "CD": float(coeffs["CD"]),
        "Cm": float(coeffs["Cm"]),
        "CY": float(coeffs["CC"]),
        "Cl": float(coeffs["Cl"]),
        "Cn": float(coeffs["Cn"]),
    }
