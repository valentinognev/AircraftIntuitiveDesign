import pytest

from aid.aircraft import load_jsonc
from aid.avl_controls import rows_from_sb, write_avl_control_case, write_avl_control_geometry
from aid.paths import models_dir

_SB = """
 Geometry-axis derivatives...
 CXd1 = 0.01
 CYd1 = 0.0
 CZd1 = -1.8
 Cld1 = 0.0
 Cmd1 = -0.4
 Cnd1 = 0.0
 CXd2 = 0.0
 CYd2 = 0.0
 CZd2 = 0.0
 Cld2 = 0.5
 Cmd2 = 0.0
 Cnd2 = -0.1
"""

_NAMES = ("flap", "aileron", "elevator", "rudder")


def test_sb_fixture_maps_flap_and_aileron_per_degree():
    # Header parser needs surface names; rows_from_sb accepts an explicit order
    # when the fixture has no run-case header.
    rows = rows_from_sb(_SB, 5.0, names=("flap", "aileron", "elevator", "rudder"))
    flap = next(r for r in rows if r["surface"] == "flap")
    assert flap["delta_deg"] == 5.0
    assert flap["available"] is True
    ail = next(r for r in rows if r["surface"] == "aileron")
    assert ail["Cl"] == pytest.approx(0.5)
    rudder = next(r for r in rows if r["surface"] == "rudder")
    assert rudder["available"] is False


def test_alpha0_body_axis_lift_is_minus_cz_per_degree():
    rows = rows_from_sb(_SB, 5.0, names=_NAMES)
    flap = next(r for r in rows if r["surface"] == "flap")
    assert flap["CL"] == pytest.approx(-(-1.8))
    assert flap["CD"] == pytest.approx(-0.01)
    assert flap["Cm"] == pytest.approx(-0.4)
    assert flap["CY"] == pytest.approx(0.0)
    assert flap["Cl"] == pytest.approx(0.0)
    assert flap["Cn"] == pytest.approx(0.0)
    ail = next(r for r in rows if r["surface"] == "aileron")
    assert ail["Cl"] == pytest.approx(0.5)
    assert ail["Cn"] == pytest.approx(-0.1)
    elevator = next(r for r in rows if r["surface"] == "elevator")
    assert elevator["available"] is False
    rudder = next(r for r in rows if r["surface"] == "rudder")
    assert rudder["reason"] == "avl surface missing"
    assert rudder["CL"] is None


def test_cld_line_overrides_body_axis_cz():
    rows = rows_from_sb(_SB + "\n CLd1 = 2.0\n", 0.0, names=_NAMES)
    flap = next(r for r in rows if r["surface"] == "flap")
    assert flap["CL"] == pytest.approx(2.0)


def test_nonzero_alpha_without_cld_leaves_lift_and_drag_empty():
    rows = rows_from_sb("Alpha = 4.0\n" + _SB, 5.0, names=_NAMES)
    flap = next(r for r in rows if r["surface"] == "flap")
    assert flap["available"] is True
    assert flap["CL"] is None
    assert flap["CD"] is None
    assert flap["Cm"] == pytest.approx(-0.4)


def test_zero_stored_deflection_still_writes_control_cards(tmp_path):
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    stored = (
        ac.F["DELTA"],
        ac.A["DELTAL"],
        ac.A["DELTAR"],
        ac.E["DELTA"],
        ac.R["DELTA"],
    )
    write_avl_control_geometry(ac, tmp_path, ("4", "2"))
    text = (tmp_path / "geometry.avl").read_text()
    for token in ("flap", "aileron", "elevator", "rudder"):
        assert token in text
    aileron_lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("aileron")]
    assert aileron_lines
    assert all(ln.endswith("-1") for ln in aileron_lines)
    assert (
        ac.F["DELTA"],
        ac.A["DELTAL"],
        ac.A["DELTAR"],
        ac.E["DELTA"],
        ac.R["DELTA"],
    ) == stored


def test_control_case_names_each_defined_surface(tmp_path):
    write_avl_control_case(
        tmp_path,
        {"flap": 5.0, "aileron": 0.0, "elevator": 5.0, "rudder": 5.0},
    )
    text = (tmp_path / "geometry.run").read_text()
    assert "OPER\n" in text
    assert "D1 D1 5.0000 ! flap" in text
    assert "D2 D2 0.0000 ! aileron" in text
    assert "D3 D3 5.0000 ! elevator" in text
    assert "D4 D4 5.0000 ! rudder" in text
    assert "sb\ngeometry.sb\n" in text
