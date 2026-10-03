"""flow5 control derivatives at a probe, from deck trailing-edge flaps."""

from __future__ import annotations

from aid.aircraft import Aircraft
from aid.axes import to_frd
from aid.control_deriv import (
    COEFFS,
    H_DEG,
    blank_row,
    central_difference,
    iter_rows,
    with_probe,
)
from aid.flow5_io import run_flow5_native, write_flow5_deck
from aid.flow5_units import ft_to_m

_BLOCK = {"flap": "F", "aileron": "A", "elevator": "E", "rudder": "R"}
_WING = {"flap": "Wing", "aileron": "Wing", "elevator": "HT", "rudder": "VT"}
_KEEP = {
    "flap": ("CL", "CD", "Cm"),
    "elevator": ("CL", "CD", "Cm"),
    "aileron": ("Cl", "Cn"),
    "rudder": ("CY", "Cl", "Cn"),
}
_STATION_FT = 1e-4


def flow5_controls(ac, deltas_deg=None, mesh=("4", "2"), *, run=None) -> list[dict]:
    """Central-difference the first alpha sample of decks at δ±h.

    ``run(deck) -> dict`` replaces ``run_flow5_native`` when tests pass a fake.
    Coefficients the deck run does not return stay ``None``.
    """
    runner = run_flow5_native if run is None else run
    return [_row(ac, surface, delta, mesh, runner) for surface, delta in iter_rows(deltas_deg)]


def _row(ac: Aircraft, surface: str, delta: float, mesh, runner) -> dict:
    block = getattr(ac, _BLOCK[surface])
    reason = _unavailable(block)
    if reason:
        return blank_row(surface, delta, available=False, reason=reason)
    if not _wing_present(ac, mesh, surface):
        return blank_row(surface, delta, available=False, reason="parent surface missing")

    plus = _sample(runner(_deck_at(ac, mesh, surface, delta + H_DEG, block)))
    minus = _sample(runner(_deck_at(ac, mesh, surface, delta - H_DEG, block)))
    slope = central_difference(plus, minus, H_DEG)
    row = blank_row(surface, delta, available=True)
    for name in _KEEP[surface]:
        row[name] = slope[name]
    # The probe runs go through run_flow5_native, so these rows are still in
    # flow5's own frame: Cl and Cn are the mirrored channels. Normalize here,
    # once, rather than in every plot that reads control rows -- a central
    # difference of two negated samples is the negation of the difference, so
    # wrapping the slope is equivalent to wrapping each sample.
    return to_frd("flow5", row)


def _unavailable(block) -> str:
    if not isinstance(block, dict):
        return "missing chords"
    spanfi = _num(block, "SPANFI")
    spanfo = _num(block, "SPANFO")
    chrdfi = _num(block, "CHRDFI")
    chrdfo = _num(block, "CHRDFO")
    if None in (spanfi, spanfo, chrdfi, chrdfo):
        return "missing chords"
    if spanfo <= spanfi:
        return "illegal span"
    return ""


def _num(block: dict, key: str) -> float | None:
    if key not in block or block[key] is None:
        return None
    raw = block[key]
    if isinstance(raw, (list, tuple)):
        if not raw:
            return None
        raw = raw[0]
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def _wing_present(ac: Aircraft, mesh, surface: str) -> bool:
    deck = write_flow5_deck(ac, mesh)
    return any(wing.get("name") == _WING[surface] for wing in deck["wings"])


def _deck_at(ac: Aircraft, mesh, surface: str, delta_deg: float, block: dict) -> dict:
    probed = with_probe(ac, surface, delta_deg)
    angle = _starboard_deg(probed, surface)
    deck = write_flow5_deck(ac, mesh)
    wing = next(item for item in deck["wings"] if item.get("name") == _WING[surface])
    _stamp(wing["sections"], block, angle, antisym=(surface == "aileron"))
    return deck


def _starboard_deg(probed: Aircraft, surface: str) -> float:
    if surface == "aileron":
        return float(probed.A["DELTAR"])
    return float(getattr(probed, _BLOCK[surface])["DELTA"])


def _stamp(sections: list[dict], block: dict, angle_deg: float, *, antisym: bool) -> None:
    spanfi = _num(block, "SPANFI")
    spanfo = _num(block, "SPANFO")
    chrdfi = _num(block, "CHRDFI")
    _insert_station(sections, spanfi)
    _insert_station(sections, spanfo)
    for section in sections:
        span = section["y_m"] / ft_to_m(1.0)
        if span < spanfi - _STATION_FT or span > spanfo + _STATION_FT:
            continue
        section["te_flap_x"] = _hinge_x(section["chord_m"], chrdfi)
        section["te_flap_deg"] = angle_deg
        section["te_flap_antisym"] = antisym


def _insert_station(sections: list[dict], span_ft: float) -> None:
    y = ft_to_m(span_ft)
    for section in sections:
        if abs(section["y_m"] / ft_to_m(1.0) - span_ft) <= _STATION_FT:
            return
    inner = None
    outer = None
    for section in sections:
        if section["y_m"] < y and (inner is None or section["y_m"] > inner["y_m"]):
            inner = section
        if section["y_m"] > y and (outer is None or section["y_m"] < outer["y_m"]):
            outer = section
    if inner is None or outer is None or outer["y_m"] == inner["y_m"]:
        return
    t = (y - inner["y_m"]) / (outer["y_m"] - inner["y_m"])
    sections.append(
        {
            "y_m": y,
            "chord_m": _lerp(inner["chord_m"], outer["chord_m"], t),
            "x_offset_m": _lerp(inner["x_offset_m"], outer["x_offset_m"], t),
            "dihedral_deg": _lerp(inner["dihedral_deg"], outer["dihedral_deg"], t),
            "twist_deg": _lerp(inner["twist_deg"], outer["twist_deg"], t),
            "ny": inner.get("ny") or 0,
            "foil": inner["foil"],
        }
    )
    sections.sort(key=lambda section: section["y_m"])


def _lerp(a: float, b: float, t: float) -> float:
    return float(a) + t * (float(b) - float(a))


def _hinge_x(chord_m: float, flap_chord_ft: float) -> float:
    chord_ft = chord_m / ft_to_m(1.0)
    if chord_ft <= 0.0:
        return 0.05
    x = 1.0 - flap_chord_ft / chord_ft
    if x < 0.05:
        return 0.05
    if x > 0.95:
        return 0.95
    return x


def _sample(result: dict) -> dict:
    return {name: _alpha0(result, name) for name in COEFFS}


def _alpha0(result: dict, name: str) -> float | None:
    if name not in result or result[name] is None:
        return None
    raw = result[name]
    if isinstance(raw, (list, tuple)):
        if len(raw) == 0:
            return None
        raw = raw[0]
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None
