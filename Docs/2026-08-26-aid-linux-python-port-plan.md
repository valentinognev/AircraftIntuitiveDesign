# AID Linux MATLAB + Python GUI Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Implementer model:** Composer 2.5 (`composer-2.5`). **Never** Composer 2.5 Fast. **Reviewer model:** Grok (`cursor-grok-4.6-high`). Implementer must not spawn reviewers.

**Goal:** Run AID’s DATCOM, Tornado, and AVL 3.52 on Linux for all 23 bundled aircraft, dump `Results/matlab/`, then ship a PySide6 twin under `Python/` whose coefficients match that oracle.

**Architecture:** Shared native DATCOM/AVL binaries; Tornado ported to Python; MATLAB AVL writers/parsers ported; GUI and comparison both call `aid/`. Aircraft in Python are JSONC with a comment on every variable.

**Tech Stack:** MATLAB R2025b (`/home/valentin/ProgramFiles/MB2025b/bin/matlab`), gfortran, AVL 3.52, Python 3.11+, PySide6, numpy, scipy, pytest.

**Spec:** `Docs/2026-08-26-aid-linux-python-port-spec.md`

## Global Constraints

- MATLAB binary is `/home/valentin/ProgramFiles/MB2025b/bin/matlab` (R2025b). Aerospace Toolbox `datcomimport` is required for Phase 1 gold DATCOM dumps.
- DATCOM Fortran source is `/home/valentin/Projects/MDT/USAF_DATCOM/datcom/datcom.f`. The PDAS binary reads the input **filename from stdin** and writes **`datcom.out`**, not `for006.dat`. A wrapper must feed `for005.dat` and copy `datcom.out` → `for006.dat`.
- AVL source is `Matlab/fsroot/code/AVL/AVL3.52rel09032025/`. Build plotlib → eispack → `bin/Makefile.gfortranDP`. Install as `Matlab/fsroot/code/AVL/run/avl`.
- Do not invent a new AVL geometry format. Port `Tornado_IO.m`, `AVL_IO.m`, `AVL/parseST.m`, `parseSB.m`, `parseRunCaseHeader.m`, `findValue.m`.
- Python aircraft files are `Python/models/<name>.jsonc` with `//` comments on **every** key. MATLAB keeps `.mat`.
- Full PySide6 GUI port (`aid_gui`), calculation engine in `aid` with no widgets.
- Batch mesh: Tornado span 10 / chord 5 / mode 0; AVL span 10 / chord 10; no `questdlg` (wing-only = No, NP estimate = No, check_io = false).
- Compare Python vs `Results/matlab/` with spec §13 tolerances. Shared Fortran binaries must match at parser precision.
- Attempt all 23 models; exotic failures are recorded in `status.json`, never fabricated.
- Primary pass aircraft: Cessna 172, Navion, DA20-C1, Learjet 23.
- Do **not** `git commit` or `git push` unless the user explicitly asks. Suggested messages are recorded per task for when they do.
- Do not use Composer 2.5 Fast or Kimi 3 subagents.
- After each meaningful slice, bump `UPDATES.md` (project-docs). Only `README.md` and `UPDATES.md` among markdown files may be edited without a separate ask, plus the files this plan names.

## File structure (locked)

```
AircraftIntuitiveDesign/
  Docs/2026-08-26-aid-linux-python-port-spec.md      # this spec
  Docs/2026-08-26-aid-linux-python-port-plan.md      # this plan
  README.md
  UPDATES.md
  Matlab/fsroot/code/
    run_aid_batch.m                                 # CREATE — headless gold runner
    AID.m                                           # MODIFY — Linux binary names
    DATCOM_IO.m                                     # MODIFY — batch skips dialogs
    AVL_IO.m                                        # MODIFY — ./avl
    DATCOM/datcom                                   # CREATE — wrapper script
    DATCOM/datcom.bin                               # CREATE — gfortran output
    AVL/run/avl                                     # CREATE — AVL 3.52 executable
    Models/*.mat                                    # RENAME — decode %20
  Python/
    pyproject.toml
    src/aid/{__init__,aircraft,jsonc,atmosphere,geometry,aero,drag,
             datcom_io,datcom_parse,datcom_run,
             tornado_io,tornado/{lattice,solver,coeff,boundary},
             avl_io,avl_parse,compare,paths}.py
    src/aid_gui/{__init__,app,main_window,tabs,view3d,menus}.py
    scripts/{mat_to_jsonc.py,run_all.py}
    tests/...
    models/*.jsonc
  Results/{matlab,python,compare}/
```

---

### Task 1: Toolchain, README, DATCOM compile + wrapper

**Files:**
- Create: `README.md`
- Create: `UPDATES.md`
- Create: `Matlab/fsroot/code/DATCOM/datcom` (wrapper)
- Create: `Matlab/fsroot/code/DATCOM/datcom.bin` (compiled)
- Test: compile smoke + wrapper copies `for006.dat`

**Interfaces:**
- Consumes: `/home/valentin/Projects/MDT/USAF_DATCOM/datcom/datcom.f`
- Produces: executable wrapper `Matlab/fsroot/code/DATCOM/datcom` that reads `for005.dat` in cwd and writes `for006.dat` + `datcom.out`

- [ ] **Step 1: Install compilers if missing**

Run:

```bash
command -v gfortran || sudo apt-get update && sudo apt-get install -y gfortran make libx11-dev
gfortran --version
```

Expected: a gfortran version line, no error.

- [ ] **Step 2: Compile DATCOM**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/datcom
gfortran -O2 -std=legacy -fallow-argument-mismatch -fbackslash \
  datcom.f -o /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/DATCOM/datcom.bin
test -x /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/DATCOM/datcom.bin
```

Expected: thousands of warnings, **zero errors**, executable exists. If `-fbackslash` fails, retry without it.

- [ ] **Step 3: Write the stdin wrapper**

Create `Matlab/fsroot/code/DATCOM/datcom`:

```bash
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$DIR/datcom.bin"
if [[ ! -f for005.dat ]]; then
  echo "DATCOM wrapper: for005.dat not found in $(pwd)" >&2
  exit 2
