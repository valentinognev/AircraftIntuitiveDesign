"""``mat_to_jsonc.py`` must not undo the runtime alpha default.

The ``Matlab/fsroot/code/Models/*.mat`` sources still carry the original 5-7
point schedules, so the converter has to expand them the way a run does --
otherwise regenerating the models quietly takes every plot back to 6 points.
"""

import importlib.util
from pathlib import Path

from aid.aircraft import Aircraft, load_jsonc
from aid.alpha_schedule import ALPHA_POINTS, alpha_schedule

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SPARSE = [-4, 0, 4, 8, 12]


def _converter():
    spec = importlib.util.spec_from_file_location(
        "mat_to_jsonc", SCRIPTS / "mat_to_jsonc.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sparse_aircraft() -> Aircraft:
    return Aircraft(
        WG={}, HT={}, VT={}, F={}, A={}, E={}, R={}, BD={},
        NP=[], NB=[], AERO={"ALSCHD": list(SPARSE)}, plot_cmp=[], unit="ft",
    )


def test_converter_writes_the_default_schedule(monkeypatch, tmp_path):
    converter = _converter()
    models = tmp_path / "models"
    code = tmp_path / "code"
    (code / "Models").mkdir(parents=True)
    (code / "Models" / "Fake.mat").write_bytes(b"")
    monkeypatch.setattr(converter, "models_dir", lambda: models)
    monkeypatch.setattr(converter, "matlab_code", lambda: code)
    monkeypatch.setattr(converter, "load_mat", lambda path: _sparse_aircraft())

    converter.main()

    ac = load_jsonc(models / "Fake.jsonc")
    assert len(ac.AERO["ALSCHD"]) >= ALPHA_POINTS
    assert [float(a) for a in ac.AERO["ALSCHD"]] == alpha_schedule(ac)