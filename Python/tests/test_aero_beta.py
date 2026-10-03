"""``AERO["BETA"]`` is the sideslip angle every solver reads, in degrees.

It is Python-only: ``Matlab/fsroot/code/AID.m``'s save list does not carry it, so
no ``.mat`` and no shipped ``.jsonc`` has the key. Every model therefore has to
resolve it to ``0.0`` (symmetric flight) rather than raising ``KeyError``, whether
the key is missing, the whole ``AERO`` block is missing, or the model came from
MATLAB at all.

Two engines read it: Tornado via ``state["betha"]`` and flow5 via
``polar.beta_deg``. ``test_flow5_beta_deck.py`` covers flow5's own ``beta=``
keyword and its ``0.0`` default for a shipped model; the flow5 cases below are
the ones only this file can make, namely a *non-zero model* reaching the deck and
an explicit argument beating it.
"""

from pathlib import Path

import numpy as np
import pytest

from aid.aircraft import _aircraft_from_dict, load_jsonc, load_mat, save_jsonc
from aid.flow5_io import run_flow5, write_flow5_deck
from aid.jsonc import loads_jsonc
from aid.paths import matlab_code
from aid.tornado_io import tornado_io

MODELS = Path(__file__).resolve().parents[1] / "models"
MESH = ("10", "5")


def _cessna_raw() -> dict:
    return loads_jsonc((MODELS / "Cessna 172.jsonc").read_text())


def _cessna(beta: float | None = None):
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    if beta is not None:
        ac.AERO["BETA"] = beta
    return ac


def _captured_run_flow5(monkeypatch, ac=None, **kwargs) -> dict:
    """The deck ``run_flow5`` would hand the helper, without running the solver."""
    decks: list[dict] = []
    monkeypatch.setattr(
        "aid.flow5_io.run_flow5_native",
        lambda deck, **k: decks.append(deck) or {"ok": True},
    )
    run_flow5(_cessna() if ac is None else ac, MESH, **kwargs)
    assert len(decks) == 1
    return decks[0]


def test_beta_defaults_to_zero():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    assert ac.AERO["BETA"] == 0.0


def test_every_shipped_model_resolves_beta():
    for path in sorted(MODELS.glob("*.jsonc")):
        assert isinstance(load_jsonc(path).AERO["BETA"], float), path.name


def test_beta_survives_a_jsonc_round_trip(tmp_path):
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    ac.AERO["BETA"] = 5.0
    out = tmp_path / "m.jsonc"
    save_jsonc(ac, out)
    assert load_jsonc(out).AERO["BETA"] == 5.0
    assert "// " in out.read_text(), "every JSONC key needs a comment"
    assert '"BETA"' in out.read_text()


def test_missing_beta_key_is_not_an_error():
    raw = _cessna_raw()
    raw["AERO"].pop("BETA", None)
    assert _aircraft_from_dict(raw).AERO["BETA"] == 0.0


def test_missing_aero_container_is_not_an_error():
    raw = _cessna_raw()
    raw.pop("AERO")
    assert _aircraft_from_dict(raw).AERO["BETA"] == 0.0


def test_a_mat_model_resolves_beta_to_zero():
    # The .mat path is load_mat, not _aircraft_from_dict, so it normalises
    # separately. Nothing under Python/models/ may gain a BETA key to make this
    # pass, and Matlab/.../Cessna 172.mat has no such field to convert.
    ac = load_mat(matlab_code() / "Models" / "Cessna 172.mat")
    assert ac.AERO["BETA"] == 0.0
    assert isinstance(ac.AERO["BETA"], float)


def test_tornado_state_uses_beta():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    ac.AERO["BETA"] = 5.0
    _, state = tornado_io(ac, ("10", "5"))
    assert state["betha"] == pytest.approx(np.deg2rad(5.0))


def test_tornado_beta_defaults_to_zero():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    _, state = tornado_io(ac, ("10", "5"))
    assert state["betha"] == pytest.approx(0.0)


def test_flow5_deck_beta_is_read_from_the_model():
    # The wiring this task exists to add. Reverting the ``beta=None`` branch of
    # write_flow5_deck to a literal 0.0 leaves every other test in the suite
    # green, so this is its only guard.
    assert write_flow5_deck(_cessna(5.0), MESH)["polar"]["beta_deg"] == 5.0


def test_flow5_deck_beta_is_zero_when_the_document_never_had_the_key():
    # Complements rather than repeats test_deck_defaults_beta_to_zero, which reads
    # a shipped model; this one pops the key so the value arrives through
    # _aero_from_any's default, which is the path a hand-edited file takes.
    raw = _cessna_raw()
    raw["AERO"].pop("BETA", None)
    assert write_flow5_deck(_aircraft_from_dict(raw), MESH)["polar"]["beta_deg"] == 0.0


def test_flow5_explicit_beta_overrides_the_model():
    # The other half of the branch: an argument still wins, so a caller that
    # wants a one-off sideslip does not have to mutate the aircraft first.
    assert write_flow5_deck(_cessna(5.0), MESH, beta=2.0)["polar"]["beta_deg"] == 2.0


def test_run_flow5_reads_beta_from_the_model(monkeypatch):
    # run_flow5 is the entry point the GUI and the API call, and it resolves
    # nothing itself -- it forwards ``beta`` to write_flow5_deck. Pin the value
    # that reaches the helper through the whole wrapper.
    assert _captured_run_flow5(monkeypatch, ac=_cessna(5.0))["polar"]["beta_deg"] == 5.0


def test_save_omits_an_aero_key_left_at_its_default(tmp_path):
    # The shipped .jsonc files predate AERO_DEFAULTS, so writing a default back
    # would append a line to all 23 and break the byte-identical geometry round
    # trip in test_aircraft_results.py. Same rule save_jsonc already applies to
    # an absent cg_data and an empty results: only non-defaults are news.
    out = tmp_path / "m.jsonc"
    save_jsonc(_cessna(0.0), out)
    assert '"BETA"' not in out.read_text()
    assert load_jsonc(out).AERO["BETA"] == 0.0


def test_save_writes_an_aero_key_that_differs_from_its_default(tmp_path):
    out = tmp_path / "m.jsonc"
    save_jsonc(_cessna(5.0), out)
    text = out.read_text()
    assert '"BETA": 5.0 // sideslip angle in degrees (0 = symmetric flight)' in text
    assert load_jsonc(out).AERO["BETA"] == 5.0
