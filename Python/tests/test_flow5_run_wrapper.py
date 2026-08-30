from aid.aircraft import load_jsonc
from aid.flow5_io import run_flow5, run_flow5_native, write_flow5_deck
from aid.paths import models_dir


def test_run_flow5_equals_native_on_same_deck():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    mesh = ("10", "10")
    deck = write_flow5_deck(ac, mesh)
    native = run_flow5_native(deck)
    wrapped = run_flow5(ac, mesh)
    assert native["CL"] == wrapped["CL"]
    assert native["CD"] == wrapped["CD"]
    assert native["Cm"] == wrapped["Cm"]
