# Python/scripts/mat_to_jsonc.py
from pathlib import Path
from aid.aircraft import load_mat, save_jsonc
from aid.paths import matlab_code, models_dir

def main():
    models_dir().mkdir(parents=True, exist_ok=True)
    for mat in sorted((matlab_code() / "Models").glob("*.mat")):
        ac = load_mat(mat)
        save_jsonc(ac, models_dir() / (mat.stem + ".jsonc"))

if __name__ == "__main__":
    main()
