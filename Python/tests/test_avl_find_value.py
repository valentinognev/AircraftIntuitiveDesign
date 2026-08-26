from aid.avl_parse import find_value

SAMPLE = [
    " Stability-axis derivatives...",
    " CLa =   4.5123  per rad",
    " Cma =  -0.8234  per rad",
]


def test_find_cla():
    v, ln = find_value(SAMPLE, "CLa")
    assert abs(v - 4.5123) < 1e-6
    assert ln == 1
