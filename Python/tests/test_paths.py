from aid.paths import avl_bin, datcom_wrapper, matlab_code, models_dir, repo_root, results_dir


def test_paths_resolve():
    assert (matlab_code() / "AID.m").is_file()
    assert datcom_wrapper().name == "datcom"
    assert avl_bin().name == "avl"
    assert repo_root().name == "AircraftIntuitiveDesign"
    assert results_dir().name == "Results"
    assert models_dir().name == "models"
