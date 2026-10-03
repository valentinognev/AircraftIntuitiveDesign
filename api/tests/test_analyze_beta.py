"""The sideslip travels in the request body and lands on AERO["BETA"].

One value in one place: analyze.py pushes the requested degrees onto the aircraft
before dispatching, so Tornado (state["betha"]) and flow5 (polar beta_deg) read the
same number and neither solver gains a beta argument of its own.
"""

import inspect

from fastapi.testclient import TestClient

from aid_web import analyze as analyze_mod
from aid_web.analyze import SOLVERS
from aid_web.app import app

COEFF = {
    "alpha": [0.0],
    "CL": [0.2],
    "CD": [0.02],
    "Cm": [0.0],
    "MACH": 0.2,
}

_RUNNERS = {
    "aid_web.analyze.run_datcom": lambda ac, workdir: dict(COEFF),
    "aid_web.analyze.run_tornado": lambda ac, mesh: dict(COEFF),
    "aid_web.analyze.run_avl_full": lambda ac, mesh, workdir: dict(COEFF),
    "aid_web.analyze.run_flow5": lambda ac, mesh: dict(COEFF),
}


def _cessna() -> dict:
    return TestClient(app).get("/models/Cessna%20172").json()["aircraft"]


def _swept(beta: float) -> dict:
    """A Cessna whose own AERO block already asks for a sideslip."""
    data = _cessna()
    data["AERO"]["BETA"] = beta
    return data


def _spy(monkeypatch) -> dict[str, list]:
    """Record the AERO["BETA"] every solver is handed, one list per solver."""
    seen: dict[str, list] = {}

    def wrap(name: str, fn):
        def stub(*args, **kw):
            seen.setdefault(name, []).append(args[0].AERO.get("BETA"))
            return fn(*args, **kw)

        return stub

    for target, fn in _RUNNERS.items():
        name = target.rsplit(".", 1)[-1]
        monkeypatch.setattr(target, wrap(name, fn))
    return seen


def test_analyze_defaults_beta_to_zero(monkeypatch):
    seen = _spy(monkeypatch)
    r = TestClient(app).post("/analyze", json={"aircraft": _cessna(), "solver": "tornado"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert seen == {"run_tornado": [0.0]}


def test_analyze_accepts_beta_in_degrees(monkeypatch):
    seen = _spy(monkeypatch)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna(), "solver": "tornado", "beta": 5.0}
    )
    assert r.status_code == 200
    assert seen == {"run_tornado": [5.0]}


def test_negative_beta_reaches_the_solver(monkeypatch):
    seen = _spy(monkeypatch)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna(), "solver": "tornado", "beta": -5.0}
    )
    assert r.status_code == 200
    assert seen == {"run_tornado": [-5.0]}


def test_beta_goes_to_every_solver_path(monkeypatch):
    seen = _spy(monkeypatch)
    for solver in ("datcom", "tornado", "avl", "flow5"):
        r = TestClient(app).post(
            "/analyze", json={"aircraft": _cessna(), "solver": solver, "beta": 3.0}
        )
        assert r.status_code == 200, solver
    assert seen == {target.rsplit(".", 1)[-1]: [3.0] for target in _RUNNERS}


def test_only_the_top_level_analyze_takes_a_beta():
    assert "beta" in inspect.signature(analyze_mod.analyze).parameters
    for per_solver in (
        analyze_mod.analyze_datcom,
        analyze_mod.analyze_tornado,
        analyze_mod.analyze_avl,
        analyze_mod.analyze_flow5,
    ):
        assert "beta" not in inspect.signature(per_solver).parameters


def test_apply_beta_fills_in_a_missing_key():
    ac = TestClient(app).get("/models/Cessna%20172")
    from aid_web.app import aircraft_from_json

    plane = aircraft_from_json(ac.json()["aircraft"])
    plane.AERO.pop("BETA", None)
    analyze_mod.apply_beta(plane, 2.5)
    assert plane.AERO["BETA"] == 2.5


