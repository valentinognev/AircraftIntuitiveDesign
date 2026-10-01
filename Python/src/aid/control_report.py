"""Dispatch one control-derivative solver by name."""

from __future__ import annotations

from aid.avl_controls import avl_controls
from aid.control_deriv import DEFAULT_DELTAS_DEG
from aid.datcom_controls import datcom_controls
from aid.flow5_controls import flow5_controls
from aid.handbook_controls import handbook_controls
from aid.tornado.control_deriv import tornado_controls

_SOLVERS = ("handbook", "datcom", "tornado", "avl", "flow5")


def control_report(ac, solver: str, deltas_deg=None, mesh=None) -> dict:
    if solver not in _SOLVERS:
        raise ValueError(f"unknown solver: {solver}")
    reported = [float(d) for d in (DEFAULT_DELTAS_DEG if deltas_deg is None else deltas_deg)]
    if solver == "handbook":
        rows = handbook_controls(ac, deltas_deg)
    elif solver == "datcom":
        rows = datcom_controls(ac, deltas_deg)
    elif solver == "tornado":
        rows = tornado_controls(ac, deltas_deg) if mesh is None else tornado_controls(ac, deltas_deg, mesh)
    elif solver == "avl":
        rows = avl_controls(ac, deltas_deg) if mesh is None else avl_controls(ac, deltas_deg, mesh)
    else:
        rows = flow5_controls(ac, deltas_deg) if mesh is None else flow5_controls(ac, deltas_deg, mesh)
    return {"solver": solver, "deltas_deg": reported, "rows": rows}
