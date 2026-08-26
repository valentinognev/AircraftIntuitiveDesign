from pathlib import Path

from aid.paths import matlab_code


def test_models_decoded_and_count_23():
    d = matlab_code() / "Models"
    mats = list(d.glob("*.mat"))
    assert len(mats) == 23
    assert (d / "Cessna 172.mat").is_file()
    assert not any("%20" in p.name for p in mats)