def test_stability_accepts_beta(monkeypatch):
    seen = []

    def spy(ac):
        seen.append(ac.AERO.get("BETA"))
        return {"x_cg": 1.0, "Cm_CL": 0.0, "summary": []}

    monkeypatch.setattr("aid_web.app.aircraft_stability", spy)
    r = TestClient(app).post("/stability", json={"aircraft": _cessna(), "beta": 5.0})
    assert r.status_code == 200
    assert seen == [5.0]


def test_beta_zero_is_the_same_as_omitting_it():
    client = TestClient(app)
    ac = _cessna()
    assert client.post("/stability", json={"aircraft": ac}).json() == client.post(
        "/stability", json={"aircraft": ac, "beta": 0.0}
    ).json()


def test_analyze_without_beta_matches_beta_zero(monkeypatch):
    client = TestClient(app)
    ac = _cessna()
    _spy(monkeypatch)
    bare = client.post("/analyze", json={"aircraft": ac, "solver": "tornado"}).json()
    _spy(monkeypatch)
    zero = client.post(
        "/analyze", json={"aircraft": ac, "solver": "tornado", "beta": 0.0}
    ).json()
    assert bare == zero


def test_unknown_solver_still_400s():
    r = TestClient(app).post("/analyze", json={"aircraft": _cessna(), "solver": "vlm2"})
    assert r.status_code == 400


# The payload's axes.beta is a flight-condition field, so it must record the condition
# the data was computed at -- not the condition that was asked for. tornado and flow5 can
# be flown at a sideslip; DATCOM's $FLTCON and AVL's run-case menu have no beta at all,
# so their runs are at zero whatever the request says and their payload must say zero.
BETA_CAPABLE = {"tornado", "flow5"}
NO_SIDESLIP_CAPABILITY = {"datcom", "avl"}


def _payload_beta(client, solver, **extra):
    r = client.post(
        "/analyze",
        json={"aircraft": _cessna(), "solver": solver, "beta": 5.0, **extra},
    )
    assert r.status_code == 200, solver
    return r.json()["payload"]["axes"]["beta"]


def test_payload_beta_names_the_sideslip_the_engine_was_handed(monkeypatch):
    """tornado and flow5 fly the requested sideslip, so the payload reports it."""
    _spy(monkeypatch)
    client = TestClient(app)
    assert _payload_beta(client, "tornado") == [5.0]
    assert _payload_beta(client, "flow5") == [5.0]


def test_payload_beta_stays_zero_for_datcom_and_avl_at_a_sideslip(monkeypatch):
    """DATCOM and AVL cannot fly a sideslip, so reporting 5.0 would be a fresh lie."""
    seen = _spy(monkeypatch)
    client = TestClient(app)
    assert _payload_beta(client, "datcom") == [0.0]
    assert _payload_beta(client, "avl") == [0.0]
    # The aircraft really did carry the request; only the payload disagrees with it.
    assert seen["run_datcom"] == [5.0]
    assert seen["run_avl_full"] == [5.0]


def test_payload_beta_stays_zero_for_datcom_and_avl_when_the_aircraft_carries_one(
    monkeypatch,
):
    """An absent top-level beta still defers to AERO["BETA"], and is still not flown."""
    _spy(monkeypatch)
    client = TestClient(app)
    for solver in ("datcom", "avl"):
        r = client.post("/analyze", json={"aircraft": _swept(9.0), "solver": solver})
        assert r.status_code == 200, solver
        assert r.json()["payload"]["axes"]["beta"] == [0.0], solver


def test_every_solver_is_classified_by_the_beta_capable_set():
    """A new solver must be classified, not silently assumed to fly a sideslip."""
    assert set(analyze_mod.BETA_CAPABLE_SOLVERS) == BETA_CAPABLE
    assert set(SOLVERS) - set(analyze_mod.BETA_CAPABLE_SOLVERS) == NO_SIDESLIP_CAPABILITY


def test_payload_beta_is_zero_at_an_upright_flight(monkeypatch):
    _spy(monkeypatch)
    client = TestClient(app)
    for solver in sorted(BETA_CAPABLE):
        r = client.post("/analyze", json={"aircraft": _cessna(), "solver": solver})
        assert r.json()["payload"]["axes"]["beta"] == [0.0], solver


