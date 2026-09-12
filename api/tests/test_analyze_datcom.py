import subprocess

import pytest
from fastapi.testclient import TestClient

from aid.paths import datcom_wrapper
from aid_web.analyze import mapper_shaped_raw, payload_from_aid_raw, to_handshake_payload
from aid_web.app import app

RAW_FIXTURE = {
    "alpha": [-2.0, 0.0, 4.0],
    "CL": [0.0, 0.2, 0.6],
    "CD": [0.02, 0.02, 0.04],
    "Cm": [0.0, -0.01, -0.03],
}

WANT_PAYLOAD = {
    "source": "aid",
    "solver": "datcom",
    "axes": {"mach": [0.2], "alpha": [-2.0, 0.0, 4.0], "beta": [0]},
    "tables": {
        "cl": [[0.0, 0.2, 0.6]],
        "cd": [[0.02, 0.02, 0.04]],
        "cm": [[0.0, -0.01, -0.03]],
    },
    "ref": {},
}


def test_to_handshake_payload():
    payload = to_handshake_payload(RAW_FIXTURE, 0.2)
    assert payload == WANT_PAYLOAD
    assert payload_from_aid_raw(RAW_FIXTURE, 0.2) == payload


def test_mapper_shaped_raw_nulls_nonfinite():
    raw = mapper_shaped_raw(
        {
            "alpha": [0.0],
            "cl": [0.2],
            "cd": [0.02],
            "cm": [0.0],
            "mach": 0.3,
            "high_lift": [{"clad": float("nan")}],
        }
    )
    assert raw["high_lift"][0]["clad"] is None
    assert raw["CL"] == [0.2]
    assert raw["MACH"] == [0.3]


def _cessna():
    return TestClient(app).get("/models/Cessna%20172").json()["aircraft"]


def test_analyze_maps_datcom_raw_to_mapper_keys(monkeypatch):
    stub = {
        "alpha": [-4.0, 0.0, 4.0],
        "cl": [0.1, 0.3, 0.5],
        "cd": [0.02, 0.03, 0.04],
        "cm": [0.01, 0.0, -0.02],
        "mach": 0.03,
    }
    monkeypatch.setattr("aid_web.analyze.run_datcom", lambda _ac, _workdir: stub)
    r = TestClient(app).post("/analyze", json={"aircraft": _cessna()})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["solver"] == "datcom"
    raw = body["raw"]
    assert raw["alpha"] == [-4.0, 0.0, 4.0]
    assert raw["CL"] == [0.1, 0.3, 0.5]
    assert raw["CD"] == [0.02, 0.03, 0.04]
    assert raw["Cm"] == [0.01, 0.0, -0.02]
    assert raw["MACH"] == [0.03]
    assert raw["cl"] == [0.1, 0.3, 0.5]
    payload = body["payload"]
    assert payload["source"] == "aid"
    assert payload["solver"] == "datcom"
    assert payload["axes"] == {"mach": [0.03], "alpha": [-4.0, 0.0, 4.0], "beta": [0]}
    assert payload["tables"]["cl"] == [[0.1, 0.3, 0.5]]
    assert payload["tables"]["cd"] == [[0.02, 0.03, 0.04]]
    assert payload["tables"]["cm"] == [[0.01, 0.0, -0.02]]
    assert payload["ref"] == {}


def test_analyze_file_not_found_is_400(monkeypatch):
    def boom(_ac, _workdir):
        raise FileNotFoundError("missing datcom")

    monkeypatch.setattr("aid_web.analyze.run_datcom", boom)
    r = TestClient(app).post("/analyze", json={"aircraft": _cessna()})
    assert r.status_code == 400
    assert r.json() == {"ok": False, "error": "missing datcom"}


def test_analyze_called_process_error_is_400(monkeypatch):
    exc = subprocess.CalledProcessError(1, ["datcom"])

    def boom(_ac, _workdir):
        raise exc

    monkeypatch.setattr("aid_web.analyze.run_datcom", boom)
    r = TestClient(app).post("/analyze", json={"aircraft": _cessna()})
    assert r.status_code == 400
    assert r.json() == {"ok": False, "error": str(exc)}


@pytest.mark.skipif(
    not (
        datcom_wrapper().is_file()
        and (datcom_wrapper().parent / "datcom.bin").is_file()
    ),
    reason="no datcom",
)
def test_analyze_cessna_live():
    r = TestClient(app).post("/analyze", json={"aircraft": _cessna()})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["solver"] == "datcom"
    raw = body["raw"]
    for key in ("alpha", "CL", "CD", "Cm", "MACH"):
        assert isinstance(raw[key], list)
        assert raw[key]
    assert len(raw["CL"]) == len(raw["alpha"])
    assert len(raw["CD"]) == len(raw["alpha"])
    assert len(raw["Cm"]) == len(raw["alpha"])
    payload = body["payload"]
    assert payload["source"] == "aid"
    assert payload["solver"] == "datcom"
    assert payload["axes"]["beta"] == [0]
    assert payload["tables"]["cl"] == [raw["CL"]]
    assert payload["tables"]["cd"] == [raw["CD"]]
    assert payload["tables"]["cm"] == [raw["Cm"]]
    assert payload["ref"] == {}
