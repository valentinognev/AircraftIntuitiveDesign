"""DATCOM writer clamps: STMACH, SSPNE min, NDELTA max. Stored JSONC fields unchanged."""

from __future__ import annotations

import re

import numpy as np
import pytest

from aid.aircraft import load_jsonc
from aid.datcom_io import write_for005
from aid.paths import models_dir


def test_mach_0_8_writes_stmach_without_mutating_aero(tmp_path):
    ac = load_jsonc(models_dir() / "F-16.jsonc")
    stored = float(np.asarray(ac.AERO["MACH"]).reshape(-1)[0])
    assert stored == pytest.approx(0.8)
    p = tmp_path / "for005.dat"
    with pytest.warns(UserWarning, match="0.6"):
        write_for005(ac, p, unit=ac.unit)
    text = p.read_text()
    assert re.search(r"MACH=0\.600?,", text)
    assert "MACH=0.800" not in text
    assert float(np.asarray(ac.AERO["MACH"]).reshape(-1)[0]) == pytest.approx(0.8)


def test_negative_sspne_omits_illegal_ht_without_mutating(tmp_path):
    ac = load_jsonc(models_dir() / "Orbiter.jsonc")
    stored = float(ac.HT["SSPNE"])
    assert stored < 0
    p = tmp_path / "for005.dat"
    write_for005(ac, p, unit=ac.unit)
    text = p.read_text()
    assert "$HTPLNF" not in text
    assert "NACA-H" not in text
    assert "$WGPLNF" in text
    assert "$VTPLNF" in text
    assert float(ac.HT["SSPNE"]) == pytest.approx(stored)
    # illegal elevator SPANFO < SPANFI is omitted
    assert "SPANFO=1.000" not in text


def test_ndelta_capped_at_nine(tmp_path):
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    ac.F["DELTA"] = [float(i) for i in range(12)]
    ac.A["DELTAL"] = [float(i) for i in range(12)]
    ac.A["DELTAR"] = [-float(i) for i in range(12)]
    p = tmp_path / "for005.dat"
    write_for005(ac, p, unit=ac.unit)
    text = p.read_text()
    for block in text.split("$SYMFLP")[1:]:
        body = block.split("$", 1)[0]
        if "NDELTA=" not in body:
            continue
        n = float(re.search(r"NDELTA=([0-9.]+)", body).group(1))
        assert n <= 9.0
        deltas = re.findall(r"DELTA=([0-9.,\s-]+)", body)
        if deltas:
            vals = [v for v in deltas[0].replace("\n", "").split(",") if v.strip()]
            assert len(vals) <= 9
    asy = text.split("$ASYFLP", 1)[1].split("$", 1)[0]
    n = float(re.search(r"NDELTA=([0-9.]+)", asy).group(1))
    assert n <= 9.0
    left = re.search(r"DELTAL=([0-9.,\s-]+)", asy).group(1)
    assert len([v for v in left.replace("\n", "").split(",") if v.strip()]) <= 9


def test_t34c_avl_geometry_omits_propeller(tmp_path):
    from aid.avl_io import write_avl_geometry
    from aid.tornado_io import tornado_io

    ac = load_jsonc(models_dir() / "Beechcraft T-34C.jsonc")
    assert ac.NP[3] is not None
    geo, state = tornado_io(ac, ("10", "10"))
    assert int(geo["nwing"]) == 3
    write_avl_geometry(ac, geo, state, tmp_path, 10, 10)
    text = (tmp_path / "geometry.avl").read_text()
    assert text.count("SURFACE") == 3
    assert "Planform" not in text


def test_f16_datcom_finite_cl_at_clamped_mach(tmp_path):
    from aid.datcom_run import run_datcom
    from aid.paths import datcom_wrapper

    if not datcom_wrapper().is_file():
        pytest.skip("datcom wrapper not present")
    ac = load_jsonc(models_dir() / "F-16.jsonc")
    stored = float(np.asarray(ac.AERO["MACH"]).reshape(-1)[0])
    got = run_datcom(ac, tmp_path / "f16")
    assert np.all(np.isfinite(got["cl"]))
    assert len(got["cl"]) >= 3
    assert stored == pytest.approx(0.8)
    assert float(np.asarray(ac.AERO["MACH"]).reshape(-1)[0]) == pytest.approx(0.8)


def test_t34c_datcom_finite_cl_despite_plot_crash(tmp_path):
    from aid.datcom_run import run_datcom
    from aid.paths import datcom_wrapper

    if not datcom_wrapper().is_file():
        pytest.skip("datcom wrapper not present")
    ac = load_jsonc(models_dir() / "Beechcraft T-34C.jsonc")
    got = run_datcom(ac, tmp_path / "t34c")
    assert np.all(np.isfinite(got["cl"]))
    assert len(got["cl"]) >= 3


def test_box_naca_uses_numeric_card_not_data(tmp_path):
    ac = load_jsonc(models_dir() / "Box.jsonc")
    assert ac.WG["NACA"][0] == "Data."
    p = tmp_path / "for005.dat"
    write_for005(ac, p, unit=ac.unit)
    text = p.read_text()
    assert "NACA-W-4-2412" in text
    assert "NACA-W-5-Data" not in text
    assert "$WGSCHR" not in text
    assert "Data." not in text


