# Python/tests/test_mat_to_jsonc_all.py
from aid.paths import matlab_code, models_dir


def test_23_jsonc_models_exist():
    mats = list((matlab_code() / "Models").glob("*.mat"))
    jsonc = list(models_dir().glob("*.jsonc"))
    assert len(mats) == 23
    assert len(jsonc) == 23
    assert (models_dir() / "Cessna 172.jsonc").is_file()
