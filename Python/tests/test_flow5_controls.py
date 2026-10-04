import pytest

from aid.aircraft import Aircraft, load_jsonc
from aid.axes import to_frd
from aid.control_deriv import H_DEG
from aid.flow5_controls import flow5_controls
from aid.flow5_io import run_flow5_native
from aid.paths import flow5_bin, models_dir

FLOW5_BIN = flow5_bin()

# Raw flow5 slopes with respect to rudder deflection, per deg, in flow5's own
# frame (x aft / y right / z up, Cl and Cn mirrored). Chosen non-zero and of
# mixed sign so that neither a missing wrap nor a doubled one can hide behind a
# -0.0 == 0.0 comparison.
_RAW_RUDDER_SLOPES = {"Cl": 0.02, "Cn": -0.05, "CY": 0.11}


def _vt_deflection(deck: dict) -> float | None:
    """The rudder deflection stamped on the VT wing, or ``None`` if untouched.

    ``write_flow5_deck`` always emits Wing/HT/VT, so keying on the wing *name*
    identifies nothing; the probe is identified by the trailing-edge flap data
    ``_stamp`` put on the fin's sections. This reads the deck, it does not
    rebuild the deflection stepping.
    """
    fin = next(w for w in deck["wings"] if w["name"] == "VT")
    angles = {s["te_flap_deg"] for s in fin["sections"] if "te_flap_deg" in s}
    return angles.pop() if len(angles) == 1 else None


def _rudder_row(rows: list[dict]) -> dict:
    return next(r for r in rows if r["surface"] == "rudder")


def test_flow5_controls_normalizes_the_lateral_rows_it_builds_from_raw_samples():
    """R1: ``flow5_controls`` probes through ``run_flow5_native``, so it must wrap.

    Same shape as ``test_axes_wiring``'s tornado ``control_deriv`` case, and for
    the same reason: ``run_flow5_native`` is raw by contract, so a row built from
    it is raw unless something normalizes it. ``Cl`` and ``Cn`` are the two of
    ``COEFFS`` that the flow5 sign map names, so the wrap must mirror exactly
    them and leave ``CY`` alone -- ``CY`` is the wind-axis side force, which no
    solver ever flips.

    The expectation is recomputed from the *captured* raw values with the same
    central difference, so this is exact equality against the very dicts the
    module read: no solver-vs-solver tolerance and no reimplementation of the
    deflection stepping.

    Uses a stub solver, so it runs even where ``flow5_run`` is not built.
    """
    seen: list[tuple[dict, dict]] = []

    def fake_run(deck):
        deflection = _vt_deflection(deck) or 0.0
        out = {
            "alpha": [0.0],
            "CL": [0.3 + 0.01 * deflection],
            "CD": [0.02],
            "Cm": [-0.1],
            **{key: [slope * deflection] for key, slope in _RAW_RUDDER_SLOPES.items()},
        }
        seen.append((deck, out))
        return out

    rows = flow5_controls(_ac(), [5.0], mesh=("4", "2"), run=fake_run)
    row = _rudder_row(rows)
    rudder_probes = [raw for deck, raw in seen if _vt_deflection(deck) is not None]
    assert len(rudder_probes) == 2, "the rudder must be probed at delta + h and - h"
    plus, minus = rudder_probes  # _row probes delta + h first

    for key, slope in _RAW_RUDDER_SLOPES.items():
        raw = (plus[key][0] - minus[key][0]) / (2.0 * H_DEG)
        assert raw == pytest.approx(slope, rel=1e-9), key
        assert row[key] != 0.0, key
        expected = -raw if key in ("Cl", "Cn") else raw
        assert row[key] == expected, key

    # The precise claim: flow5_controls' Cl/Cn are the ones run_flow5 reports for
    # the same two decks. to_frd is linear, so it commutes with the difference --
    # which is why one wrap of the slope equals a wrap of each sample.
    for key in ("Cl", "Cn"):
        raw = (plus[key][0] - minus[key][0]) / (2.0 * H_DEG)
        normalized = (to_frd("flow5", plus)[key][0] - to_frd("flow5", minus)[key][0]) / (2.0 * H_DEG)
        assert normalized == -raw
        assert row[key] == normalized, key


