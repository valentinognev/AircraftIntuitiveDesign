# Python/tests/test_avl_merge_run_case.py
from pathlib import Path

from aid.avl_io import merge_avl_st


_ST = """
 Vortex Lattice Output -- Total Forces

 Run case:  Cessna

 Alpha =   4.00000     pb/2V =   0.00000     p'b/2V =   0.00000
 Beta  =   0.00000     qc/2V =   0.00000
 Mach  =     0.000     rb/2V =   0.00000     r'b/2V =   0.00000

 CXtot =   0.01000     Cltot =   0.00000     Cl'tot =   0.00000
 CYtot =   0.00000     Cmtot =  -0.05000     Cn'tot =   0.00000
 CZtot =  -0.50000     Cntot =   0.00000

 CLtot =   0.51000
 CDtot =   0.02500
 CDvis =   0.00000     CDind =   0.02000
 CLff  =   0.50000     CDff  =   0.01800    | Trefftz
 CYff  =   0.00000         e =   0.80000    | Plane


 Stability-axis derivatives...

  z' force CL   |  CLa =   5.200000   CLb =  -0.100000
  y  force CY   |  CYa =  -0.010000   CYb =  -0.400000
  x' mom.  Cl'  |  Cla =   0.000000   Clb =  -0.050000
  y  mom.  Cm   |  Cma =  -1.200000   Cmb =   0.000000
  z' mom.  Cn'  |  Cna =   0.010000   Cnb =   0.080000

 Neutral point  Xnp =   3.500000
"""


def test_merge_avl_st_keeps_derivatives_and_totals(tmp_path: Path):
    p = tmp_path / "geometry.st"
    p.write_text(_ST)
    got = merge_avl_st(p)
    assert abs(got["CLa"] - 5.2) < 1e-6
    assert abs(got["Cma"] + 1.2) < 1e-6
    assert abs(got["CLtot"] - 0.51) < 1e-6
    assert abs(got["CDtot"] - 0.025) < 1e-6
    assert abs(got["Cmtot"] + 0.05) < 1e-6
    assert abs(got["alpha"] - 4.0) < 1e-6
