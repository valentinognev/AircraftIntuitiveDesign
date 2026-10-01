from fastapi.testclient import TestClient

from aid_web.app import app


def _cessna():
    return TestClient(app).get("/models/Cessna%20172").json()["aircraft"]


def test_control_derivatives_handbook_zero_and_five():
    client = TestClient(app)
    r = client.post(
        "/control-derivatives",
        json={"aircraft": _cessna(), "solver": "handbook", "deltas_deg": [0, 5]},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["solver"] == "handbook"
    assert body["deltas_deg"] == [0.0, 5.0]
    assert len(body["rows"]) == 8
    assert {row["surface"] for row in body["rows"]} == {"flap", "aileron", "elevator", "rudder"}


def test_unknown_solver_is_400():
    client = TestClient(app)
    r = client.post(
        "/control-derivatives",
        json={"aircraft": _cessna(), "solver": "panel"},
    )
    assert r.status_code == 400
    body = r.json()
    assert body["ok"] is False
    assert "error" in body


def test_control_report_passes_deltas_deg_to_heavy_solvers(monkeypatch):
    from aid.control_report import control_report

    seen = {}

    def capture(name):
        def fake(ac, deltas_deg=None, *args, **kwargs):
            seen[name] = (ac, deltas_deg, args, kwargs)
            return []

        return fake

    for name in ("datcom_controls", "tornado_controls", "avl_controls", "flow5_controls"):
        monkeypatch.setattr(f"aid.control_report.{name}", capture(name))

    ac = object()
    deltas = [1.0, 3.0]
    mesh = ("8", "4")

    datcom = control_report(ac, "datcom", deltas_deg=deltas)
    assert datcom["solver"] == "datcom"
    assert datcom["deltas_deg"] == [1.0, 3.0]
    assert datcom["rows"] == []
    assert seen["datcom_controls"][0] is ac
    assert seen["datcom_controls"][1] == deltas
    assert seen["datcom_controls"][2] == ()

    for solver, name in (
        ("tornado", "tornado_controls"),
        ("avl", "avl_controls"),
        ("flow5", "flow5_controls"),
    ):
        report = control_report(ac, solver, deltas_deg=deltas, mesh=mesh)
        assert report["solver"] == solver
        assert report["deltas_deg"] == [1.0, 3.0]
        assert report["rows"] == []
        assert seen[name][0] is ac
        assert seen[name][1] == deltas
        assert seen[name][2] == (mesh,)


def test_control_report_omitted_mesh_matches_api_default(monkeypatch):
    """The Controls menu calls control_report with no mesh. Panel solvers must
    receive the same tuples POST /control-derivatives applies from DEFAULT_MESH.
    Handbook and DATCOM stay mesh-free.
    """
    from aid.control_report import control_report
    from aid_web.analyze import DEFAULT_MESH

    seen = {}

    def capture(name):
        def fake(ac, deltas_deg=None, *args, **kwargs):
            seen[name] = (args, kwargs)
            return []

        return fake

    for name in (
        "handbook_controls",
        "datcom_controls",
        "tornado_controls",
        "avl_controls",
        "flow5_controls",
    ):
        monkeypatch.setattr(f"aid.control_report.{name}", capture(name))

    ac = object()
    for solver in ("tornado", "avl", "flow5"):
        control_report(ac, solver)
        assert seen[f"{solver}_controls"] == ((DEFAULT_MESH[solver],), {})

    control_report(ac, "handbook")
    assert seen["handbook_controls"] == ((), {})
    control_report(ac, "datcom")
    assert seen["datcom_controls"] == ((), {})


def test_control_report_unknown_solver_raises():
    from aid.control_report import control_report

    try:
        control_report(object(), "panel")
    except ValueError as exc:
        assert "unknown solver" in str(exc)
    else:
        raise AssertionError("expected ValueError")
