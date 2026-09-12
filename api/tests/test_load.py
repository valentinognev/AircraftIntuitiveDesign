from fastapi.testclient import TestClient
from aid_web.app import app


def test_list_includes_cessna():
    names = TestClient(app).get("/models").json()["names"]
    assert "Cessna 172" in names


def test_load_cessna_has_WG():
    r = TestClient(app).get("/models/Cessna%20172")
    assert r.json()["ok"]
    assert "CHRDR" in r.json()["aircraft"]["WG"]


def test_validate_cessna_ok():
    ac = TestClient(app).get("/models/Cessna%20172").json()["aircraft"]
    r = TestClient(app).post("/models/validate", json={"aircraft": ac})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_validate_empty_aircraft_fails():
    r = TestClient(app).post("/models/validate", json={"aircraft": {}})
    assert r.status_code == 200
    assert r.json()["ok"] is False
    assert r.json()["error"]


def test_cors_allows_vite_ports():
    origin = "http://127.0.0.1:5175"
    r = TestClient(app).get("/models", headers={"Origin": origin})
    assert r.headers.get("access-control-allow-origin") == origin