def _body_block(text: str) -> str:
    start = text.index("$BODY")
    naca = text.index("NACA-", start)
    return text[start:naca]


def _long_lines(text: str):
    return [(i + 1, len(line), line) for i, line in enumerate(text.splitlines()) if len(line) > 80]


def test_orbiter_body_lines_wrap_at_80_columns(tmp_path):
    ac = load_jsonc(models_dir() / "Orbiter.jsonc")
    p = tmp_path / "for005.dat"
    write_for005(ac, p, unit=ac.unit)
    body = _body_block(p.read_text())
    long_lines = _long_lines(body)
    assert long_lines == [], f"BODY namelist lines exceed 80 cols: {long_lines}"
    assert "NX=11.0" in body
    x_vals = re.findall(r"-?\d+\.\d+", body.split("\n  X=", 1)[1].split("ZU=", 1)[0])
    assert len(x_vals) == 11


def test_body_not_downsampled_below_200(tmp_path):
    ac = load_jsonc(models_dir() / "DA20-C1.jsonc")
    assert int(ac.BD["NX"]) == 24
    p = tmp_path / "for005.dat"
    write_for005(ac, p, unit=ac.unit)
    body = _body_block(p.read_text())
    assert "NX=24.0" in body
    x_vals = re.findall(r"-?\d+\.\d+", body.split("\n  X=", 1)[1].split("ZU=", 1)[0])
    assert len(x_vals) == 24
    assert _long_lines(body) == []


def test_da20_writes_elevator_when_spanfo_exceeds_ht(tmp_path):
    """Write elevator $SYMFLP even when SPANFO > HT.SSPN; clamp SPANFO at write time.

    Unclamped SPANFO=4.7 crashes Digital DATCOM (SIGSEGV, no α table). Stored E unchanged.
    """
    ac = load_jsonc(models_dir() / "DA20-C1.jsonc")
    stored = float(ac.E["SPANFO"])
    ht_sspn = float(ac.HT["SSPN"])
    assert stored > ht_sspn
    assert stored > float(ac.E["SPANFI"])
    p = tmp_path / "for005.dat"
    write_for005(ac, p, unit=ac.unit)
    text = p.read_text()
    assert "$HTPLNF" in text
    assert "$VTPLNF" in text
    assert text.count("$SYMFLP") == 2
    assert "SPANFO=11.700" in text
    assert f"SPANFO={ht_sspn:.3f}" in text
    assert "SPANFO=4.700" not in text
    assert float(ac.E["SPANFO"]) == pytest.approx(stored)


def test_namelist_array_wraps_ten_per_line_like_matlab():
    from aid.datcom_io import format_wrapped_array

    vals = [0.0, 12.944, 44.888, 194.581, 318.573, 450.883, 497.968, 559.064, 559.064, 559.064, 559.064]
    text = format_wrapped_array("S", vals, "%.3f,")
    lines = text.splitlines()
    assert all(len(line) <= 80 for line in lines), [len(l) for l in lines]
    assert lines[0].startswith("  S=")
    first_n = lines[0].count(",")
    assert first_n <= 10
    assert sum(line.count(",") for line in lines) == 11
    assert lines[-1].startswith("  ")


def test_xwing_omits_buried_ht_and_vt(tmp_path):
    ac = load_jsonc(models_dir() / "X-Wing.jsonc")
    assert float(ac.HT["SSPNE"]) < 0
    assert float(ac.VT["SSPNE"]) < 0
    p = tmp_path / "for005.dat"
    write_for005(ac, p, unit=ac.unit)
    text = p.read_text()
    assert "$HTPLNF" not in text
    assert "$VTPLNF" not in text
    assert "$WGPLNF" in text
    assert float(ac.HT["SSPNE"]) < 0
    assert float(ac.VT["SSPNE"]) < 0


def test_orbiter_datcom_finite_cl(tmp_path):
    from aid.datcom_run import run_datcom
    from aid.paths import datcom_wrapper

    if not datcom_wrapper().is_file():
        pytest.skip("datcom wrapper not present")
    ac = load_jsonc(models_dir() / "Orbiter.jsonc")
    stored = float(ac.HT["SSPNE"])
    got = run_datcom(ac, tmp_path / "orbiter")
    assert np.all(np.isfinite(got["cl"]))
    assert len(got["cl"]) >= 3
    assert float(ac.HT["SSPNE"]) == pytest.approx(stored)


def test_t34c_avl_retries_spacing_and_returns_finite_cla(tmp_path):
    from aid.avl_io import run_avl_full
    from aid.paths import avl_bin

    if not avl_bin().is_file():
        pytest.skip("avl binary not present")
    ac = load_jsonc(models_dir() / "Beechcraft T-34C.jsonc")
    got = run_avl_full(ac, ("10", "10"), tmp_path / "t34c_avl")
    cla = got.get("CLa")
    assert cla is not None
    assert np.isfinite(float(np.asarray(cla).reshape(-1)[0]))
    assert (tmp_path / "t34c_avl" / "geometry.st").is_file()