fi
# PDAS binary prompts: Enter the input file name:
printf 'for005.dat\n' | "$BIN"
if [[ -f datcom.out ]]; then
  cp -f datcom.out for006.dat
else
  echo "DATCOM wrapper: datcom.out was not produced" >&2
  exit 3
fi
```

`chmod +x Matlab/fsroot/code/DATCOM/datcom`

- [ ] **Step 4: Smoke-test wrapper with a minimal for005**

Write `Matlab/fsroot/code/DATCOM/for005.dat`:

```
CASEID WRAPPER SMOKE
 $FLTCON NALPHA=3.0,ALSCHD=-2.0,0.0,2.0,
  NALT=1.0,ALT=0.0,
  NMACH=1.0,MACH=0.200,
  WT=1000.00,LOOP=2.0$
 $OPTINS SREF=100.00,CBARR=5.00,BLREF=20.00$
 $SYNTHS XCG=5.00,ZCG=0.00,XW=2.00,ZW=0.00,ALIW=0.00,
  XH=15.00,ZH=1.00,ALIH=0.00,XV=15.00,YV=0.00,ZV=0.00,VERTUP=.TRUE.$
 $BODY NX=3.0,ITYPE=1.0,
  X=0.00,5.00,20.00,
  ZU=0.50,1.00,0.20,
  ZL=-0.50,-1.00,-0.20,
  R=0.50,1.00,0.20,
  S=0.79,3.14,0.13$
NACA-W-4-2412
 $WGPLNF CHRDR=5.00,CHRDBP=5.00,CHRDTP=5.00,SSPN=10.00,
  SSPNOP=0.00,SAVSI=0.00,SAVSO=0.00,CHSTAT=0.25,
  DHDADI=0.00,DHDADO=0.00,TWISTA=0.00,TYPE=1.0$
PLOT
NEXT CASE
```

Run:

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/DATCOM
./datcom
test -s for006.dat && grep -q "CASEID" datcom.out
```

Expected: exit 0, `for006.dat` non-empty. If DATCOM rejects the namelist, keep `datcom.out` and fix the smoke input until the file contains coefficient tables (search for `CL` or `CN`). Do not proceed to Task 5 until this wrapper works.

- [ ] **Step 5: README + UPDATES**

`README.md`:

```markdown
# Aircraft Intuitive Design

## Idea
MATLAB (and Python twin) GUI for conceptual aircraft geometry plus DATCOM, Tornado, and AVL aerodynamic coefficients.

## Architecture
MATLAB app lives in `Matlab/fsroot/code`. Linux DATCOM/AVL binaries sit beside the original Windows/macOS ones. Python package is `Python/` (`aid` engine + `aid_gui`). Oracle dumps are `Results/`.

## Reading order for agents
1. Read this `README.md` (mandatory if present).
2. Read `UPDATES.md` (mandatory) for the change history and current state before working.
3. Read `Docs/2026-08-26-aid-linux-python-port-spec.md` and `Docs/2026-08-26-aid-linux-python-port-plan.md`.
```

`UPDATES.md`:

```markdown
# Updates

## 0.1.0 - Linux DATCOM binary and wrapper
- Compiled PDAS `datcom.f` to `Matlab/fsroot/code/DATCOM/datcom.bin`
- Added `DATCOM/datcom` wrapper: stdin `for005.dat`, copy `datcom.out` → `for006.dat`
```

---

### Task 2: Decode model filenames

**Files:**
- Modify: `Matlab/fsroot/code/Models/*.mat` (rename only)
- Test: MATLAB `dir` shows spaces, 23 files, load Cessna 172

**Interfaces:**
- Consumes: URL-encoded names (`Cessna%20172.mat`)
- Produces: decoded names (`Cessna 172.mat`)

- [ ] **Step 1: Rename**

```bash
python3 - <<'PY'
from pathlib import Path
from urllib.parse import unquote
p = Path("/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/Models")
for f in list(p.glob("*.mat")):
    new = p / unquote(f.name)
    if new != f:
        print(f"rename {f.name!r} -> {new.name!r}")
        f.rename(new)
print("count", len(list(p.glob("*.mat"))))
PY
```

Expected: `Cessna 172.mat` exists; no remaining `%20` in names; count 23. Leave `.DS_Store` if present.

- [ ] **Step 2: Verify MATLAB load**

```bash
/home/valentin/ProgramFiles/MB2025b/bin/matlab -batch "S=load('/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/Models/Cessna 172.mat'); disp(S.WG.CHRDR); disp(S.unit)"
```

Expected: `2` and `ft`.

- [ ] **Step 3: UPDATES**

Add top entry `0.1.1 - Decode model %20 filenames`.

---

### Task 3: Compile AVL 3.52 for Linux

**Files:**
- Modify: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/bin/Makefile.gfortranDP` (X11 path) and/or `plotlib/config.make`
- Create: `Matlab/fsroot/code/AVL/run/avl`
- Test: `./avl` prints the AVL banner then exit via stdin `Quit`

**Interfaces:**
- Consumes: `AVL3.52rel09032025` README build sequence
- Produces: `Matlab/fsroot/code/AVL/run/avl`

- [ ] **Step 1: Point plotlib/X11 at Linux**

In `AVL3.52rel09032025/bin/Makefile.gfortranDP` replace:

```
PLTLIB = -L/opt/X11/lib -lX11
```

with:

```
PLTLIB = -L/usr/lib/x86_64-linux-gnu -lX11
```

If `pkg-config --libs x11` returns a different `-L`, use that. Also set `GFIX = -fallow-argument-mismatch` (already in file).

Check `plotlib/config.make` / `config.make.gfortranDP` for the same `/opt/X11` path and fix identically.

- [ ] **Step 2: Build plotlib**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/AVL/AVL3.52rel09032025/plotlib
make clean || true
make gfortranDP
test -f libPlt_gDP.a || test -f libPlt.a
```

Expected: static plot library exists.

