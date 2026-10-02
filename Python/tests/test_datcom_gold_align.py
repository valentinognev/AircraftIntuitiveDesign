# Python/tests/test_datcom_gold_align.py
"""``_compare_datcom`` against a gold swept on a coarser alpha schedule.

The MATLAB gold predates the 15-point default, so its ``alpha`` array is a
subset of the Python sweep. The comparison must sample the Python series at the
gold's alphas -- and must never let that sampling turn a mismatch into a pass.
"""

from aid.compare import _compare_datcom, _gold_alpha

# A fine Python sweep and the coarser gold flown on five of its points.
PY = {
    "alpha": [-4.0, -3.0, -2.0, -1.0, 0.0, 1.0],
    "cl": [-0.224, -0.134, -0.046, 0.042, 0.132, 0.224],
    "mach": 0.03,
}
GOLD = {"alpha": [-4.0, 0.0], "cl": [-0.224, 0.132], "mach": 0.03}


def test_coarse_gold_is_sampled_on_the_fine_python_sweep():
    assert _compare_datcom(PY, GOLD) is True


def test_wrong_value_at_a_shared_alpha_still_fails():
    gold = {**GOLD, "cl": [-0.224, 0.999]}
    assert _compare_datcom(PY, gold) is False


def test_gold_alpha_missing_from_the_python_sweep_fails():
    """Alignment must not silently drop a gold condition it cannot honour."""
    gold = {**GOLD, "alpha": [-4.0, 0.5], "cl": [-0.224, 0.132]}
    assert _compare_datcom(PY, gold) is False


def test_empty_gold_series_never_passes():
    """Comparing zero values would be a vacuous pass."""
    assert _compare_datcom(PY, {**GOLD, "cl": []}) is False


def test_empty_gold_alpha_axis_never_passes():
    assert _compare_datcom(PY, {**GOLD, "alpha": []}) is False


def test_unaligned_gold_without_an_alpha_axis_is_compared_as_is():
    """A gold with no alpha axis keeps the plain element-wise behaviour."""
    python = {"cl": [-0.2, 0.2]}
    assert _compare_datcom(python, {"cl": [-0.2, 0.2]}) is True
    assert _compare_datcom(python, {"cl": [-0.2, 0.9]}) is False


def test_missing_python_key_fails():
    assert _compare_datcom({"mach": 0.03}, GOLD) is False


def test_gold_alpha_read_from_the_gold_file(tmp_path):
    (tmp_path / "datcom.json").write_text('{"alpha": [-4, 0, 4]}')
    assert _gold_alpha(tmp_path) == [-4, 0, 4]


def test_gold_alpha_is_none_when_the_gold_records_no_sweep(tmp_path):
    assert _gold_alpha(tmp_path) is None
    (tmp_path / "datcom.json").write_text('{"cl": [1.0]}')
    assert _gold_alpha(tmp_path) is None