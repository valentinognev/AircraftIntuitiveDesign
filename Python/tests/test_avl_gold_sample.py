from aid.compare import _compare_avl


def test_gold_scalar_uses_zero_alpha_sample():
    python = {"alpha": [-4.0, 0.0, 4.0], "CLa": [5.0, 5.057308, 5.2], "CLtot": [0.1, 0.4, 0.8]}
    gold = {"CLa": 5.057308}
    assert _compare_avl(python, gold) is True


def test_gold_scalar_does_not_use_another_angle():
    python = {"alpha": [2.0, 4.0], "CLa": [5.057308, 5.2]}
    gold = {"CLa": 5.057308}
    assert _compare_avl(python, gold) is False
