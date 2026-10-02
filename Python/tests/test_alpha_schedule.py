import math
from itertools import pairwise

import numpy as np
import pytest

from aid.aircraft import Aircraft
from aid.alpha_schedule import ALPHA_POINTS, alpha_schedule, apply_alpha_default


def _craft(alschd) -> Aircraft:
    return Aircraft(
        WG={},
        HT={},
        VT={},
        F={},
        A={},
        E={},
        R={},
        BD={},
        NP=[],
        NB=[],
        AERO={"ALSCHD": alschd},
        plot_cmp=[],
        unit="ft",
    )


def _step(sched: list[float]) -> float:
    return round(sched[1] - sched[0], 9)


@pytest.mark.parametrize("span", [4, 16, 20, 28, 40])
def test_span_fills_to_target_on_round_step(span):
    sched = alpha_schedule(_craft([0.0, span]))
    assert abs(len(sched) - ALPHA_POINTS) <= 6
    steps = {round(b - a, 9) for a, b in pairwise(sched)}
    assert steps == {_step(sched)}
    assert _step(sched) in (0.05, 0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)


@pytest.mark.parametrize("span", [16, 28, 5.3, 20.7])
def test_endpoints_preserved(span):
    sched = alpha_schedule(_craft([-span, span]))
    assert sched[0] == pytest.approx(-span)
    assert sched[-1] == pytest.approx(span)
    assert all(b > a for a, b in pairwise(sched))


def test_tie_between_ladder_steps_prefers_finer_step():
    sched = alpha_schedule(_craft([-4, 36]))
    assert _step(sched) == 2.0
    assert len(sched) == 21


@pytest.mark.parametrize(
    ("alschd", "expected"),
    [(0, [0.0]), ([3.5], [3.5]), ((-2.0,), [-2.0]), ([2.0, 2.0], [2.0]),
     (np.array(3.0), [3.0])],
)
def test_degenerate_input_kept(alschd, expected):
    assert alpha_schedule(_craft(alschd)) == expected


@pytest.mark.parametrize("alschd", [None, [], np.array([])])
def test_empty_input_yields_empty_schedule(alschd):
    assert alpha_schedule(_craft(alschd)) == []


def test_dense_input_returned_verbatim():
    given = [-4.0, -1.3, 0.0, 2.7, 5.5, 7.1, 9.9, 11.3, 13.0, 15.7,
             17.2, 19.9, 21.4, 23.8, 26.0]
    assert alpha_schedule(_craft(given)) == given


def test_target_override_thresholds_on_count():
    given = [0.0, 5.0, 10.0, 15.0, 20.0]
    assert alpha_schedule(_craft(given), target=5) == given
    assert len(alpha_schedule(_craft(given), target=15)) == 11


def test_apply_alpha_default_writes_schedule_and_returns_aircraft():
    ac = _craft([-4, 0, 4, 8, 12, 16])
    out = apply_alpha_default(ac)
    assert out is ac
    assert ac.AERO["ALSCHD"] == [-4.0, -2.0, 0.0, 2.0, 4.0, 6.0, 8.0,
                                  10.0, 12.0, 14.0, 16.0]
    assert ac.AERO["ALSCHD"] == alpha_schedule(ac)


def test_non_finite_entries_ignored():
    sched = alpha_schedule(_craft([0.0, math.nan, 4.0]))
    assert all(math.isfinite(a) for a in sched)
    assert sched[0] == 0.0
    assert sched[-1] == pytest.approx(4.0)


def test_column_shaped_array_matches_flat_list():
    flat = alpha_schedule(_craft([-4.0, 0.0, 4.0, 8.0, 12.0, 16.0]))
    column = alpha_schedule(_craft(np.array([[-4.0], [0.0], [4.0], [8.0], [12.0], [16.0]])))
    assert column == flat


def test_apply_alpha_default_is_idempotent():
    ac = _craft([-4, 0, 4, 8, 12, 16])
    apply_alpha_default(ac)
    first = list(ac.AERO["ALSCHD"])
    apply_alpha_default(ac)
    assert ac.AERO["ALSCHD"] == first


def test_apply_alpha_default_stores_plain_floats_from_numpy_input():
    ac = _craft(np.array([-4.0, 0.0, 4.0, 8.0, 12.0, 16.0]))
    apply_alpha_default(ac)
    assert all(type(a) is float for a in ac.AERO["ALSCHD"])