@pytest.mark.skipif(not FLOW5_BIN.is_file(), reason="flow5 helper not built")
def test_flow5_controls_lateral_slopes_match_the_live_solver():
    """The same invariant on real flow5 output, not a stub's.

    ``Cl``/``Cn`` are read off polar vars 12/13, which are mirrored, so the live
    rudder probe must come back right-wing-down-positive-in-F-R-D: measured raw
    slope ``Cl`` -4.1448e-04 and ``Cn`` +1.8853e-03 at mesh ("4","2"), delta = 5.
    The wrap turns those into +4.1448e-04 and -1.8853e-03.
    """
    probes: list[tuple[dict, dict]] = []

    def spy(deck):
        out = run_flow5_native(deck)
        probes.append((deck, out))
        return out

    rows = flow5_controls(
        load_jsonc(models_dir() / "Cessna 172.jsonc"), [5.0], mesh=("4", "2"), run=spy
    )
    rudder_probes = [raw for deck, raw in probes if _vt_deflection(deck) is not None]
    assert len(rudder_probes) == 2, "the rudder must be probed at delta + h and - h"

    row = _rudder_row(rows)
    assert row["available"] and not row["reason"]
    plus, minus = rudder_probes

    for key in ("Cl", "Cn", "CY"):
        assert row[key] != 0.0, f"{key} must be non-zero for the equalities to bite"
        raw_slope = (plus[key][0] - minus[key][0]) / (2.0 * H_DEG)
        frd_slope = (
            to_frd("flow5", plus)[key][0] - to_frd("flow5", minus)[key][0]
        ) / (2.0 * H_DEG)
        assert frd_slope == (-raw_slope if key in ("Cl", "Cn") else raw_slope)
        assert row[key] == pytest.approx(frd_slope, rel=1e-12, abs=0.0), key

    # Measured pins, so a solver-side change that reversed the rudder's authority
    # would be noticed rather than quietly absorbed by the sign convention.
    assert row["Cl"] == pytest.approx(4.144763306434448e-04, rel=1e-9)
    assert row["Cn"] == pytest.approx(-1.8853295223498004e-03, rel=1e-9)
    assert row["CY"] > 0.0, "a right rudder produces a right side force"


def _ac() -> Aircraft:
    wing = {
        "CHRDR": 2.0, "CHRDTP": 1.0, "SSPN": 5.0, "SSPNOP": 0.0,
        "SAVSI": 0.0, "SAVSO": 0.0, "CHSTAT": 0.25, "DHDADI": 0.0, "DHDADO": 0.0,
        "TWISTA": 0.0, "SSPNE": 5.0, "X": 0.0, "Y": 0.0, "Z": 0.0, "i": 0.0,
        "NACA": ["0012"], "S": [20.0],
    }
    tail = dict(wing)
    tail["SSPN"] = 2.0
    z = {"SPANFI": 0.5, "SPANFO": 2.0, "CHRDFI": 0.4, "CHRDFO": 0.4, "DELTA": 0.0}
    a = {"SPANFI": 3.0, "SPANFO": 4.5, "CHRDFI": 0.3, "CHRDFO": 0.25, "DELTAL": 0.0, "DELTAR": 0.0}
    return Aircraft(
        WG=wing, HT=dict(tail), VT=dict(tail), F=dict(z), A=dict(a), E=dict(z), R=dict(z),
        BD={}, NP=[], NB=[], AERO={"ALSCHD": [0.0], "SREF": 20.0, "CBARR": 1.5, "BLREF": 10.0,
                                    "XCG": 0.4, "ZCG": 0.0, "WT": 1000.0, "MACH": [0.1], "ALT": [0.0]},
        plot_cmp=[1, 1, 1, 1], unit="ft",
    )


def test_flow5_probe_difference_and_antisym_aileron():
    decks = []

    def fake_run(deck):
        decks.append(deck)
        wing = next(w for w in deck["wings"] if w["name"] == "Wing")
        flaps = [s for s in wing["sections"] if "te_flap_deg" in s]
        angle = flaps[0]["te_flap_deg"] if flaps else 0.0
        antisym = bool(flaps and flaps[0].get("te_flap_antisym"))
        return {
            "alpha": [0.0],
            "CL": [0.2 + (0.0 if antisym else 0.01 * angle)],
            "CD": [0.02],
            "Cm": [0.0],
            "Cl": [0.002 * angle if antisym else 0.0],
            "Cn": [0.0],
            "CY": [0.0],
        }

    ac = _ac()
    rows = flow5_controls(ac, [5.0], mesh=("4", "2"), run=fake_run)
    flap = next(r for r in rows if r["surface"] == "flap")
    assert abs(flap["CL"] - 0.01) < 1e-9
    ail = next(r for r in rows if r["surface"] == "aileron")
    assert any(s.get("te_flap_antisym") is True for d in decks for w in d["wings"] for s in w["sections"])
    assert ail["Cl"] is not None
    assert ac.F["DELTA"] == 0.0
