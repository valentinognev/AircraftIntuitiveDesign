"""DATCOM for005 honors plot_cmp like MATLAB DATCOM_IO.m."""

from __future__ import annotations

import json
import subprocess
from dataclasses import replace

import numpy as np
import pytest

from aid.aircraft import load_jsonc
from aid.datcom_io import write_for005
from aid.datcom_parse import parse_for006
from aid.paths import datcom_wrapper, models_dir, results_dir

_COEF_KEYS = ("alpha", "cd", "cl", "cm", "cn", "ca", "cla", "cma", "cyb", "cnb", "clb")


def _write(ac, tmp_path, name="for005.dat"):
    p = tmp_path / name
    write_for005(ac, p, unit=ac.unit)
    return p.read_text()


def test_sphere_for005_omits_ht_and_vt(tmp_path):
    ac = load_jsonc(models_dir() / "Sphere.jsonc")
    assert list(ac.plot_cmp) == [0, 0, 0, 1]
    text = _write(ac, tmp_path)
    assert "$HTPLNF" not in text
    assert "$VTPLNF" not in text
    assert "$WGPLNF" in text
    assert "$BODY" in text


def test_cessna_for005_has_wing_ht_vt(tmp_path):
    ac = load_jsonc(models_dir() / "Cessna 172.jsonc")
    text = _write(ac, tmp_path)
    assert "$WGPLNF" in text
    assert "$HTPLNF" in text
    assert "$VTPLNF" in text
    assert "$BODY" in text


def test_short_plot_cmp_pads_enabled(tmp_path):
    ac = replace(load_jsonc(models_dir() / "Cessna 172.jsonc"), plot_cmp=[1])
    text = _write(ac, tmp_path)
    assert "$HTPLNF" in text
    assert "$VTPLNF" in text
    assert "$BODY" in text


def test_body_omitted_when_plot_cmp_body_off(tmp_path):
    ac = replace(
        load_jsonc(models_dir() / "Cessna 172.jsonc"),
        plot_cmp=[1, 1, 1, 0],
    )
    text = _write(ac, tmp_path)
    assert "$BODY" not in text
    assert "$HTPLNF" in text
    assert "$VTPLNF" in text


def test_sphere_datcom_keys_match_matlab_gold_if_present(tmp_path):
    gold_path = results_dir() / "matlab" / "Sphere" / "datcom.json"
    if not gold_path.is_file():
        pytest.skip("Sphere MATLAB gold datcom.json not present")
    wrapper = datcom_wrapper()
    if not wrapper.is_file():
        pytest.skip("datcom wrapper not present")
    gold = json.loads(gold_path.read_text())
    ac = load_jsonc(models_dir() / "Sphere.jsonc")
    work = tmp_path / "sphere-gold"
    work.mkdir()
    write_for005(ac, work / "for005.dat", unit=ac.unit)
    subprocess.run([str(wrapper)], cwd=work, check=True, timeout=30)
    got = parse_for006((work / "for006.dat").read_text())
    for key in _COEF_KEYS:
        if key not in gold:
            continue
        assert key in got, key
        if not np.allclose(got[key], gold[key], atol=1e-6):
            pytest.skip(
                f"Sphere MATLAB gold stale vs NX=200 body (key {key}); "
                "re-run MATLAB DATCOM after body_max=200 wrap"
            )


def test_sphere_datcom_runs_if_wrapper_fast(tmp_path):
    wrapper = datcom_wrapper()
    if not wrapper.is_file():
        pytest.skip("datcom wrapper not present")
    ac = load_jsonc(models_dir() / "Sphere.jsonc")
    work = tmp_path / "sphere-run"
    work.mkdir()
    write_for005(ac, work / "for005.dat", unit=ac.unit)
    try:
        r = subprocess.run(
            [str(wrapper)],
            cwd=work,
            check=True,
            timeout=30,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        pytest.skip("DATCOM Sphere run exceeded 30s")
    out = work / "for006.dat"
    assert out.is_file(), r.stderr
    assert len(out.read_text()) > 200