- [ ] **Step 3: Build eispack**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/AVL/AVL3.52rel09032025/eispack
make -f Makefile.gfortran
test -f libeispack.a || test -f eispack.a
```

Expected: eispack archive exists. If the makefile name differs, use the gfortran makefile present in that directory.

- [ ] **Step 4: Build avl and install into AID run dir**

```bash
cd /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/AVL/AVL3.52rel09032025/bin
make -f Makefile.gfortranDP avl
test -x avl
cp -f avl /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/AVL/run/avl
chmod +x /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/AVL/run/avl
```

- [ ] **Step 5: Batch smoke (graphics off)**

```bash
cd /tmp
printf 'PLOP\ng\n\nQuit\n' | /home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/AVL/run/avl
```

Expected: process exits 0 (or AVL’s normal quit) without hanging. If it waits for X display, confirm `PLOP/g` sequence against `avl_doc` and `AVL_IO.Write_Case`.

- [ ] **Step 6: UPDATES** `0.2.0 - Linux AVL 3.52 binary in AVL/run/avl`

---

### Task 4: Patch MATLAB AID for Linux binaries and batch dialogs

**Files:**
- Modify: `Matlab/fsroot/code/AID.m` (DATCOM `system` call ~1594)
- Modify: `Matlab/fsroot/code/AVL_IO.m` (AVL `system` call ~35)
- Modify: `Matlab/fsroot/code/DATCOM_IO.m` (`questdlg` wing-only and CG prompts)

**Interfaces:**
- Consumes: Task 1 wrapper `./datcom`, Task 3 `./avl`
- Produces: GUI and batch both invoke Linux binaries; `choice=='batch'` skips dialogs

- [ ] **Step 1: Patch `AID.m` DATCOM else-branch**

Replace:

```matlab
system('./datcom.osx');
```

with:

```matlab
system('./datcom');
```

Keep `datcomimport('for006.dat',true)`. Do not delete the `ispc` branch.

- [ ] **Step 2: Patch `AVL_IO.m` else-branch**

Replace:

```matlab
setenv('DYLD_LIBRARY_PATH', '/usr/local/bin:/opt/local/lib:')
system(['./avl3.35',' < ',CaseID,'.run']);
```

with:

```matlab
system(['./avl',' < ',CaseID,'.run']);
```

- [ ] **Step 3: Patch `DATCOM_IO.m` dialogs for batch**

In `Write_DATCOM`, the wing-only block is:

```matlab
if max(abs([F.DELTA,A.DELTAL])) && strcmp(choice,'DATCOM')
    owg = questdlg('Run wing-only case to evaluate flaps/ailerons?');
else
    owg = 'no thanks, I would not like to run a wing-only case';
end
```

Change the condition so batch never dialogs:

```matlab
if max(abs([F.DELTA,A.DELTAL])) && strcmp(choice,'DATCOM')
    owg = questdlg('Run wing-only case to evaluate flaps/ailerons?');
else
    owg = 'no thanks, I would not like to run a wing-only case';
end
```

`choice=='batch'` already falls in the else. **Also** the CG `questdlg` block uses `strcmp(choice,'DATCOM')` — `'batch'` already skips it. Verify by reading the function; if any other `questdlg` fires on `'batch'`, default to No.

- [ ] **Step 4: Patch Tornado NP dialog for batch**

In `AID.m` around the `questdlg('Estimate Neutral Point?')` call, wrap:

```matlab
if ~strcmp(choice,'batch')
    np = questdlg('Estimate Neutral Point?','Iterate to Find NP');
else
    np = 'No';
end
```

Same for Tornado `inputdlg` mesh: batch will not go through `AID.m` (it uses `run_aid_batch.m`). Do not remove GUI dialogs.

- [ ] **Step 5: Manual GUI smoke (optional if display available)**

```matlab
cd('/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code')
AID
```

Help → Examples → Cessna 172. Analyze → DATCOM / Tornado / AVL. If no DISPLAY, skip and rely on Task 5.

---

### Task 5: Headless MATLAB gold runner

**Files:**
- Create: `Matlab/fsroot/code/run_aid_batch.m`
- Create: `Results/matlab/` tree (runtime)
- Test: Cessna 172 produces three JSON files and `status.json`

**Interfaces:**
- Consumes: loaded `.mat` structs; `DATCOM_IO`, Tornado functions, `AVL_IO`, `parseST`
- Produces: `Results/matlab/<aircraft>/{datcom.json,tornado.json,avl.json,status.json,for005.dat,datcom.out,geometry.st}`

- [ ] **Step 1: Write `run_aid_batch.m`**

This function must not use `inputdlg`/`questdlg`. It reconstructs AID globals from the `.mat`, calls Geometry-derived fields already in the file, and runs the three solvers.

```matlab
function run_aid_batch(model_name)
%RUN_AID_BATCH  Gold DATCOM/Tornado/AVL dump for one aircraft .mat
% model_name e.g. 'Cessna 172' (no extension)
if nargin < 1, model_name = 'Cessna 172'; end

this = fileparts(mfilename('fullpath'));
addpath(this, fullfile(this,'Tornado'), fullfile(this,'AVL'));
lib_path = [this filesep];
assignin('base','lib_path',lib_path); %#ok<NASGU>
global lib_path WG HT VT F A E R BD NP NB AERO Results cmp opt ATM AC
lib_path = [this filesep];

root = fileparts(fileparts(fileparts(this))); % AircraftIntuitiveDesign
out_dir = fullfile(root,'Results','matlab',model_name);
if ~exist(out_dir,'dir'), mkdir(out_dir); end

S = load(fullfile(this,'Models',[model_name,'.mat']));
WG=S.WG; HT=S.HT; VT=S.VT; F=S.F; A=S.A; E=S.E; R=S.R; BD=S.BD;
NP=S.NP; NB=S.NB; AERO=S.AERO;
if ~isfield(S,'unit'), unit='ft'; else, unit=S.unit; end
Results = cell(1,4);
ATM = Atmosphere(AERO.ALT(1));
ATM.Q = 0.5*ATM.D*(AERO.MACH(1)*ATM.a)^2;
AC = struct('alpha',AERO.ALSCHD(max(1,ceil(end/2))),'CD0',0);
if isfield(WG,'CD0'), AC.CD0 = WG.CD0; end

