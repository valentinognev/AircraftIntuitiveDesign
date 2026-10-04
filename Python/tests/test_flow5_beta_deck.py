"""flow5's deck writer has to be able to carry a sideslip.

``PlanePolar::setBetaSpec`` is the only lever the library offers for a sideslip
on a T1 polar, and ``flow5_run`` already reads ``polar.beta_deg`` (Task 2.1), but
``write_flow5_deck`` had no way to set it, so ``beta = 0`` was structural rather
than chosen. These tests pin the plumbing only -- that the deck says what it was
asked, and that ``beta`` does not disturb the alpha sweep it rides along with.
Nothing here runs the solver; ``test_flow5_overlay_signs.py`` proves the sideslip
actually reaches it.
"""

from aid.aircraft import load_jsonc
from aid.flow5_io import run_flow5, write_flow5_deck
from aid.paths import models_dir

MESH = ("10", "10")


def _cessna():
    return load_jsonc(models_dir() / "Cessna 172.jsonc")


def _captured_run_flow5(monkeypatch, beta=None, **kwargs):
    """Return the deck ``run_flow5`` would hand the helper, without running it."""
    decks: list[dict] = []
    monkeypatch.setattr(
        "aid.flow5_io.run_flow5_native",
        lambda deck, **k: decks.append(deck) or {"ok": True},
    )
    if beta is None:
        run_flow5(_cessna(), MESH, **kwargs)
    else:
        run_flow5(_cessna(), MESH, beta=beta, **kwargs)
    assert len(decks) == 1
    return decks[0]


def test_deck_defaults_beta_to_zero():
    assert write_flow5_deck(_cessna(), MESH)["polar"]["beta_deg"] == 0.0


def test_deck_carries_beta_through():
    assert write_flow5_deck(_cessna(), MESH, beta=5.0)["polar"]["beta_deg"] == 5.0


def test_deck_alpha_list_is_untouched_by_beta():
    flat = write_flow5_deck(_cessna(), MESH)["polar"]["alpha_deg"]
    tilted = write_flow5_deck(_cessna(), MESH, beta=5.0)["polar"]["alpha_deg"]
    assert flat == tilted


def test_deck_beta_accepts_a_negative_sideslip():
    assert write_flow5_deck(_cessna(), MESH, beta=-5.0)["polar"]["beta_deg"] == -5.0


def test_deck_beta_is_a_float_not_the_caller_s_int():
    # Task 3.1 resolves the default from ac.AERO["BETA"], which is a list. An int
    # would serialize as 5 rather than 5.0 and json_number() would still read it,
    # but the deck is a documented interface, so pin the type it is written as.
    assert isinstance(write_flow5_deck(_cessna(), MESH, beta=5)["polar"]["beta_deg"], float)


def test_deck_rest_is_identical_across_beta():
    # beta is one polar key and nothing else may move: a sideslip that also
    # touched the geometry would invalidate every alpha in the sweep.
    flat = write_flow5_deck(_cessna(), MESH)["polar"]
    tilted = write_flow5_deck(_cessna(), MESH, beta=5.0)["polar"]
    assert {k: v for k, v in tilted.items() if k != "beta_deg"} == {
        k: v for k, v in flat.items() if k != "beta_deg"
    }


def test_run_flow5_defaults_beta_to_zero(monkeypatch):
    deck = _captured_run_flow5(monkeypatch)
    assert deck["polar"]["beta_deg"] == 0.0


def test_run_flow5_passes_beta_into_the_deck(monkeypatch):
    assert _captured_run_flow5(monkeypatch, beta=7.5)["polar"]["beta_deg"] == 7.5


def test_run_flow5_keeps_timeout_keyword_only(monkeypatch):
    # The new positional beta must not have swallowed timeout, which main_window
    # and test_gui_analyze_flow5 pass by keyword.
    deck = _captured_run_flow5(monkeypatch, timeout=42)
    assert deck["polar"]["beta_deg"] == 0.0


def test_run_flow5_normalizes_to_frd_at_its_own_boundary(monkeypatch):
    # run_flow5 is the one place flow5's raw output becomes F-R-D. Sourced from a
    # stub so this pins the wrapper, not the solver: the four mapped channels are
    # mirrored and everything else passes through by identity.
    monkeypatch.setattr(
        "aid.flow5_io.run_flow5_native",
        lambda deck, **k: {
            "alpha": [0.0], "beta": [5.0],
            "Cx": [1.0], "Cz": [2.0], "Cl": [3.0], "Cn": [-4.0],
            "CY": [5.0], "CL": [6.0], "CD": [7.0], "Cm": [8.0],
            "CZa": [-5.2562], "Cnb": [0.1685],
        },
    )
    got = run_flow5(_cessna(), MESH, beta=5.0)
    assert got["Cx"] == [-1.0] and got["Cz"] == [-2.0]
    assert got["Cl"] == [-3.0] and got["Cn"] == [4.0]
    untouched = {"CY": [5.0], "CL": [6.0], "CD": [7.0], "Cm": [8.0],
                 "CZa": [-5.2562], "Cnb": [0.1685]}
    for key, value in untouched.items():
        assert got[key] == value, key


def test_write_flow5_deck_beta_is_keyword_and_positional_equivalent():
    ac = _cessna()
    assert write_flow5_deck(ac, MESH, 5.0) == write_flow5_deck(ac, MESH, beta=5.0)