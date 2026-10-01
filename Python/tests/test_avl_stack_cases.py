# Python/tests/test_avl_stack_cases.py
from pathlib import Path

from aid.avl_io import stack_avl_cases

_ST = """
 Run case:  wing

 Alpha =   {alpha:.5f}     pb/2V =   0.00000     p'b/2V =   0.00000
 Beta  =   0.00000     qc/2V =   0.00000
 Mach  =     0.000     rb/2V =   0.00000     r'b/2V =   0.00000

 CXtot =   {cx:.5f}     Cltot =   0.00000     Cl'tot =   0.00000
 CYtot =   0.00000     Cmtot =  {cm:.5f}     Cn'tot =   0.00000
 CZtot =  {cz:.5f}     Cntot =   0.00000

 CLtot =   {cl:.5f}
 CDtot =   {cd:.5f}
 CDvis =   0.00000     CDind =   {cdi:.5f}
 CLff  =   {cl:.5f}     CDff  =   0.01800    | Trefftz
 CYff  =   0.00000         e =   0.80000    | Plane


 Stability-axis derivatives...

  z' force CL   |  CLa =   {cla:.6f}   CLb =   0.000000
  y  force CY   |  CYa =   0.000000   CYb =  -0.400000
  x' mom.  Cl'  |  Cla =   0.000000   Clb =  -0.050000
  y  mom.  Cm   |  Cma =  -1.200000   Cmb =   0.000000
  z' mom.  Cn'  |  Cna =   0.000000   Cnb =   0.080000
  z' force CL   |  CLp =   0.010000   CLq =   8.000000   CLr =  -0.020000
  y  force CY   |  CYp =  -0.100000   CYq =  -0.200000   CYr =   0.300000
  x' mom.  Cl'  |  Clp =  -0.400000   Clq =  -0.010000   Clr =   0.040000
  y  mom.  Cm   |  Cmp =  -0.020000   Cmq = -15.000000   Cmr =   0.050000
  z' mom.  Cn'  |  Cnp =   0.030000   Cnq =   0.060000   Cnr =  -0.100000

 Neutral point  Xnp =   3.500000
"""


def _write(dirpath: Path, name: str, **kw) -> None:
    (dirpath / name).write_text(_ST.format(**kw))


def test_stack_avl_cases_keeps_each_solved_angle(tmp_path: Path):
    _write(tmp_path, "a0.st", alpha=-4, cx=0.01, cz=-0.2, cl=0.2, cd=0.01, cdi=0.008, cm=-0.02, cla=5.1)
    _write(tmp_path, "a1.st", alpha=0, cx=0.02, cz=-0.5, cl=0.5, cd=0.02, cdi=0.016, cm=-0.04, cla=5.2)
    got = stack_avl_cases([tmp_path / "a0.st", tmp_path / "a1.st"])
    assert got["alpha"] == [-4.0, 0.0]
    assert got["CLtot"] == [0.2, 0.5]
    assert got["CDtot"] == [0.01, 0.02]
    assert got["CZtot"] == [-0.2, -0.5]
    assert got["CXtot"] == [0.01, 0.02]
    assert got["CLa"] == [5.1, 5.2]
    assert got["NP"] == [3.5, 3.5]
    assert len(got["Cmtot"]) == 2
    assert got["surface"] == []


def test_stack_avl_cases_rejects_empty():
    try:
        stack_avl_cases([])
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("expected ValueError")