% Fake component checkboxes: all on if plot_cmp missing
cmp = gobjects(1,8); %#ok<NASGU>
% Tornado_IO uses get(cmp(i),'Value') — provide dummy handles via figure-less stubs.
% Use a hidden figure so get() works.
hf = figure('Visible','off','HandleVisibility','off');
for i=1:8
    cmp(i) = uicontrol(hf,'Style','checkbox','Value',1,'Visible','off');
end
if isfield(S,'plot_cmp')
    for i=1:min(4,numel(S.plot_cmp)), set(cmp(i),'Value',S.plot_cmp(i)); end
end
opt = gobjects(1,17);
for i=1:17
    opt(i) = uimenu(hf,'Label','x','Checked','off','Visible','off');
end
set(opt(1),'UserData',repmat({'0'},3,10));
set(opt(9),'UserData',[0.5,0.9]);
set(opt(14),'Checked',onoff(strcmp(unit,'in')));

status = struct('datcom','failed','tornado','failed','avl','failed','error',{{}});

try
    cd(fullfile(this,'DATCOM'));
    delete('*.dat');
    DATCOM_IO('for005.dat','case','batch',false,unit);
    [st,cmdout] = system('./datcom'); %#ok<ASGLU>
    if exist('for005.dat','file'), copyfile('for005.dat',fullfile(out_dir,'for005.dat')); end
    if exist('datcom.out','file'), copyfile('datcom.out',fullfile(out_dir,'datcom.out')); end
    if exist('for006.dat','file') && exist('datcomimport','file')
        Results{1} = datcomimport('for006.dat',true);
        if iscell(Results{1}), Results{1}=Results{1}{1}; end
        if isfield(Results{1},'cl')
            status.datcom = 'ok';
            write_json(fullfile(out_dir,'datcom.json'), strip_datcom(Results{1}));
        end
    end
catch ME
    status.error{end+1} = ['datcom: ' ME.message];
end
cd(this);

try
    mesh = {'10','5'};
    [geo,state] = Tornado_IO(mesh);
    [lattice,ref] = fLattice_setup2(geo,state,0);
    tres = solver(state,geo,lattice);
    tres = coeff_create3(tres,lattice,state,ref,geo);
    Results{3} = tres;
    status.tornado = 'ok';
    write_json(fullfile(out_dir,'tornado.json'), strip_tornado(tres));
catch ME
    status.error{end+1} = ['tornado: ' ME.message];
end

try
    mesh = {'10','10'};
    [geo,state] = Tornado_IO(mesh);
    avl_path = AVL_IO(mesh,geo,state,false);
    stfile = fullfile(avl_path,'geometry.st');
    if exist(stfile,'file')
        Results{4} = parseST(stfile);
        status.avl = 'ok';
        write_json(fullfile(out_dir,'avl.json'), Results{4});
        copyfile(stfile, fullfile(out_dir,'geometry.st'));
        copyfile(fullfile(avl_path,'geometry.avl'), fullfile(out_dir,'geometry.avl'));
    end
catch ME
    status.error{end+1} = ['avl: ' ME.message];
end

write_json(fullfile(out_dir,'status.json'), status);
close(hf);
fprintf('batch %s datcom=%s tornado=%s avl=%s\n', model_name, status.datcom, status.tornado, status.avl);
end

function s = onoff(tf)
if tf, s='on'; else, s='off'; end
end

function write_json(path, obj)
fid = fopen(path,'w'); fwrite(fid, jsonencode(obj,'PrettyPrint',true)); fclose(fid);
end

function D = strip_datcom(S)
keep = {'alpha','cl','cd','cm','cn','ca','cla','cma','cyb','cnb','clb','xcg','mach','alt'};
D = struct();
for i=1:numel(keep)
    if isfield(S,keep{i}), D.(keep{i}) = S.(keep{i}); end
end
end

function D = strip_tornado(S)
keep = {'CL','CD','Cm','CY','Cl','Cn','CL_a','Cm_a','CY_b','Cl_b','Cn_b','CL0','Cm0'};
D = struct();
for i=1:numel(keep)
    if isfield(S,keep{i}), D.(keep{i}) = S.(keep{i}); end
end
end
```

If `Tornado_IO` / `get(cmp)` still needs more globals (`AC.CD0` is used in AVL write), set them as above. If `fLattice_setup2` requires `config.m`, the `addpath` Tornado folder covers it.

`solver.m` uses a waitbar handle `h` and `isvalid(h)`. In batch a waitbar is still created — that is OK without a display? On Linux with no X, waitbar can fail. If it fails, patch `solver.m` **only** to treat missing waitbar as valid:

```matlab
[w2,~,h]=fastdw(lattice,1);
if ~isempty(h) && ishandle(h) && ~isvalid(h), results = []; return, end
```

Keep the change minimal; prefer setting `set(0,'DefaultFigureVisible','off')` at the top of `run_aid_batch`.

- [ ] **Step 2: Run Cessna 172**

```bash
/home/valentin/ProgramFiles/MB2025b/bin/matlab -batch "cd('/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code'); run_aid_batch('Cessna 172')"
```

Expected: `Results/matlab/Cessna 172/status.json` with `"datcom":"ok"` (Aerospace Toolbox present). Tornado/AVL ok. If DATCOM fails, open `datcom.out` and fix `DATCOM_IO` namelist or wrapper cwd.

- [ ] **Step 3: Fix until Cessna 172 has all three `ok`**

Do not mark this task complete with fabricated JSON. Primary blocker is usually: DATCOM cwd, AVL `./avl` not executable, Tornado `cmp` handles, `lib_path` trailing slash.

---

### Task 6: Batch all 23 models

**Files:**
- Create: `Matlab/fsroot/code/run_aid_batch_all.m`
- Create: `Results/matlab/<each aircraft>/status.json`
- Test: 23 status files exist; Cessna/Navion/DA20-C1/Learjet 23 all three solvers `ok`

**Interfaces:**
- Consumes: `run_aid_batch`
- Produces: `Results/matlab/_summary.json`

- [ ] **Step 1: Write driver**

```matlab
function run_aid_batch_all
this = fileparts(mfilename('fullpath'));
d = dir(fullfile(this,'Models','*.mat'));
summary = struct('name',{},'datcom',{},'tornado',{},'avl',{});
root = fileparts(fileparts(fileparts(this)));
for i=1:numel(d)
    name = d(i).name(1:end-4);
    fprintf('==== %s ====\n', name);
    try
        run_aid_batch(name);
    catch ME
        fprintf('FATAL %s: %s\n', name, ME.message);
    end
    stpath = fullfile(root,'Results','matlab',name,'status.json');
    row.name = name; row.datcom='missing'; row.tornado='missing'; row.avl='missing';
    if exist(stpath,'file')
        st = jsondecode(fileread(stpath));
        row.datcom = st.datcom; row.tornado = st.tornado; row.avl = st.avl;
    end
    summary(end+1) = row; %#ok<AGROW>
