from fastapi.testclient import TestClient

from aid_web.app import app


def test_stability_cessna_has_keys():
    ac = TestClient(app).get("/models/Cessna%20172").json()["aircraft"]
    r = TestClient(app).post("/stability", json={"aircraft": ac})
    assert r.status_code == 200
    body = r.json()
    assert "x_cg" in body
    assert "Cm_CL" in body
    assert "summary" in body
    text = "\n".join(body["summary"])
    assert "CG at" in text
    assert "MAC" in text
