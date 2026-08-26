# Python/tests/test_tornado_isa.py
from aid.tornado.isa import isa_atmosphere

def test_isa_rho_positive():
    r = isa_atmosphere(0.0)
    assert r["rho"] > 0