end
fid = fopen(fullfile(root,'Results','matlab','_summary.json'),'w');
fwrite(fid, jsonencode(summary,'PrettyPrint',true)); fclose(fid);
end
```

- [ ] **Step 2: Run**

```bash
/home/valentin/ProgramFiles/MB2025b/bin/matlab -batch "cd('/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code'); run_aid_batch_all"
```

Expected: `_summary.json` with 23 rows. Primary four aircraft three-way `ok`. Others may fail; leave their `status.json` errors intact.

- [ ] **Step 3: UPDATES** `0.3.0 - MATLAB gold Results/matlab for bundled models`

---

### Task 7: Python package skeleton

**Files:**
- Create: `Python/pyproject.toml`
- Create: `Python/src/aid/__init__.py`
- Create: `Python/src/aid/paths.py`
- Create: `Python/tests/test_paths.py`

**Interfaces:**
- Produces:

```python
def repo_root() -> Path: ...
def matlab_code() -> Path: ...
def datcom_wrapper() -> Path: ...  # .../DATCOM/datcom
def avl_bin() -> Path: ...         # .../AVL/run/avl
def results_dir() -> Path: ...
```

- [ ] **Step 1: Failing test**

`Python/tests/test_paths.py`:

```python
from aid.paths import avl_bin, datcom_wrapper, matlab_code, repo_root

def test_binaries_exist():
    assert (matlab_code() / "AID.m").is_file()
    assert datcom_wrapper().is_file()
    assert avl_bin().is_file()
    assert repo_root().name == "AircraftIntuitiveDesign"
```

- [ ] **Step 2: Run to fail**

```bash
cd Python && python -m pytest tests/test_paths.py -v
```

Expected: FAIL `ModuleNotFoundError: aid`

- [ ] **Step 3: Implement**

`Python/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "aid"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["numpy", "scipy", "PySide6"]

[project.optional-dependencies]
dev = ["pytest"]

[tool.setuptools.packages.find]
where = ["src"]
```

`Python/src/aid/paths.py`:

```python
from pathlib import Path

def repo_root() -> Path:
    p = Path(__file__).resolve()
    for cand in p.parents:
        if (cand / "Matlab" / "fsroot" / "code" / "AID.m").is_file():
            return cand
    raise FileNotFoundError("AircraftIntuitiveDesign root not found")

def matlab_code() -> Path:
    return repo_root() / "Matlab" / "fsroot" / "code"

def datcom_wrapper() -> Path:
    return matlab_code() / "DATCOM" / "datcom"

def avl_bin() -> Path:
    return matlab_code() / "AVL" / "run" / "avl"

def results_dir() -> Path:
    return repo_root() / "Results"
```

```bash
cd Python && pip install -e ".[dev]" && python -m pytest tests/test_paths.py -v
```

Expected: PASS.

---

### Task 8: JSONC aircraft I/O + mat converter

**Files:**
- Create: `Python/src/aid/jsonc.py`
- Create: `Python/src/aid/aircraft.py`
- Create: `Python/src/aid/field_docs.py`
- Create: `Python/scripts/mat_to_jsonc.py`
- Create: `Python/tests/test_jsonc_roundtrip.py`
- Create: `Python/models/Cessna 172.jsonc` (via converter)

**Interfaces:**
- Consumes: MATLAB `.mat` keys listed in spec §6
- Produces:

```python
@dataclass
class Aircraft:
    WG: dict
    HT: dict
    VT: dict
    F: dict
    A: dict
    E: dict
    R: dict
    BD: dict
    NP: list
    NB: list
    AERO: dict
    plot_cmp: list
    unit: str
    cg_data: list | None = None

def loads_jsonc(text: str) -> dict: ...
def dumps_jsonc(data: dict, docs: dict) -> str: ...
def load_mat(path: Path) -> Aircraft: ...
def load_jsonc(path: Path) -> Aircraft: ...
def save_jsonc(ac: Aircraft, path: Path) -> None: ...
```

Every emitted JSONC key has a trailing `//` comment from `field_docs.DOCS` (nested paths like `WG.CHRDR`). Missing doc is a **test failure**, not a silent skip.

- [ ] **Step 1: Failing tests**

```python
from pathlib import Path
from aid.aircraft import load_jsonc, load_mat, save_jsonc
from aid.jsonc import loads_jsonc

MAT = Path("/home/valentin/Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign/Matlab/fsroot/code/Models/Cessna 172.mat")

def test_mat_chrdr():
    ac = load_mat(MAT)
    assert ac.unit == "ft"
    assert abs(ac.WG["CHRDR"] - 2.0) < 1e-9
    assert list(ac.AERO["ALSCHD"]) == [-4, 0, 4, 8, 12]

def test_jsonc_comments_on_every_key(tmp_path):
    ac = load_mat(MAT)
    out = tmp_path / "c.jsonc"
    save_jsonc(ac, out)
    text = out.read_text()
    data = loads_jsonc(text)
    assert data["WG"]["CHRDR"] == 2.0
    # every non-empty data line that contains a key must contain //
    for line in text.splitlines():
        s = line.strip()
        if s in "{[]}," or not s or s.startswith("//"):
            continue
        if ":" in s:
            assert "//" in s, line

def test_roundtrip(tmp_path):
    ac = load_mat(MAT)
    p = tmp_path / "c.jsonc"
    save_jsonc(ac, p)
    ac2 = load_jsonc(p)
    assert ac2.WG["SSPN"] == ac.WG["SSPN"]
    assert ac2.AERO["XCG"] == ac.AERO["XCG"]
```

