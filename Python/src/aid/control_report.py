"""Dispatch one control-derivative solver by name."""

from __future__ import annotations

from aid.avl_controls import avl_controls
from aid.control_deriv import DEFAULT_DELTAS_DEG
from aid.datcom_controls import datcom_controls
from aid.flow5_controls import flow5_controls
from aid.handbook_controls import handbook_controls
from aid.tornado.control_deriv import tornado_controls

_SOLVERS = ("handbook", "datcom", "tornado", "avl", "flow5")
# Same tuples as aid_web.analyze.DEFAULT_MESH. Applied only when the caller
# omits mesh, so tornado_controls and flow5_controls keep ("4", "2") for tests.
# This module must not import the web API.
_DEFAULT_MESH = {
    "tornado": ("10", "5"),
    "avl": ("10", "10"),
    "flow5": ("10", "10"),
}


def _panel_mesh(solver: str, mesh):
    if mesh is None:
        return _DEFAULT_MESH[solver]
    return mesh


def control_report(ac, solver: str, deltas_deg=None, mesh=None) -> dict:
    if solver not in _SOLVERS:
        raise ValueError(f"unknown solver: {solver}")
    reported = [float(d) for d in (DEFAULT_DELTAS_DEG if deltas_deg is None else deltas_deg)]
    if solver == "handbook":
        rows = handbook_controls(ac, deltas_deg)
    elif solver == "datcom":
        rows = datcom_controls(ac, deltas_deg)
    elif solver == "tornado":
        rows = tornado_controls(ac, deltas_deg, _panel_mesh(solver, mesh))
    elif solver == "avl":
        rows = avl_controls(ac, deltas_deg, _panel_mesh(solver, mesh))
    else:
        rows = flow5_controls(ac, deltas_deg, _panel_mesh(solver, mesh))
    return {"solver": solver, "deltas_deg": reported, "rows": rows}
