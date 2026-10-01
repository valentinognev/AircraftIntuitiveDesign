from aid.aircraft import Aircraft
from aid.flow5_controls import flow5_controls


def _ac() -> Aircraft:
    wing = {
        "CHRDR": 2.0, "CHRDTP": 1.0, "SSPN": 5.0, "SSPNOP": 0.0,
        "SAVSI": 0.0, "SAVSO": 0.0, "CHSTAT": 0.25, "DHDADI": 0.0, "DHDADO": 0.0,
        "TWISTA": 0.0, "SSPNE": 5.0, "X": 0.0, "Y": 0.0, "Z": 0.0, "i": 0.0,
        "NACA": ["0012"], "S": [20.0],
    }
    tail = dict(wing)
    tail["SSPN"] = 2.0
    z = {"SPANFI": 0.5, "SPANFO": 2.0, "CHRDFI": 0.4, "CHRDFO": 0.4, "DELTA": 0.0}
    a = {"SPANFI": 3.0, "SPANFO": 4.5, "CHRDFI": 0.3, "CHRDFO": 0.25, "DELTAL": 0.0, "DELTAR": 0.0}
    return Aircraft(
        WG=wing, HT=dict(tail), VT=dict(tail), F=dict(z), A=dict(a), E=dict(z), R=dict(z),
        BD={}, NP=[], NB=[], AERO={"ALSCHD": [0.0], "SREF": 20.0, "CBARR": 1.5, "BLREF": 10.0,
                                    "XCG": 0.4, "ZCG": 0.0, "WT": 1000.0, "MACH": [0.1], "ALT": [0.0]},
        plot_cmp=[1, 1, 1, 1], unit="ft",
    )


def test_flow5_probe_difference_and_antisym_aileron():
    decks = []

    def fake_run(deck):
        decks.append(deck)
        wing = next(w for w in deck["wings"] if w["name"] == "Wing")
        flaps = [s for s in wing["sections"] if "te_flap_deg" in s]
        angle = flaps[0]["te_flap_deg"] if flaps else 0.0
        antisym = bool(flaps and flaps[0].get("te_flap_antisym"))
        return {
            "alpha": [0.0],
            "CL": [0.2 + (0.0 if antisym else 0.01 * angle)],
            "CD": [0.02],
            "Cm": [0.0],
            "Cl": [0.002 * angle if antisym else 0.0],
            "Cn": [0.0],
            "CY": [0.0],
        }

    ac = _ac()
    rows = flow5_controls(ac, [5.0], mesh=("4", "2"), run=fake_run)
    flap = next(r for r in rows if r["surface"] == "flap")
    assert abs(flap["CL"] - 0.01) < 1e-9
    ail = next(r for r in rows if r["surface"] == "aileron")
    assert any(s.get("te_flap_antisym") is True for d in decks for w in d["wings"] for s in w["sections"])
    assert ail["Cl"] is not None
    assert ac.F["DELTA"] == 0.0