- [ ] **Step 2: pytest fail** then implement `jsonc.py` (strip `//` outside strings), `field_docs.py` (catalog from spec §6.1–6.4 **and** derived fields present on Cessna: `cbar`, `S`, `AR`, … — copy labels from `Initialize_GUI.m` / spec), `aircraft.py` using `scipy.io.loadmat(..., squeeze_me=True, struct_as_record=False)`.

MATLAB structs become `mat_struct` objects; convert recursively to dicts/lists. Field `i` stays `"i"`. Cell `NP`/`NB`: empty doubles → `null`.

`dumps_jsonc` walks dicts; for each key looks up `DOCS[path]` e.g. `"WG.CHRDR": "Root chord, ft (DATCOM CHRDR)"`.

- [ ] **Step 3: Convert all 23 models**

```bash
cd Python && python scripts/mat_to_jsonc.py
ls models/*.jsonc | wc -l
```

Expected: 23 jsonc files. Spot-check `Cessna 172.jsonc` has `//` on `CHRDR`, `ALSCHD`, `XCG`.

---

### Task 9: Atmosphere, Geometry, Drag (numeric twin)

**Files:**
- Create: `Python/src/aid/atmosphere.py` — port `Atmosphere.m` literally
- Create: `Python/src/aid/geometry.py` — port `Geometry.m`
- Create: `Python/src/aid/drag.py` — port `Drag.m`
- Create: `Python/tests/test_geometry_cessna.py`

**Interfaces:**

```python
def atmosphere(h_ft: float) -> dict:  # keys T,P,D,V,a
def geometry(pt: dict, angl: bool, type: str = "") -> dict:
def drag(pt: dict, unit: str, atm: dict, wg_sref: float) -> dict:
```

- [ ] **Step 1: Test against Cessna .mat derived fields**

```python
from aid.aircraft import load_mat
from aid.geometry import geometry
from pathlib import Path

def test_wing_area_matches_mat():
    ac = load_mat(Path(".../Models/Cessna 172.mat"))
    wg = {k: ac.WG[k] for k in
          ["CHRDR","CHRDBP","CHRDTP","SSPN","SSPNOP","SAVSI","SAVSO",
           "CHSTAT","DHDADI","DHDADO","X","Y","Z"]}
    out = geometry(wg, angl=False)
    assert abs(out["S"] if not hasattr(out["S"], "__len__") else out["S"][-1] if False else (out["S"][-1] if isinstance(out["S"], list) else out["S"]) - 24) < 1e-6 or abs(float(np.asarray(out["S"]).reshape(-1)[-1]) - 24) < 1e-6
```

Use `numpy.asarray(...).reshape(-1)[-1]` and compare to `ac.WG["S"]` (already 24), `cbar` (2), `AR` (~5.9918). Atmosphere at 0 ft: `T≈518.69`, `a≈sqrt(1.4*1716*T)`.

- [ ] **Step 2: Port formulas from `Geometry.m` and `Atmosphere.m` with no “simplification.”** Washout/sweep branches (`SSPNOP` vs linear taper) must both exist.

---

### Task 10: DATCOM writer (port `Write_DATCOM`)

**Files:**
- Create: `Python/src/aid/datcom_io.py`
- Create: `Python/tests/test_datcom_writer.py`

**Interfaces:**

```python
def write_for005(ac: Aircraft, path: Path, *, unit: str, cg_calc: bool = False) -> None:
```

Must emit the same namelist families as `DATCOM_IO.m`: `DIM` (inches only), `CASEID`, `$FLTCON`, `$OPTINS`, `$SYNTHS`, `$BODY`, `NACA-W-…`, `$WGPLNF`, optional `$WGSCHR`, HT/VT, `$SYMFLP` (flap then elevator), `$ASYFLP`, `PLOT`, `NEXT CASE`.

`SSPNOP` conversion: if nonzero, write `SSPN-SSPNOP` (span from tip), matching MATLAB.

- [ ] **Step 1: Test** — write Cessna for005, assert file contains `$FLTCON`, `NACA-W-4-2412` or `NACA-W-4-2412` depending on `length(WG.NACA{1})` (Cessna NACA is `{'2412','2412'}`, MATLAB `WG.NACA{1}` is `'2412'`, length 4), `MACH=0.030`, `SREF=24`.

- [ ] **Step 2: Implement by translating `DATCOM_IO.m` `Write_DATCOM` from line 528 to 840.** Use `choice` equivalent of batch (always full aircraft, `owg` not Yes).

---

### Task 11: DATCOM parser + runner

**Files:**
- Create: `Python/src/aid/datcom_parse.py`
- Create: `Python/src/aid/datcom_run.py`
- Create: `Python/tests/test_datcom_run_cessna.py`

**Interfaces:**

```python
def parse_for006(text: str) -> dict:  # keys alpha, cl, cd, cm, ...
def run_datcom(ac: Aircraft, workdir: Path) -> dict:
```

`run_datcom`: write for005 into `workdir`, `subprocess.run([str(datcom_wrapper())], cwd=workdir, check=True, timeout=120)`, parse `for006.dat`.

Parser: Digital DATCOM print tables are 132-col. Prefer matching MATLAB `datcomimport` field names (lowercase). If a full parser is large, first milestone: parse the static-stability `CL`, `CD`, `CM` vs `ALPHA` rows that AID plots (`Results{1}.cl`, `.cm`, `.alpha`). Expand until `Results/matlab/Cessna 172/datcom.json` keys match.

- [ ] **Step 1: Test vs gold**

```python
def test_cessna_datcom_matches_matlab():
    gold = json.loads(Path("Results/matlab/Cessna 172/datcom.json").read_text())
    ac = load_jsonc(Path("Python/models/Cessna 172.jsonc"))
    got = run_datcom(ac, Path("/tmp/aid-datcom-cessna"))
    assert np.allclose(got["alpha"], gold["alpha"], atol=1e-6)
    assert np.allclose(got["cl"], gold["cl"], atol=1e-6, rtol=0)
```

