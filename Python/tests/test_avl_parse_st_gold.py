import json
from aid.avl_parse import parse_st
from aid.paths import results_dir


def test_parse_st_matches_matlab_json():
    stfile = results_dir() / "matlab" / "Cessna 172" / "geometry.st"
    gold = json.loads((results_dir() / "matlab" / "Cessna 172" / "avl.json").read_text())
    got = parse_st(stfile)
    assert abs(got["CLa"] - gold["CLa"]) < 1e-6
    assert abs(got["Cma"] - gold["Cma"]) < 1e-6
