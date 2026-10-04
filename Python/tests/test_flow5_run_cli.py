import json
import subprocess
import tempfile
from pathlib import Path

from aid.aircraft import load_jsonc
from aid.flow5_io import write_flow5_deck
from aid.paths import flow5_bin, models_dir


def test_flow5_run_usage_exit_2():
    exe = flow5_bin()
    assert exe.is_file(), "build FLOW5/run/flow5_run"
    r = subprocess.run([str(exe)], capture_output=True, text=True)
    assert r.returncode == 2
    assert "usage" in r.stderr.lower()


def test_flow5_run_deck_skeleton_json_shape():
    """A deck with no native geometry returns the zero array shape -- and nothing else.

    Reachable from the product, not just from a hand-made deck: ``write_flow5_deck``
    emits empty ``foils``/``wings`` whenever ``plot_cmp`` disables every component,
    which is what ``deck_has_native_geometry`` tests.
    """
    exe = flow5_bin()
    assert exe.is_file(), "build FLOW5/run/flow5_run"
    deck = {"polar": {"alpha_deg": [-2.0, 0.0, 2.0]}}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(deck, f)
        deck_path = f.name
    try:
        r = subprocess.run(
            [str(exe), "--deck", deck_path],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert len(out["alpha"]) == 3
        assert len(out["CL"]) == 3
        assert len(out["CD"]) == 3
        assert len(out["Cm"]) == 3
        # Every derivative is OMITTED, never seeded to 0.0. Nothing was computed
        # here, and the real path treats a missing or non-finite derivative as a
        # hard failure precisely because a silent zero reads as a physical claim:
        # Cnb = 0.0 is "perfectly stable in yaw", indistinguishable at a glance
        # from a computed value. Same reasoning for the two OLS slopes, which are
        # fitted to the zero arrays above.
        for key in ("CLa", "Cma", "CXa", "CZa", "CYb", "CYp", "CYr",
                    "Clb", "Clp", "Clr", "Cnb", "Cnp", "Cnr", "XNP"):
            assert key not in out, f"{key} was emitted as a fabricated value"
    finally:
        Path(deck_path).unlink(missing_ok=True)


def test_flow5_run_skeleton_is_reachable_from_a_real_deck(tmp_path):
    """The skeleton path is not a curiosity: a plot_cmp-off model reaches it.

    Every shipped model has ``plot_cmp`` on, so this is the one way the zero
    skeleton gets into a real ``run_flow5`` result -- which is why it has to be
    honest about having computed nothing.
    """
    exe = flow5_bin()
    assert exe.is_file(), "build FLOW5/run/flow5_run"

    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    assert write_flow5_deck(ac, ("10", "10"))["wings"], "the shipped model has geometry"
    ac.plot_cmp = [0, 0, 0, 0, 0, 0]
    deck = write_flow5_deck(ac, ("10", "10"))
    assert not deck["foils"] and not deck["wings"], "plot_cmp-off must clear the geometry"

    path = tmp_path / "deck.json"
    path.write_text(json.dumps(deck))
    r = subprocess.run([str(exe), "--deck", str(path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert "Cnb" not in out, "a run that computed nothing must not report Cnb = 0.0"