Shared binary ⇒ parsers must agree. If they do not, fix Python parser, not the Fortran.

---

### Task 12: Tornado_IO port

**Files:**
- Create: `Python/src/aid/tornado_io.py`
- Create: `Python/tests/test_tornado_io.py`

**Interfaces:**

```python
def write_geometry(pt: dict, controls: list, ni: int, nj: int, m: tuple[int,int], geo=None, type: str = "h") -> dict:
def tornado_io(ac: Aircraft, mesh: tuple[str, str, ...]) -> tuple[dict, dict]:
```

`state` keys must match MATLAB: `AS, alpha, betha, P, Q, R, alphadot, bethadot, ALT, rho, pgcorr`.

`AS = MACH * ATM.a / 3.28084`, `ALT = AERO.ALT/3.28084`, `rho = ATM.D*515.379` (`Tornado_IO.m`).

- [ ] **Step 1: Test** — Cessna `mesh=('10','5')`, `geo['nwing']>=1`, `geo['c'][0,0]==WG.CHRDR` (2.0), `state['betha']==0`.

- [ ] **Step 2: Translate `Tornado_IO.m` including flap `eta` splitting and vertical-tail `type=='v'`.**

---

### Task 13: Tornado VLM port

**Files:**
- Create: `Python/src/aid/tornado/lattice.py`  # `fLattice_setup2`
- Create: `Python/src/aid/tornado/boundary.py`  # `setboundary5`
- Create: `Python/src/aid/tornado/solver.py`    # `solver` + downwash, no waitbar
- Create: `Python/src/aid/tornado/coeff.py`     # `coeff_create3`
- Create: `Python/src/aid/tornado/isa.py`       # `ISAtmosphere.m` if solver needs it
- Create: `Python/tests/test_tornado_cessna.py`
- Modify: supporting files only if the MATLAB functions call them (`fViscCorr2`, `fmultLattice`, `fPablo`, `fSonicCP`)

**Interfaces:**

```python
def lattice_setup(geo: dict, state: dict, mode: int) -> tuple[dict, dict]:
def solver(state: dict, geo: dict, lattice: dict) -> dict:
def coeff_create(results: dict, lattice: dict, state: dict, ref: dict, geo: dict) -> dict:
```

- [ ] **Step 1: Dump MATLAB lattice size for Cessna in a one-off if needed; test `CL` vs `Results/matlab/Cessna 172/tornado.json` with spec §13 (1e-4 relative).**

- [ ] **Step 2: Port panel-for-panel.** Do not replace Tornado with a different VLM. Drop waitbar; never return empty results because a figure was missing.

- [ ] **Step 3: `numpy.linalg.solve` for `gamma=w2\rhs`.** Preserve Prandtl-Glauert branch `state.pgcorr`.

---

### Task 14: AVL writer + parser port

**Files:**
- Create: `Python/src/aid/avl_io.py`     # Write_Input, Write_Surface, Write_Case, run
- Create: `Python/src/aid/avl_parse.py`  # findValue, parseST, parseSB, parseRunCaseHeader
- Create: `Python/tests/test_avl_parse.py`
- Create: `Python/tests/test_avl_run_cessna.py`

**Interfaces:**

```python
def write_avl(ac: Aircraft, geo: dict, state: dict, run_dir: Path, ni: int, nj: int) -> None:
def run_avl(run_dir: Path) -> None:  # subprocess avl_bin() < geometry.run
def parse_st(path: Path) -> dict:    # keys CLa, Cma, ...
```

`Write_Case` must match `AVL_IO.m`: `LOAD geometry.avl`, `PLOP/g`, `OPER`, `c1`, `v <AS>`, `x`, `st`, `geometry.st`, `sb`, `geometry.sb`, `Quit`.

Airfoil `AFILE` files `WG.1`, `HT.1`, … as MATLAB does (`%.6f %.6f` of flipped foil).

- [ ] **Step 1: Unit-test `findValue` on a checked-in snippet of `Results/matlab/Cessna 172/geometry.st` (copy into `tests/data/` if gold exists).**

- [ ] **Step 2: `test_avl_run_cessna` — `CLa` matches gold `avl.json` at parser precision (`atol=1e-6`).** Shared AVL 3.52 binary.

---

### Task 15: Comparison harness

**Files:**
- Create: `Python/src/aid/compare.py`
- Create: `Python/scripts/run_all.py`
- Create: `Python/tests/test_compare_primary.py`

**Interfaces:**

```python
def run_python(ac: Aircraft, work: Path) -> dict:  # keys datcom, tornado, avl, status
def compare_to_matlab(name: str) -> dict:  # writes Results/compare/<name>.json
```

`run_all.py` loops `Python/models/*.jsonc`, writes `Results/python/<name>/`, then compare.

Tolerances from spec §13. Primary four aircraft must all pass in pytest. Others: record fail, pytest `xfail` or skip with reason from MATLAB `status.json` if MATLAB also failed that solver.

```python
PRIMARY = ["Cessna 172", "Navion", "DA20-C1", "Learjet 23"]

@pytest.mark.parametrize("name", PRIMARY)
def test_primary_all_solvers(name):
    report = compare_to_matlab(name)
    assert report["datcom"]["pass"]
    assert report["tornado"]["pass"]
    assert report["avl"]["pass"]
```

---

### Task 16: PySide6 shell — window, menus, 3D placeholder

**Files:**
- Create: `Python/src/aid_gui/app.py`
- Create: `Python/src/aid_gui/main_window.py`
- Create: `Python/src/aid_gui/menus.py`
- Create: `Python/tests/test_gui_smoke.py` (offscreen)

**Interfaces:**

```python
def main() -> int: ...
class MainWindow(QMainWindow):
    aircraft: Aircraft | None
```

