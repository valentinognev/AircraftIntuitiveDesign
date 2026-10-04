"""``_compare_coeffs`` grades F-R-D Python output against raw MATLAB gold.

``Results/python/<name>/*.json`` is Forward-Right-Down and stays that way; the
re-rawing happens in memory inside ``_compare_coeffs``, so these tests read the
on-disk gold directly and never call ``compare_to_matlab`` (which is what writes
``Results/compare/<name>.json`` and therefore needs ``isolated_results``).
"""

import json

import numpy as np
import pytest

from aid.axes import from_frd
from aid.compare import _compare_coeffs
from aid.paths import results_dir

GOLD_ROOT = results_dir() / "matlab"
_AIRCRAFT = "Cessna 172"


def _gold(solver: str) -> dict:
    path = GOLD_ROOT / _AIRCRAFT / f"{solver}.json"
    if not path.is_file():
        pytest.skip(f"missing MATLAB gold {path}")
    return json.loads(path.read_text())


def _to_raw_space(solver: str, data: dict) -> dict:
    """What ``compare_to_matlab`` hands ``_compare_coeffs``: F-R-D, not raw."""
    return from_frd(solver, data)


def test_compare_datcom_accepts_normalized_python():
    gold = _gold("datcom")
    normalized = {
        k: (np.asarray(v) * -1 if k in ("ca", "cn") else v) for k, v in gold.items()
    }
    assert _compare_coeffs("datcom", normalized, gold) is True


def test_compare_datcom_rejects_a_double_flip():
    gold = _gold("datcom")
    assert _compare_coeffs("datcom", gold, gold) is False


def test_compare_tornado_and_avl_still_pass_against_gold():
    for solver in ("tornado", "avl"):
        gold = _gold(solver)
        python_result = _to_raw_space(solver, gold)
        assert _compare_coeffs(solver, python_result, gold) is True


def test_unknown_solver_still_raises():
    with pytest.raises(ValueError):
        _compare_coeffs("vlm2", {}, {})