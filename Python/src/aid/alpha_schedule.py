"""Angle-of-attack schedule expansion for ``AERO.ALSCHD``."""

from __future__ import annotations

import math

ALPHA_POINTS = 15
_STEP_LADDER = (0.05, 0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
_EPS = 1e-9


def _finite_values(raw) -> list[float]:
    """Flat list of the finite floats in a scalar, sequence or array."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        items = list(raw)
    else:
        tolist = getattr(raw, "tolist", None)
        items = tolist() if callable(tolist) else raw
    if not isinstance(items, (list, tuple)):
        items = [items]
    if items and isinstance(items[0], (list, tuple)):
        items = [x for row in items for x in row]
    values = []
    for item in items:
        try:
            value = float(item)
        except (TypeError, ValueError):
            continue
        if math.isfinite(value):
            values.append(value)
    return values


def _point_count(span: float, step: float) -> int:
    return math.floor(span / step + _EPS) + 1


def _step_for(span: float, target: int) -> float:
    """Ladder step whose point count is closest to ``target``; ties take the finer step."""
    return min(_STEP_LADDER, key=lambda s: (abs(_point_count(span, s) - target), s))


def alpha_schedule(ac, target: int = ALPHA_POINTS) -> list[float]:
    """``AERO.ALSCHD`` as a list of angles of attack, expanded to about ``target`` points.

    Sparse schedules are refilled on the finest ladder step that lands nearest
    ``target``; schedules already at or above it are returned as stored.
    """
    values = _finite_values(ac.AERO.get("ALSCHD"))
    if not values or len(values) >= target:
        return values
    lo, hi = min(values), max(values)
    span = hi - lo
    if span == 0.0:
        return [lo]
    step = _step_for(span, target)
    sched = [lo + i * step for i in range(_point_count(span, step))]
    if hi - sched[-1] > _EPS:
        sched.append(hi)
    return sched


def apply_alpha_default(ac, target: int = ALPHA_POINTS):
    """Store the expanded schedule in ``AERO.ALSCHD`` and return the aircraft."""
    ac.AERO["ALSCHD"] = alpha_schedule(ac, target)
    return ac