# R33: absent and null both mean "keep whatever AERO["BETA"] already says", because
# the Aero tab's Beta field commits null when blank and that must not 422. An explicit
# 0 is the opposite instruction: force the run upright.


def test_null_beta_is_accepted_not_rejected(monkeypatch):
    seen = _spy(monkeypatch)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _swept(5.0), "solver": "tornado", "beta": None}
    )
    assert r.status_code == 200
    assert seen == {"run_tornado": [5.0]}


def test_absent_beta_defers_to_the_aircraft(monkeypatch):
    seen = _spy(monkeypatch)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _swept(7.0), "solver": "tornado"}
    )
    assert r.status_code == 200
    assert seen == {"run_tornado": [7.0]}


def test_explicit_zero_overrides_the_aircraft(monkeypatch):
    seen = _spy(monkeypatch)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _swept(7.0), "solver": "tornado", "beta": 0.0}
    )
    assert r.status_code == 200
    assert seen == {"run_tornado": [0.0]}


def test_explicit_zero_is_not_the_same_as_omitting_it(monkeypatch):
    """The None-versus-0 distinction, read off the wire rather than off the aircraft."""
    client = TestClient(app)
    swept = _swept(7.0)
    _spy(monkeypatch)
    bare = client.post(
        "/analyze", json={"aircraft": swept, "solver": "tornado"}
    ).json()["payload"]["axes"]["beta"]
    _spy(monkeypatch)
    forced = client.post(
        "/analyze", json={"aircraft": swept, "solver": "tornado", "beta": 0.0}
    ).json()["payload"]["axes"]["beta"]
    _spy(monkeypatch)
    blank = client.post(
        "/analyze", json={"aircraft": swept, "solver": "tornado", "beta": None}
    ).json()["payload"]["axes"]["beta"]
    assert bare == [7.0]
    assert blank == [7.0]
    assert forced == [0.0]


def test_null_beta_defers_on_stability(monkeypatch):
    seen = []

    def spy(ac):
        seen.append(ac.AERO.get("BETA"))
        return {"summary": []}

    monkeypatch.setattr("aid_web.app.aircraft_stability", spy)
    r = TestClient(app).post("/stability", json={"aircraft": _swept(4.0), "beta": None})
    assert r.status_code == 200
    assert seen == [4.0]


def test_explicit_zero_overrides_on_stability(monkeypatch):
    seen = []

    def spy(ac):
        seen.append(ac.AERO.get("BETA"))
        return {"summary": []}

    monkeypatch.setattr("aid_web.app.aircraft_stability", spy)
    r = TestClient(app).post("/stability", json={"aircraft": _swept(4.0), "beta": 0.0})
    assert r.status_code == 200
    assert seen == [0.0]


def test_apply_beta_leaves_the_aircraft_alone_for_none():
    from aid_web.app import aircraft_from_json

    plane = aircraft_from_json(_swept(3.0))
    assert analyze_mod.apply_beta(plane, None) is plane
    assert plane.AERO["BETA"] == 3.0


def test_control_derivatives_defers_to_the_aircraft(monkeypatch):
    seen = []
    monkeypatch.setattr(
        "aid_web.analyze.control_report",
        lambda ac, solver, **kw: seen.append(ac.AERO.get("BETA")) or {"rows": []},
    )
    r = TestClient(app).post(
        "/control-derivatives", json={"aircraft": _swept(6.0), "solver": "flow5"}
    )
    assert r.status_code == 200
    assert seen == [6.0]


def test_control_derivatives_takes_an_explicit_beta(monkeypatch):
    seen = []
    monkeypatch.setattr(
        "aid_web.analyze.control_report",
        lambda ac, solver, **kw: seen.append(ac.AERO.get("BETA")) or {"rows": []},
    )
    r = TestClient(app).post(
        "/control-derivatives",
        json={"aircraft": _swept(6.0), "solver": "flow5", "beta": 0.0},
    )
    assert r.status_code == 200
    assert seen == [0.0]
