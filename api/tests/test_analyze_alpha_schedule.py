import pytest
from fastapi.testclient import TestClient

from aid.aircraft import Aircraft
from aid_web import analyze as analyze_mod
from aid_web.app import aircraft_from_json, app

# A deliberately sparse schedule, set explicitly so the tests do not depend on
# what a shipped model happens to store. The default schedule is that envelope
# on a 1-degree step.
SPARSE = [-4, 0, 4, 8, 12]
CESSNA_EXPANDED = [-4.0 + i for i in range(17)]

_COEFF = {
    "alpha": [0.0],
    "CL": [0.2],
    "CD": [0.02],
    "Cm": [0.0],
    "MACH": 0.2,
}

_SOLVERS = {
    "aid_web.analyze.run_datcom": lambda ac, workdir: dict(_COEFF),
    "aid_web.analyze.run_tornado": lambda ac, mesh: dict(_COEFF),
    "aid_web.analyze.run_avl_full": lambda ac, mesh, workdir: dict(_COEFF),
    "aid_web.analyze.run_flow5": lambda ac, mesh: dict(_COEFF),
    "aid_web.analyze.control_report": lambda ac, solver, **kw: {"rows": []},
}

_ENTRIES = [
    ("analyze_datcom", ()),
    ("analyze_tornado", (("6", "3"),)),
    ("analyze_avl", (("6", "3"),)),
    ("analyze_flow5", (("6", "3"),)),
    ("control_derivatives", ("flow5",)),
]

_ENTRY_IDS = ["datcom", "tornado", "avl", "flow5", "control_derivatives"]


def _cessna_aircraft() -> Aircraft:
    data = TestClient(app).get("/models/Cessna%20172").json()["aircraft"]
    ac = aircraft_from_json(data)
    ac.AERO["ALSCHD"] = list(SPARSE)
    return ac


def _stub_solvers(monkeypatch, seen: list | None = None) -> list:
    """Stub every solver, recording the ALSCHD each one is handed when ``seen``."""

    def wrap(fn):
        def stub(*args, **kw):
            if seen is not None:
                seen.append(list(args[0].AERO["ALSCHD"]))
            return fn(*args, **kw)

        return stub

    for target, fn in _SOLVERS.items():
        monkeypatch.setattr(target, wrap(fn))
    return seen


@pytest.mark.parametrize(("entry", "args"), _ENTRIES, ids=_ENTRY_IDS)
def test_entry_points_expand_alschd_before_the_solver(monkeypatch, entry, args):
    seen = _stub_solvers(monkeypatch, seen=[])
    ac = _cessna_aircraft()
    getattr(analyze_mod, entry)(ac, *args)
    assert seen == [CESSNA_EXPANDED]
    assert ac.AERO["ALSCHD"] == CESSNA_EXPANDED


@pytest.mark.parametrize(("entry", "args"), _ENTRIES, ids=_ENTRY_IDS)
def test_entry_points_do_not_introduce_alschd(monkeypatch, entry, args):
    _stub_solvers(monkeypatch)
    ac = _cessna_aircraft()
    ac.AERO.pop("ALSCHD")
    getattr(analyze_mod, entry)(ac, *args)
    assert "ALSCHD" not in ac.AERO
