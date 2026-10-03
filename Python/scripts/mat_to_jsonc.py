# Python/scripts/mat_to_jsonc.py
from pathlib import Path
from aid.alpha_schedule import apply_alpha_default
from aid.aircraft import load_mat, save_jsonc
from aid.paths import matlab_code, models_dir

def main():
    models_dir().mkdir(parents=True, exist_ok=True)
    for mat in sorted((matlab_code() / "Models").glob("*.mat")):
        ac = load_mat(mat)
        # The .mat sources keep the original 5-7 point schedules; expand them
        # the way a run does, or the files fall behind the runtime default.
        apply_alpha_default(ac)
        save_jsonc(ac, models_dir() / (mat.stem + ".jsonc"))

if __name__ == "__main__":
    main()
