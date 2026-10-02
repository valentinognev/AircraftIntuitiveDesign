# Python/tests/test_compare_sweep.py
"""Which alpha sweep each solver leg is flown on, and what the report records.

The MATLAB gold is a fixture with its own inputs, and DATCOM's output depends on
the alpha grid it is asked for -- so only the DATCOM leg flies the gold's sweep.
Tornado and AVL have no gold alpha axis and fly the model's own schedule.
"""

import json

from aid import compare
from aid.aircraft import load_jsonc
from aid.paths import models_dir, results_dir

CESSNA = "Cessna 172"


def _model_sweep() -> list[float]:
    ac = load_jsonc(models_dir() / f"{CESSNA}.jsonc")
    return [float(a) for a in ac.AERO["ALSCHD"]]


def _gold_sweep() -> list[float]:
    gold = json.loads((results_dir() / "matlab" / CESSNA / "datcom.json").read_text())
    return [float(a) for a in gold["alpha"]]


def _stub_runs(monkeypatch, seen: dict) -> None:
    """Replace the three solver leaves, recording the aircraft each received.

    The stubbed coefficients carry every key the gold compares, so the comparison
    runs to a verdict instead of raising; the values are irrelevant here.
    """

    def leaf(name):
        gold = json.loads(
            (results_dir() / "matlab" / CESSNA / f"{name}.json").read_text()
        )
        stub = {key: 0.0 for key in gold}

        def run(ac, *args, **kwargs):
            seen[name] = ac
            return {"status": "ok", "coeffs": stub, "error": None}

        return run

    for attr, name in (
        ("_run_datcom_safe", "datcom"),
        ("_run_tornado", "tornado"),
        ("_run_avl", "avl"),
    ):
        monkeypatch.setattr(compare, attr, leaf(name))


def test_only_the_datcom_leg_flies_the_gold_sweep(monkeypatch):
    """The pin is justified by DATCOM alone; the other two keep the model's."""
    seen: dict = {}
    _stub_runs(monkeypatch, seen)
    compare.compare_to_matlab(CESSNA)
    model, gold = _model_sweep(), _gold_sweep()
    assert model != gold, "fixture is degenerate, the sweep would not discriminate"
    assert seen["datcom"].AERO["ALSCHD"] == gold
    assert seen["tornado"].AERO["ALSCHD"] == model
    assert seen["avl"].AERO["ALSCHD"] == model


def test_the_pinned_aircraft_is_separate_and_the_model_is_not_mutated(monkeypatch):
    """The pin must not hand the same object to another solver, nor edit in place."""
    seen: dict = {}
    _stub_runs(monkeypatch, seen)
    compare.compare_to_matlab(CESSNA)
    assert seen["datcom"] is not seen["tornado"]
    assert seen["datcom"] is not seen["avl"]
    assert seen["tornado"] is seen["avl"]
    assert seen["datcom"].AERO is not seen["tornado"].AERO


def test_report_records_the_sweep_and_its_provenance(monkeypatch):
    seen: dict = {}
    _stub_runs(monkeypatch, seen)
    report = compare.compare_to_matlab(CESSNA)
    model, gold = _model_sweep(), _gold_sweep()
    assert report["datcom"]["alpha"] == gold
    assert report["datcom"]["alpha_source"] == "gold"
    for solver in ("tornado", "avl"):
        assert report[solver]["alpha"] == model
        assert report[solver]["alpha_source"] == "model"


def test_the_written_report_is_self_describing(monkeypatch):
    """A reader of the artifact alone must see which schedule ran, and where from."""
    _stub_runs(monkeypatch, {})
    compare.compare_to_matlab(CESSNA)
    written = json.loads((results_dir() / "compare" / f"{CESSNA}.json").read_text())
    assert written["datcom"]["alpha"] == _gold_sweep()
    assert written["datcom"]["alpha_source"] == "gold"
    assert written["tornado"]["alpha"] == _model_sweep()
    assert written["tornado"]["alpha_source"] == "model"
    assert written["avl"]["alpha_source"] == "model"


def test_report_records_the_model_sweep_when_no_gold_alpha_exists(monkeypatch):
    monkeypatch.setattr(compare, "_gold_alpha", lambda matlab_dir: None)
    seen: dict = {}
    _stub_runs(monkeypatch, seen)
    report = compare.compare_to_matlab(CESSNA)
    model = _model_sweep()
    assert seen["datcom"].AERO["ALSCHD"] == model
    for solver in ("datcom", "tornado", "avl"):
        assert report[solver]["alpha"] == model
        assert report[solver]["alpha_source"] == "model"