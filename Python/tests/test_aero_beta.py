"""``AERO["BETA"]`` is the sideslip angle every solver reads, in degrees.

It is Python-only: ``Matlab/fsroot/code/AID.m``'s save list does not carry it, so
no ``.mat`` and no shipped ``.jsonc`` has the key. Every model therefore has to
resolve it to ``0.0`` (symmetric flight) rather than raising ``KeyError``, whether
the key is missing, the whole ``AERO`` block is missing, or the model came from
MATLAB at all.
"""

from pathlib import Path

import numpy as np
import pytest

from aid.aircraft import _aircraft_from_dict, load_jsonc, save_jsonc
from aid.jsonc import loads_jsonc
from aid.tornado_io import tornado_io

MODELS = Path(__file__).resolve().parents[1] / "models"


def _cessna_raw() -> dict:
    return loads_jsonc((MODELS / "Cessna 172.jsonc").read_text())


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


def test_tornado_state_uses_beta():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    ac.AERO["BETA"] = 5.0
    _, state = tornado_io(ac, ("10", "5"))
    assert state["betha"] == pytest.approx(np.deg2rad(5.0))


def test_tornado_beta_defaults_to_zero():
    ac = load_jsonc(MODELS / "Cessna 172.jsonc")
    _, state = tornado_io(ac, ("10", "5"))
    assert state["betha"] == pytest.approx(0.0)