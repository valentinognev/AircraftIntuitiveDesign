from dataclasses import replace

from fastapi.testclient import TestClient
from aid.aircraft import load_jsonc
from aid_web.app import aircraft_from_json, aircraft_to_json, app
from aid_web.paths import resolve_model

RESULTS = {
    "datcom": {
        "solver": "datcom",
        "payload": {"source": "datcom", "solver": "datcom", "axes": ["X", "Y", "Z"]},
        "raw": {
            "lattice": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
            "notes": {"alpha": 0.25, "flags": [True, False, None], "label": "a//b"},
        },
    },
    "avl": {
        "solver": "avl",
        "payload": {"source": "avl", "solver": "avl"},
        "raw": {"forces": {"CL": 0.5, "CD": 0.02}},
    },
}


def _cessna():
    return load_jsonc(resolve_model("Cessna 172"))


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


def test_get_model_omits_results_key():
    ac = TestClient(app).get("/models/Cessna%20172").json()["aircraft"]
    assert "results" not in ac


def test_aircraft_to_json_omits_absent_results():
    ac = _cessna()
    assert ac.results is None
    assert "results" not in aircraft_to_json(ac)


def test_aircraft_to_json_omits_empty_results():
    assert "results" not in aircraft_to_json(replace(_cessna(), results={}))


def test_aircraft_to_json_keeps_populated_results():
    data = aircraft_to_json(replace(_cessna(), results=RESULTS))
    assert data["results"] == RESULTS


def test_aircraft_from_json_absent_results_is_none():
    data = aircraft_to_json(replace(_cessna(), results=RESULTS))
    data.pop("results")
    assert aircraft_from_json(data).results is None


def test_aircraft_round_trip_preserves_results():
    ac = replace(_cessna(), results=RESULTS)
    assert aircraft_from_json(aircraft_to_json(ac)).results == RESULTS


def test_aircraft_from_json_keeps_results_verbatim():
    data = aircraft_to_json(replace(_cessna(), results=None))
    data["results"] = RESULTS
    assert aircraft_from_json(data).results == RESULTS


def test_validate_accepts_aircraft_with_results():
    ac = TestClient(app).get("/models/Cessna%20172").json()["aircraft"]
    ac["results"] = RESULTS
    r = TestClient(app).post("/models/validate", json={"aircraft": ac})
    assert r.json()["ok"] is True
