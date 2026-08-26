from pathlib import Path

def repo_root() -> Path:
    p = Path(__file__).resolve()
    for cand in p.parents:
        if (cand / "Matlab" / "fsroot" / "code" / "AID.m").is_file():
            return cand
    raise FileNotFoundError("AircraftIntuitiveDesign root not found")

def matlab_code() -> Path:
    return repo_root() / "Matlab" / "fsroot" / "code"

def datcom_wrapper() -> Path:
    return matlab_code() / "DATCOM" / "datcom"

def avl_bin() -> Path:
    return matlab_code() / "AVL" / "run" / "avl"

def results_dir() -> Path:
    return repo_root() / "Results"

def models_dir() -> Path:
    return repo_root() / "Python" / "models"
