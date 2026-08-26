import math
from aid.atmosphere import atmosphere

def test_sea_level_isa():
    r = atmosphere(0.0)
    assert abs(r["T"] - 518.69) < 0.01
    assert abs(r["a"] - math.sqrt(1.4 * 1716 * r["T"])) < 0.1
    assert r["D"] > 0