Menus exactly: New, Load, Save, Analyze/{DATCOM,Tornado,AVL}, Settings/{Scale A/C Size, Estimate CG, Plot Options/{Transparent, Show Axes, Plot Resolution, Interpolated Shading, Project Dimensions, Aircraft Color}, Calculations/{Trim Mode, Estimate Slipstream, Multhopp's Method}, Units/{in-oz-ft/s, ft-lb-kts}, Inputs/Outputs, Error Check, Scroll Sensitivity}, Help/{Examples, Quick Start, User's Manual}.

Window title `Aircraft Intuitive Design Tool`, size 960×600.

- [ ] **Step 1: Offscreen smoke**

```python
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from aid_gui.main_window import MainWindow

def test_menus_exist():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    titles = [a.text() for a in w.menuBar().actions()]
    assert "Analyze" in titles
    assert "Help" in titles
```

- [ ] **Step 2: `python -m aid_gui` entry point in `pyproject.toml`:**

```toml
[project.scripts]
aid = "aid_gui.app:main"
```

Analyze actions may `QMessageBox.information("not wired")` until Task 18.

---

### Task 17: Geometry tabs bound to Aircraft

**Files:**
- Create: `Python/src/aid_gui/tabs.py`
- Modify: `Python/src/aid_gui/main_window.py`
- Create: `Python/tests/test_tabs_cessna.py`

**Interfaces:** Tabs Wing/HT/VT/Control/Body/Aero with the 16 planform fields (`RP` list), flap/aileron/elevator/rudder, body stations (up to 11 shown like MATLAB), aero `ALSCHD, ALT, MACH, WT, XCG, ZCG, XI, YI` and NACA boxes.

Load `Cessna 172.jsonc` → Wing Root Chord field shows `2`. Editing CHRDR and calling `aircraft_from_tabs()` returns `2.5` if user typed 2.5.

Labels from spec §6.1 (`Root Chord`, …).

`+` tab: stub “add part” disabled or minimal extra planform list (`NP`).

---

### Task 18: 3D view + Analyze wiring

**Files:**
- Create: `Python/src/aid_gui/view3d.py`  # matplotlib FigureCanvas in Qt or Qt3D; matplotlib is enough
- Modify: `Python/src/aid_gui/main_window.py` — Analyze slots call `aid.datcom_run`, tornado, avl
- Create: `Python/src/aid_gui/results_panel.py` — plot CL-alpha overlay like AID ~1370

**Interfaces:** After Analyze DATCOM, a results plot shows `alpha` vs `cl`. Errors from missing binary use `QMessageBox.critical` with the path.

Default meshes: Tornado 10/5, AVL 10/10, no extra dialogs unless Settings → Inputs/Outputs is checked (then show QDialog equivalent of `inputdlg`).

- [ ] **Step 1: Offscreen test** — load Cessna, call `window.run_datcom()` without display crash; `window.last_results["datcom"]["cl"]` nonempty.

- [ ] **Step 2: Open/Save JSONC via QFileDialog. Help → Examples lists `Python/models/*.jsonc`. Help → User's Manual opens `Matlab/fsroot/code/AID_Documentation.pdf` (`QDesktopServices.openUrl`).**

---

### Task 19: End-to-end verification + docs bump

**Files:**
- Modify: `README.md` (Python launch, MATLAB batch)
- Modify: `UPDATES.md` → `1.0.0 - Python AID GUI and solver parity`
- Test: commands below

- [ ] **Step 1: MATLAB still works**

```bash
/home/valentin/ProgramFiles/MB2025b/bin/matlab -batch "cd('.../code'); run_aid_batch('Cessna 172')"
```

- [ ] **Step 2: Python primary suite**

```bash
cd Python && python -m pytest tests/test_compare_primary.py tests/test_gui_smoke.py -v
```

Expected: PASS.

- [ ] **Step 3: `python -m aid.scripts.run_all` or `python scripts/run_all.py`** writes `Results/python` and `Results/compare`. Open `_summary` if added.

- [ ] **Step 4: Manual GUI (DISPLAY required):** `aid` or `python -m aid_gui`, Examples → Cessna 172, Analyze all three, Save JSONC.

---

## Self-review (plan vs spec)

| Spec requirement | Task |
|------------------|------|
| Linux DATCOM wrapper stdin/for006 | 1 |
| Decode `%20` models | 2 |
| AVL 3.52 from `AVL3.52rel09032025` | 3 |
| Patch AID/AVL_IO binaries | 4 |
| Gold `Results/matlab` all 23 | 5–6 |
| `aid` / `aid_gui` split | 7, 16 |
| JSONC + comments every key | 8 |
| Atmosphere/Geometry | 9 |
| DATCOM write/parse/run | 10–11 |
| Port Tornado_IO + VLM | 12–13 |
| Port AVL MATLAB helpers | 14 |
| Compare vs MATLAB oracle | 15 |
| Full PySide6 GUI | 16–18 |
| Composer 2.5 + Grok review | header / Global Constraints |
| No commits unless asked | Global Constraints |

Placeholder scan: no TBD. Tornado port is specified as 1:1 file mapping with tests against gold JSON, not “implement later.”

Type consistency: `Aircraft` dataclass is defined in Task 8 and used in 10–18. `tornado_io` returns `(geo, state)` consumed by 13–14. Paths helpers from Task 7 used everywhere.

## Suggested commit messages (only if the user asks to commit)

1. `build: compile Linux DATCOM and stdin wrapper`
2. `chore: decode AID model filenames`
3. `build: compile AVL 3.52 for Linux`
4. `fix: point AID at Linux DATCOM/AVL binaries`
5. `feat: MATLAB batch gold runner for DATCOM/Tornado/AVL`
6. `feat: dump Results/matlab for bundled aircraft`
7. `feat: Python aid package skeleton`
8. `feat: JSONC aircraft format and mat converter`
9. `feat: port Atmosphere/Geometry/Drag to Python`
10. `feat: DATCOM for005 writer and for006 parser`
11. `feat: port Tornado I/O and VLM`
12. `feat: port AVL writer and ST parser`
13. `feat: coefficient comparison harness`
14. `feat: PySide6 AID GUI`

---

Plan complete and saved to `Docs/2026-08-26-aid-linux-python-port-plan.md`. Spec is `Docs/2026-08-26-aid-linux-python-port-spec.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — Composer 2.5 implementer per task, Grok reviewer between tasks, as you specified.

**2. Inline Execution** — this session runs the tasks with checkpoints.

Which approach?
