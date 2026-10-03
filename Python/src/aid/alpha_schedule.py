"""Angle-of-attack schedule expansion for ``AERO.ALSCHD``."""

from __future__ import annotations

import math

ALPHA_POINTS = 15
# Only steps DATCOM's ``%.1f`` $FLTCON cards carry exactly: a grid finer than
# 0.1 is written as a different set of alphas than the one differenced here,
# and ``cla``/``cma`` are finite differences along the *written* grid.
_STEP_LADDER = (0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0)
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


def _as_written(value: float) -> float:
    """*value* snapped to the double DATCOM's ``%.1f`` will carry, when it carries it."""
    written = float(f"{value:.1f}")
    return written if abs(written - value) <= _EPS else value


def _datcom_faithful(sched: list[float]) -> bool:
    """Whether the ``%.1f`` $FLTCON cards would carry *sched* unaltered."""
    return all(float(f"{a:.1f}") == a for a in sched)


def alpha_schedule(ac, target: int = ALPHA_POINTS) -> list[float]:
    """``AERO.ALSCHD`` as a list of angles of attack, expanded to about ``target`` points.

    Sparse schedules are refilled on the ladder step whose point count lands
    nearest ``target``, ties taking the finer step, and the endpoints are kept.
    A schedule that survives ``%.1f`` comes back as plain floats; one stored
    with more points than ``target``, as a scalar, or with no finite value at
    all, comes back normalised by ``_finite_values`` and no longer than stored.

    A generated schedule that DATCOM's cards could not carry unaltered -- the
    endpoints do not reach 0.1, so the deck would difference over a grid it
    never received -- is abandoned and the stored schedule returned unchanged:
    fail safe, never emit a deck that misreports its own sweep.
    """
    values = _finite_values(ac.AERO.get("ALSCHD"))
    if not values or len(values) >= target:
        return values
    lo, hi = min(values), max(values)
    span = hi - lo
    if span == 0.0:
        return [lo]
    step = _step_for(span, target)
    sched = [_as_written(lo + i * step) for i in range(_point_count(span, step))]
    if hi - sched[-1] > _EPS:
        sched.append(_as_written(hi))
    if not _datcom_faithful(sched):
        return values
    return sched


def apply_alpha_default(ac, target: int = ALPHA_POINTS):
    """Store the expanded schedule in ``AERO.ALSCHD`` and return the aircraft.

    An absent ``ALSCHD`` key stays absent, and a stored value with no finite
    number in it is left exactly as it is: ``[]`` in its place would erase the
    user's input and hand every solver an empty sweep.
    """
    if "ALSCHD" not in ac.AERO:
        return ac
    if not _finite_values(ac.AERO["ALSCHD"]):
        return ac
    ac.AERO["ALSCHD"] = alpha_schedule(ac, target)
    return ac