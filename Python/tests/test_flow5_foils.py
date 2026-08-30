from dataclasses import replace

import pytest
from aid.aircraft import load_jsonc
from aid.flow5_foils import foils_for_aircraft, naca_digits
from aid.paths import models_dir


def test_naca_digits_2412():
    assert naca_digits("2412") == 2412
    assert naca_digits("0009") == 9
    assert naca_digits("NACA-W-4-2412") == 2412

def test_naca_digits_rejects_empty():
    with pytest.raises(ValueError):
        naca_digits("Data.")


def test_cessna_foils_include_2412():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    foils = foils_for_aircraft(ac)
    digits = {f["naca"] for f in foils}
    assert 2412 in digits


def test_cessna_foils_unique_first_seen_order():
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    foils = foils_for_aircraft(ac)
    assert foils == [
        {"name": "NACA 2412", "naca": 2412},
        {"name": "NACA 12", "naca": 12},
    ]


def test_plot_cmp_skips_disabled_planforms():
    ac = replace(
        load_jsonc(models_dir() / "Cessna 172.jsonc"),
        plot_cmp=[1, 0, 0, 1],
    )
    foils = foils_for_aircraft(ac)
    assert foils == [{"name": "NACA 2412", "naca": 2412}]


def test_skips_invalid_naca():
    ac = replace(
        load_jsonc(models_dir() / "Cessna 172.jsonc"),
        HT={"NACA": "Data."},
        plot_cmp=[1, 1, 0, 0],
    )
    foils = foils_for_aircraft(ac)
    assert foils == [{"name": "NACA 2412", "naca": 2412}]


def test_short_plot_cmp_pads_enabled():
    ac = replace(
        load_jsonc(models_dir() / "Cessna 172.jsonc"),
        plot_cmp=[1],
    )
    foils = foils_for_aircraft(ac)
    assert {f["naca"] for f in foils} == {2412, 12}
