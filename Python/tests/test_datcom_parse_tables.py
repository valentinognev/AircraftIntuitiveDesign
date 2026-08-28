# Python/tests/test_datcom_parse_tables.py
import math

import numpy as np
import pytest

from aid.datcom_parse import parse_for006

# Excerpt of a typical AID DATCOM for006: section defs, stability, downwash, high-lift.
_FOR006 = """
1                             AUTOMATED STABILITY AND CONTROL METHODS PER APRIL 1976 VERSION OF DATCOM
                                                        WING SECTION DEFINITION
0                                 IDEAL ANGLE OF ATTACK =   0.25757 DEG.
                              ZERO LIFT ANGLE OF ATTACK =  -1.87966 DEG.
                                 IDEAL LIFT COEFFICIENT =   0.25602
                  ZERO LIFT PITCHING MOMENT COEFFICIENT =  -0.05087
                             MACH ZERO LIFT-CURVE-SLOPE =   0.09617 /DEG.
                                    LEADING EDGE RADIUS =   0.01587 FRACTION CHORD
                              MAXIMUM AIRFOIL THICKNESS =   0.12000 FRACTION CHORD
                                                DELTA-Y =   3.16898 PERCENT CHORD
0                         MACH= 0.0300 LIFT-CURVE-SLOPE =   0.09622 /DEG.      XAC =   0.25810
1                             AUTOMATED STABILITY AND CONTROL METHODS PER APRIL 1976 VERSION OF DATCOM
                                                   HORIZONTAL TAIL SECTION DEFINITION
0                                 IDEAL ANGLE OF ATTACK =   0.00000 DEG.
                              ZERO LIFT ANGLE OF ATTACK =   0.00000 DEG.
                                 IDEAL LIFT COEFFICIENT =   0.00000
                  ZERO LIFT PITCHING MOMENT COEFFICIENT =   0.00000
                             MACH ZERO LIFT-CURVE-SLOPE =   0.09596 /DEG.
                                    LEADING EDGE RADIUS =   0.01587 FRACTION CHORD
                              MAXIMUM AIRFOIL THICKNESS =   0.12000 FRACTION CHORD
                                                DELTA-Y =   3.16898 PERCENT CHORD
0                         MACH= 0.0300 LIFT-CURVE-SLOPE =   0.09604 /DEG.      XAC =   0.25870
  MACH    ALTITUDE   VELOCITY
0 0.030       0.00      33.49
0 ALPHA     CD       CL       CM       CN       CA       XCP        CLA          CMA          CYB          CNB          CLB
0
   -4.0    0.028   -0.225    0.1059  -0.227    0.012   -0.467    8.555E-02   -1.236E-02   -1.207E-02    7.950E-04   -1.579E-03
    0.0    0.024    0.131    0.0472   0.131    0.024    0.360    9.269E-02   -1.351E-02                             -1.988E-03
    4.0    0.037    0.516   -0.0022   0.518    0.001   -0.004    1.003E-01   -1.431E-02                             -2.436E-03
    8.0    0.070    0.934   -0.0672   0.934   -0.060   -0.072    1.084E-01   -1.920E-02                             -2.933E-03
   12.0    0.128    1.383   -0.1558   1.380   -0.163   -0.113    1.164E-01   -2.508E-02                             -3.471E-03
0                                    ALPHA     Q/QINF    EPSLON  D(EPSLON)/D(ALPHA)
0
                                     -4.0      1.000     -1.029        0.482
                                      0.0      1.000      0.901        0.474
                                      4.0      1.000      2.763        0.453
                                      8.0      1.000      4.523        0.418
                                     12.0      1.000      6.104        0.395
1                            AUTOMATED STABILITY AND CONTROL METHODS PER APRIL 1976 VERSION OF DATCOM
                                         CHARACTERISTICS OF HIGH LIFT AND CONTROL DEVICES
                                            TAIL PLAIN TRAILING-EDGE FLAP CONFIGURATION
0     DELTA     D(CL)     D(CM)    D(CL MAX)    D(CD MIN)                (CLA)D     (CH)A       (CH)D
        0.0     0.000    -0.0002     0.000      0.00000                  NDM       2.820E-03  -4.579E-03
0            --------- INDUCED DRAG COEFFICIENT INCREMENT , D(CDI) , DUE TO DEFLECTION ---------
0       DELTA =   0.0
   ALPHA
    -4.0       -6.69E-07
     0.0        6.04E-07
     4.0        1.92E-06
     8.0        3.29E-06
    12.0        4.78E-06
"""


def test_parse_exports_xcp_and_downwash():
    got = parse_for006(_FOR006)
    assert np.allclose(got["xcp"], [-0.467, 0.360, -0.004, -0.072, -0.113])
    assert np.allclose(got["q_qinf"], [1.0, 1.0, 1.0, 1.0, 1.0])
    assert np.allclose(got["epslon"], [-1.029, 0.901, 2.763, 4.523, 6.104])
    assert np.allclose(got["depsda"], [0.482, 0.474, 0.453, 0.418, 0.395])
    assert np.allclose(got["alpha"], [-4.0, 0.0, 4.0, 8.0, 12.0])


def test_parse_high_lift_increments_and_dcdi():
    got = parse_for006(_FOR006)
    hl = got["high_lift"]
    assert len(hl) == 1
    block = hl[0]
    assert "TAIL" in block["config"].upper()
    assert block["delta"] == pytest.approx(0.0)
    assert block["dcl"] == pytest.approx(0.0)
    assert block["dcm"] == pytest.approx(-0.0002)
    assert math.isnan(block["clad"])
    assert block["cha"] == pytest.approx(2.820e-3)
    assert np.allclose(block["dcdi_alpha"], [-4.0, 0.0, 4.0, 8.0, 12.0])
    assert block["dcdi"][-1] == pytest.approx(4.78e-6, rel=1e-3)


def test_parse_section_definitions():
    got = parse_for006(_FOR006)
    wing = got["sections"]["wing"]
    assert wing["alpha_ideal"] == pytest.approx(0.25757)
    assert wing["alpha_zl"] == pytest.approx(-1.87966)
    assert wing["cl_ideal"] == pytest.approx(0.25602)
    assert wing["cm0"] == pytest.approx(-0.05087)
    assert wing["xac"] == pytest.approx(0.25810)
    ht = got["sections"]["ht"]
    assert ht["alpha_ideal"] == pytest.approx(0.0)
    assert ht["xac"] == pytest.approx(0.25870)
