from aid.aircraft import load_jsonc
from aid.flow5_io import write_flow5_deck
from aid.paths import models_dir


def test_cessna_deck_t1_vlm2_inviscid():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    deck = write_flow5_deck(ac, ("10", "10"))
    assert deck["polar"]["type"] == "T1"
    assert deck["polar"]["method"] == "VLM2"
    assert deck["polar"]["thin"] is True
    assert deck["polar"]["viscous"] is False
    assert [float(a) for a in deck["polar"]["alpha_deg"]] == [
        float(a) for a in ac.AERO["ALSCHD"]
    ]
    roles = [w["role"] for w in deck["wings"]]
    assert "main" in roles
    assert "elevator" in roles
    assert "fin" in roles
    assert not any("fuse" in str(deck).lower() for _ in [0])
    fin = next(w for w in deck["wings"] if w["role"] == "fin")
    assert fin["rx_deg"] == -90.0
    assert fin["closed_inner"] is True
