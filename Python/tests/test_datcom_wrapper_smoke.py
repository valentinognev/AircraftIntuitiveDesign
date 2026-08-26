import subprocess
from pathlib import Path
from aid.paths import matlab_code

SMOKE = """CASEID WRAPPER SMOKE
 $FLTCON NALPHA=3.0,ALSCHD=-2.0,0.0,2.0,
  NALT=1.0,ALT=0.0,
  NMACH=1.0,MACH=0.200,
  WT=1000.00,LOOP=2.0$
 $OPTINS SREF=100.00,CBARR=5.00,BLREF=20.00$
 $SYNTHS XCG=5.00,ZCG=0.00,XW=2.00,ZW=0.00,ALIW=0.00,
  XH=15.00,ZH=1.00,ALIH=0.00,XV=15.00,YV=0.00,ZV=0.00,VERTUP=.TRUE.$
 $BODY NX=3.0,ITYPE=1.0,
  X=0.00,5.00,20.00,
  R=0.50,1.00,0.20$
NACA-W-4-2412
 $WGPLNF CHRDR=5.00,CHRDBP=4.00,CHRDTP=2.50,SSPN=10.00,
  SSPNE=9.00,SSPNOP=0.00,SAVSI=0.00,SAVSO=0.00,CHSTAT=0.25,
  DHDADI=0.00,DHDADO=0.00,TWISTA=0.00,TYPE=1.0$
PLOT
NEXT CASE
"""

def test_datcom_wrapper_produces_for006():
    d = matlab_code() / "DATCOM"
    (d / "for005.dat").write_text(SMOKE)
    r = subprocess.run(["./datcom"], cwd=d, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    out = (d / "for006.dat").read_text()
    assert "CASEID" in out
    assert len(out) > 200
    assert "0 ALPHA     CD       CL" in out
