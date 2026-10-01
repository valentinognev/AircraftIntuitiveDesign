from aid.aircraft import Aircraft, load_jsonc
from aid.control_deriv import COEFFS
from aid.datcom_controls import datcom_controls
from aid.datcom_io import write_controls
from aid.paths import models_dir


def _ac() -> Aircraft:
    z = {"SPANFI": 1.0, "SPANFO": 3.0, "CHRDFI": 0.4, "CHRDFO": 0.3, "DELTA": 0.0,
         "FTYPE": 1.0, "PHETE": 0.0, "PHETEP": 0.0, "TC": 0.12, "CB": 0.5}
    a = {"SPANFI": 3.0, "SPANFO": 4.0, "CHRDFI": 0.3, "CHRDFO": 0.2, "DELTAL": 0.0, "DELTAR": 0.0, "STYPE": 1.0}
    return Aircraft(
        WG={"SSPN": 5.0}, HT={"SSPN": 2.0}, VT={"SSPN": 2.0},
        F=dict(z), A=dict(a), E=dict(z), R=dict(z),
        BD={}, NP=[], NB=[], AERO={"ALSCHD": [0.0]}, plot_cmp=[1, 1, 1, 1], unit="ft",
    )


def test_datcom_differences_a_fake_run_and_skips_rudder():
    seen = []

    def fake_run(ac):
        seen.append(("flap", float(ac.F["DELTA"]), "ail", float(ac.A["DELTAR"])))
        cl = 0.1 + 0.02 * float(ac.F["DELTA"])
        return {"alpha": [0.0], "CL": [cl], "CD": [0.02], "Cm": [-0.01 * float(ac.F["DELTA"])]}

    ac = _ac()
    rows = datcom_controls(ac, [5.0], run=fake_run)
    flap = next(r for r in rows if r["surface"] == "flap")
    assert abs(flap["CL"] - 0.02) < 1e-9
    assert flap["Cm"] is not None
    rudder = next(r for r in rows if r["surface"] == "rudder")
    assert rudder["available"] is False
    assert rudder["reason"] == "datcom has no rudder namelist"
    assert ac.F["DELTA"] == 0.0
    assert any(abs(delta - 6.0) < 1e-9 for _, delta, _, _ in seen)
    assert any(abs(delta - 4.0) < 1e-9 for _, delta, _, _ in seen)


def test_illegal_flap_span_is_unavailable_and_other_rows_remain():
    ac = _ac()
    ac.F["SPANFO"] = float(ac.F["SPANFI"])

    def fake_run(probed):
        if float(probed.F["DELTA"]) != 0.0:
            raise AssertionError("ran illegal flap")
        return {"alpha": [0.0], "CL": [0.1], "CD": [0.02], "Cm": [0.0]}

    rows = datcom_controls(ac, [5.0], run=fake_run)
    flap = next(r for r in rows if r["surface"] == "flap")
    assert flap["available"] is False
    assert all(flap[name] is None for name in COEFFS)
    assert next(r for r in rows if r["surface"] == "aileron")["available"] is True
    assert next(r for r in rows if r["surface"] == "elevator")["available"] is True


def test_controls_section_present_or_empty():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    lines = []
    write_controls(ac, lines)
    text = "\n".join(lines)
    # Cessna may have zero deflection; writer must not crash
    assert "PLOT" not in text  # controls only task
