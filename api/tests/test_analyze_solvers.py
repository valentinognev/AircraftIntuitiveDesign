import subprocess

from fastapi.testclient import TestClient

from aid_web.app import app

TORNADO_STUB = {
    "alpha": [-2.0, 0.0, 4.0],
    "CL": [0.1, 0.3, 0.5],
    "CD": [0.02, 0.03, 0.04],
    "Cm": [0.01, 0.0, -0.02],
    "MACH": 0.2,
}

AVL_STUB = {
    "alpha": [0.0, 4.0],
    "CLtot": [0.2, 0.6],
    "CDtot": [0.02, 0.05],
    "Cmtot": [0.0, -0.03],
    "mach": 0.3,
}

FLOW5_STUB = {
    "alpha": [-4.0, 0.0, 8.0],
    "CL": [0.0, 0.25, 0.8],
    "CD": [0.02, 0.02, 0.06],
    "Cm": [0.02, 0.0, -0.04],
    "MACH": [0.03],
}


def _cessna():
    return TestClient(app).get("/models/Cessna%20172").json()["aircraft"]


def _assert_handshake(payload, *, solver, alpha, cl, cd, cm, mach):
    assert payload["source"] == "aid"
    assert payload["solver"] == solver
    assert payload["axes"] == {"mach": [mach], "alpha": alpha, "beta": [0]}
    assert payload["tables"]["cl"] == [cl]
    assert payload["tables"]["cd"] == [cd]
    assert payload["tables"]["cm"] == [cm]
    assert payload["ref"] == {}


def test_analyze_tornado_maps_stub_to_payload(monkeypatch):
    seen = []

    def stub(ac, mesh):
        seen.append(mesh)
        return dict(TORNADO_STUB)

    monkeypatch.setattr("aid_web.analyze.run_tornado", stub)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna(), "solver": "tornado"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["solver"] == "tornado"
    assert body["raw"]["CL"] == [0.1, 0.3, 0.5]
    _assert_handshake(
        body["payload"],
        solver="tornado",
        alpha=[-2.0, 0.0, 4.0],
        cl=[0.1, 0.3, 0.5],
        cd=[0.02, 0.03, 0.04],
        cm=[0.01, 0.0, -0.02],
        mach=0.2,
    )
    assert seen == [("10", "5")]


def test_analyze_avl_maps_cltot_to_payload(monkeypatch):
    seen = []

    def stub(ac, mesh, workdir):
        seen.append(mesh)
        return dict(AVL_STUB)

    monkeypatch.setattr("aid_web.analyze.run_avl_full", stub)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna(), "solver": "avl"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["solver"] == "avl"
    assert body["raw"]["CL"] == [0.2, 0.6]
    _assert_handshake(
        body["payload"],
        solver="avl",
        alpha=[0.0, 4.0],
        cl=[0.2, 0.6],
        cd=[0.02, 0.05],
        cm=[0.0, -0.03],
        mach=0.3,
    )
    assert seen == [("10", "10")]


def test_analyze_flow5_maps_stub_to_payload(monkeypatch):
    seen = []

    def stub(ac, mesh):
        seen.append(mesh)
        return dict(FLOW5_STUB)

    monkeypatch.setattr("aid_web.analyze.run_flow5", stub)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna(), "solver": "flow5"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["solver"] == "flow5"
    assert body["raw"]["CL"] == [0.0, 0.25, 0.8]
    _assert_handshake(
        body["payload"],
        solver="flow5",
        alpha=[-4.0, 0.0, 8.0],
        cl=[0.0, 0.25, 0.8],
        cd=[0.02, 0.02, 0.06],
        cm=[0.02, 0.0, -0.04],
        mach=0.03,
    )
    assert seen == [("10", "10")]


def test_analyze_passes_requested_mesh(monkeypatch):
    seen = []

    def stub(ac, mesh):
        seen.append(mesh)
        return dict(TORNADO_STUB)

    monkeypatch.setattr("aid_web.analyze.run_tornado", stub)
    r = TestClient(app).post(
        "/analyze",
        json={"aircraft": _cessna(), "solver": "tornado", "mesh": ["8", "4"]},
    )
    assert r.status_code == 200
    assert seen == [("8", "4")]


def test_omitted_solver_still_datcom(monkeypatch):
    monkeypatch.setattr(
        "aid_web.analyze.run_datcom",
        lambda _ac, _workdir: {
            "alpha": [0.0],
            "CL": [0.2],
            "CD": [0.02],
            "Cm": [0.0],
            "MACH": 0.3,
        },
    )
    r = TestClient(app).post("/analyze", json={"aircraft": _cessna()})
    assert r.status_code == 200
    assert r.json()["solver"] == "datcom"
    assert r.json()["payload"]["solver"] == "datcom"


def test_unknown_solver_is_400():
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna(), "solver": "xfoil"}
    )
    assert r.status_code == 400
    body = r.json()
    assert body["ok"] is False
    assert "error" in body
    assert body["error"]


def test_avl_file_not_found_is_400(monkeypatch):
    def boom(ac, mesh, workdir):
        raise FileNotFoundError("missing avl")

    monkeypatch.setattr("aid_web.analyze.run_avl_full", boom)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna(), "solver": "avl"}
    )
    assert r.status_code == 400
    assert r.json() == {"ok": False, "error": "missing avl"}


def test_flow5_called_process_error_is_400(monkeypatch):
    exc = subprocess.CalledProcessError(1, ["flow5_run"])

    def boom(ac, mesh):
        raise exc

    monkeypatch.setattr("aid_web.analyze.run_flow5", boom)
    r = TestClient(app).post(
        "/analyze", json={"aircraft": _cessna(), "solver": "flow5"}
    )
    assert r.status_code == 400
    assert r.json() == {"ok": False, "error": str(exc)}


def test_analyze_timeout_expired_is_400(monkeypatch):
    exc = subprocess.TimeoutExpired(["datcom"], 120)

    def boom(_ac, _workdir):
        raise exc

    monkeypatch.setattr("aid_web.analyze.run_datcom", boom)
    r = TestClient(app).post("/analyze", json={"aircraft": _cessna()})
    assert r.status_code == 400
    assert r.json() == {"ok": False, "error": str(exc)}
