import math

import pytest
from fastapi.testclient import TestClient

from aid.aircraft import Aircraft
from aid_web.app import aircraft_from_json, app

# Same coefficient stub as test_analyze_solvers.TORNADO_STUB. CL must stay unchanged.
TORNADO_STUB = {
    "alpha": [-2.0, 0.0, 4.0],
    "CL": [0.1, 0.3, 0.5],
    "CD": [0.02, 0.03, 0.04],
    "Cm": [0.01, 0.0, -0.02],
    "MACH": 0.2,
}

SPANWISE_STUB = [{"name": "Wing", "y": [1.0], "dy": [0.5], "Cl": [0.3]}]

_COEFF = {
    "alpha": [0.0],
    "CL": [0.2],
    "CD": [0.02],
    "Cm": [0.0],
    "MACH": 0.2,
}


def _cessna_json():
    return TestClient(app).get("/models/Cessna%20172").json()["aircraft"]


def _cessna_aircraft() -> Aircraft:
    return aircraft_from_json(_cessna_json())


def _stub_tornado_chain(monkeypatch, spanwise):
    monkeypatch.setattr(
        "aid_web.analyze.tornado_io", lambda ac, mesh: ({}, {"alpha": 0.0})
    )
    monkeypatch.setattr(
        "aid_web.analyze.lattice_setup", lambda geo, state, mode: ({}, {})
    )
    monkeypatch.setattr(
        "aid_web.analyze.set_boundary", lambda lattice, geo, state: lattice
    )
    monkeypatch.setattr("aid_web.analyze.solve", lambda state, geo, lattice: {})
    monkeypatch.setattr(
        "aid_web.analyze.coeff_create",
        lambda raw, lattice, state, ref, geo: dict(TORNADO_STUB),
    )
    monkeypatch.setattr("aid_web.analyze.tornado_spanwise", spanwise, raising=False)


def test_tornado_attaches_spanwise_and_keeps_cl_and_handshake(monkeypatch):
    _stub_tornado_chain(monkeypatch, lambda *args, **kwargs: list(SPANWISE_STUB))
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna_json(), "solver": "tornado"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["raw"]["spanwise"][0]["Cl"] == [0.3]
    assert body["raw"]["spanwise"] == SPANWISE_STUB
    assert body["raw"]["CL"] == [0.1, 0.3, 0.5]
    assert list(body["payload"]["tables"]) == ["cl", "cd", "cm"]


def test_tornado_spanwise_error_omits_spanwise_and_keeps_cl(monkeypatch):
    called = []

    def boom(*args, **kwargs):
        called.append(True)
        raise RuntimeError("spanwise failed")

    _stub_tornado_chain(monkeypatch, boom)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna_json(), "solver": "tornado"}
    )
    assert called == [True]
    assert r.status_code == 200
    body = r.json()
    assert "spanwise" not in body["raw"]
    assert body["raw"]["CL"] == [0.1, 0.3, 0.5]


def test_handbook_spanwise_cessna_equal_finite():
    import aid_web.analyze as analyze_mod

    handbook_spanwise = getattr(analyze_mod, "handbook_spanwise", None)
    assert callable(handbook_spanwise)
    result = handbook_spanwise(_cessna_aircraft())
    assert isinstance(result, dict)
    assert set(result) == {"y", "Cl"}
    y, cl = result["y"], result["Cl"]
    assert isinstance(y, list) and isinstance(cl, list)
    assert len(y) == len(cl) >= 2
    assert all(isinstance(v, float) and math.isfinite(v) for v in y)
    assert all(isinstance(v, float) and math.isfinite(v) for v in cl)


def test_handbook_spanwise_failure_returns_none(monkeypatch):
    import aid_web.analyze as analyze_mod

    handbook_spanwise = getattr(analyze_mod, "handbook_spanwise", None)
    assert callable(handbook_spanwise)

    def boom(*args, **kwargs):
        raise RuntimeError("stations failed")

    monkeypatch.setattr("aid_web.analyze.planform_stations", boom, raising=False)
    assert handbook_spanwise(_cessna_aircraft()) is None


def test_handbook_none_omits_key(monkeypatch):
    seen = []

    def none_handbook(ac):
        seen.append(ac)
        return None

    monkeypatch.setattr(
        "aid_web.analyze.handbook_spanwise", none_handbook, raising=False
    )
    monkeypatch.setattr(
        "aid_web.analyze.run_datcom", lambda ac, workdir: dict(_COEFF)
    )
    r = TestClient(app).post("/analyze", json={"aircraft": _cessna_json()})
    assert r.status_code == 200
    assert seen
    assert "handbook" not in r.json()
    assert "handbook" not in r.json()["raw"]


@pytest.mark.parametrize(
    "solver,target,nargs",
    [
        ("datcom", "aid_web.analyze.run_datcom", 2),
        ("tornado", "aid_web.analyze.run_tornado", 2),
        ("avl", "aid_web.analyze.run_avl_full", 3),
        ("flow5", "aid_web.analyze.run_flow5", 2),
    ],
)
def test_each_solver_puts_handbook_on_result_not_raw(monkeypatch, solver, target, nargs):
    def stub(*args):
        assert len(args) == nargs
        return dict(_COEFF)

    monkeypatch.setattr(target, stub)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna_json(), "solver": solver}
    )
    assert r.status_code == 200
    body = r.json()
    assert "handbook" not in body["raw"]
    handbook = body["handbook"]
    assert isinstance(handbook, dict)
    assert len(handbook["y"]) == len(handbook["Cl"]) >= 2
    assert all(math.isfinite(v) for v in handbook["y"])
    assert all(math.isfinite(v) for v in handbook["Cl"])
