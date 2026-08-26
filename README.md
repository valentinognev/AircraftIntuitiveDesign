# Aircraft Intuitive Design

## Idea
MATLAB GUI (AID) for conceptual aircraft geometry and aerodynamic coefficients via DATCOM, Tornado, and AVL. Python twin under `Python/` with a PySide6 GUI; aircraft files are `.mat` (MATLAB) and JSONC (Python).

## Architecture
- `Matlab/fsroot/code` — AID, Tornado VLM, AVL I/O, model `.mat` files.
- DATCOM Fortran lives beside this repo at `../datcom/datcom.f`; Linux binary is built locally and gitignored.
- AVL 3.52 source: `Matlab/fsroot/code/AVL/AVL3.52rel09032025/` (binaries gitignored).
- `Python/` — `aid` calculation engine and `aid_gui`.
- `Results/` — run dumps, not versioned.
- Spec/plan: `Docs/`.

## Reading order for agents
1. Read this `README.md` (mandatory if present).
2. Read `UPDATES.md` (mandatory) for the change history and current state before working.
3. Read `Docs/2026-08-26-aid-linux-python-port-spec.md` then `Docs/2026-08-26-aid-sdd-atomic-tasks.md`.
