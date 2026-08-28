from aid.aircraft import load_jsonc
from aid.downwash import downwash
from aid.paths import models_dir


def test_cessna_downwash_eta():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    out = downwash(ac)
    assert 0 < out["eta"] <= 1
    assert out["dwash"] > 0
