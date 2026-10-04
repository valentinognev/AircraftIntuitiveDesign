"""Central-difference DATCOM control derivatives at a stored probe angle."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from aid.aircraft import Aircraft
from aid.control_deriv import H_DEG, blank_row, central_difference, iter_rows, with_probe
from aid.datcom_run import run_datcom

_RUDDER_REASON = "datcom has no rudder namelist"
_SURFACE_ATTR = {"flap": "F", "aileron": "A", "elevator": "E"}


def datcom_controls(ac, deltas_deg=None, *, run=None) -> list[dict]:
    """One paired run per flap, aileron, and elevator probe.

    ``run(ac) -> dict`` replaces ``run_datcom`` when tests pass a fake.
    Rudder rows stay unavailable: DATCOM has no rudder namelist.
    ``SPANFO <= SPANFI`` or a missing chord skips ``run`` for that surface
    and still returns the other rows.
    """
    runner = _run_datcom if run is None else run
    rows: list[dict] = []
    for surface, delta in iter_rows(deltas_deg):
        if surface == "rudder":
            rows.append(blank_row(surface, delta, available=False, reason=_RUDDER_REASON))
            continue
        blocked = _blocked_reason(getattr(ac, _SURFACE_ATTR[surface]))
        if blocked is not None:
            rows.append(blank_row(surface, delta, available=False, reason=blocked))
            continue
        plus = _totals(runner(with_probe(ac, surface, delta + H_DEG)))
        minus = _totals(runner(with_probe(ac, surface, delta - H_DEG)))
        row = blank_row(surface, delta, available=True)
        row.update(central_difference(plus, minus, H_DEG))
        rows.append(row)
    return rows


def _blocked_reason(pt: dict) -> str | None:
    """None when the surface can be written. Checked before ``run``."""
    if pt.get("CHRDFI") is None or pt.get("CHRDFO") is None:
        return "missing chord"
    try:
        spanfo = float(pt["SPANFO"])
        spanfi = float(pt["SPANFI"])
    except (KeyError, TypeError, ValueError):
        return None
    if spanfo <= spanfi:
        return "SPANFO<=SPANFI"
    return None


def _run_datcom(ac: Aircraft) -> dict:
    with TemporaryDirectory(prefix="datcom-ctrl-") as tmp:
        return run_datcom(ac, Path(tmp))


def _index0(raw) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)) or hasattr(raw, "shape"):
        if len(raw) == 0:
            return None
        raw = raw[0]
    if raw is None:
        return None
    return float(raw)


def _pick(parsed: dict, *keys: str):
    for key in keys:
        if key in parsed:
            return key, _index0(parsed[key])
    return None, None


def _totals(parsed: dict) -> dict:
    """Alpha row 0.

    Longitudinal totals are ``CL``/``CD``/``Cm``, else the parser keys
    ``cl``/``cd``/``cm``. Lateral ``Cl``/``Cn``/``CY`` use lowercase
    ``cl``/``cn``/``cy`` when that key was not already the longitudinal
    total. Parser ``cn`` (normal force) fills yawing-moment ``Cn`` only
    when ``cy`` is also present. A missing lateral key stays ``None``.
    """
    cl_key, cl = _pick(parsed, "CL", "cl")
    cd_key, cd = _pick(parsed, "CD", "cd")
    cm_key, cm = _pick(parsed, "Cm", "cm")
    used = {cl_key, cd_key, cm_key}

    def lateral(key: str) -> float | None:
        if key not in parsed or key in used:
            return None
        # Parser ``cn`` is normal force. Treat it as yawing moment only
        # alongside a side-force key, which the static alpha table does not emit.
        if key == "cn" and "cy" not in parsed:
            return None
        return _index0(parsed[key])

    # ``parsed`` arrives already normalized: ``_run_datcom`` goes through
    # ``run_datcom``, whose ``to_frd("datcom", ...)`` flips the two lowercase force
    # keys ``ca`` and ``cn`` (aid/axes.py). There is no uppercase pair in play --
    # ``parse_for006`` emits only the lowercase names in ``_COEF_NAMES`` -- so no
    # second conversion belongs here, and the ``cl``/``cm``/``cd`` this reads are
    # already F-R-D moments and totals.
    #
    # What actually protects ``lateral("cn")`` is the ``"cy" not in parsed`` guard
    # above, and nothing else. ``parsed["cn"]`` is the *normal force*, already
    # sign-flipped by ``to_frd`` and still not a yawing moment, so that guard is the
    # only thing standing between this function and reporting the normal force as
    # ``Cn`` on the Controls tab. It holds solely because the static alpha table
    # emits no side-force key: ``_COEF_NAMES`` has ``cyb`` but no ``cy``. If DATCOM
    # ever gains a side-force channel, revisit that guard first -- flipping the sign
    # would not be the fix.
    #
    # Likewise the uppercase arms of the three ``_pick`` probes above are dead:
    # ``parse_for006`` never produces ``CL``, ``CD`` or ``Cm``, so only the
    # lowercase branch is live. They are harmless, but do not read them as evidence
    # that a differently-cased payload is supported.
    return {
        "CL": cl,
        "CD": cd,
        "Cm": cm,
        "CY": lateral("cy"),
        "Cl": lateral("cl"),
        "Cn": lateral("cn"),
    }
