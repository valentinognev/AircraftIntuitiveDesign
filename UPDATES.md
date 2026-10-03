# Updates

## 1.36.1 - The tornado `*_Q`/`*_P`/`*_R`/`*_b` sign entries, and four false claims
- **`_SIGN_MAP["tornado"]` gains ten entries**, all by one derivation rather than by patching the four that were reported. tornado's frame is x-aft/y-right/z-up and F-R-D is x-forward/y-right/z-down, a 180° rotation about y, so x and z reverse and y does not. A derivative with respect to a body rate picks up `s_i * s_j`; alpha, beta and control deflections are flow rotations and contribute nothing. Reading the whole emitted universe off that rule found **six** more missing keys beyond the four `*_Q`: `CY_P`, `CY_R`, `Cm_P`, `Cm_R` (the channel sign is `+1` there, so nothing cancels) and `CX_b`, `CZ_b`. `CZ_Q` shipped mirrored on every alpha of both aircraft
- Measured against AVL, whose map is empty and so prints F-R-D directly, seven of the ten have a witness: `CZq` -9.93/-9.54/-9.10/-8.86 (Cessna, alpha -4/0/+4/+6) and -8.35..-8.27 (Learjet) against raw `CZ_Q` +9.47..+9.74 and +8.84..+8.88 — opposite on all 8 points, within 8% after the flip; `CYr` +0.427/+0.539 against raw -0.387/-0.450; `CYp` -0.182/-0.0360 against raw +0.160/+0.0622; and at β=+5, where they clear tornado's noise floor, `Clq` -0.00635 against raw +0.00853, `Cnq` +0.0776 against raw -0.0489, `Cmr` +0.0838 against raw -0.0703. The p/r cancellation is confirmed from the other side by the existing `Clp`/`Cnr`/`Cmq` agreement. The remaining three rest on the rule alone: `Cm_P`'s one non-noise value disagrees with AVL by 5× in magnitude (a magnitude disagreement, not evidence about a frame), and AVL emits no `CZb`/`CXb` at all, so `CX_b`/`CZ_b` are structural — same channel as the already-confirmed `CX_a`/`CZ_a`, different invariant angle
- `Python/src/aid/axes.py`'s docstring no longer offers flow5's `CZa` as support for dropping the rate derivatives. `CZa` is an *alpha* derivative and constrains only the alpha entries; the rate derivatives are absent because `p`/`r` reverse while the p/r-flavoured channels reverse too, so the two cancel. That false argument was the stated rationale for ruling R17
- The "six rate derivatives are absent" restatement in `test_frd_sign_agreement.py` is gone. `test_damping_derivatives_still_agree` now says the cancellation is not universal and points at `test_pitch_rate_derivative_agrees_with_avl`, a new live cross-solver test that reads AVL's own `CZq` out of `geometry.sb` and asserts sign **and** a 0.5–2.0 magnitude band
- `test_axes.py` pins the map against the derivation itself (`derived_tornado_signs()`), as a set equality over every key `coeff_create` emits, so a channel nobody remembered cannot be missing and a no-op entry cannot survive either. `test_cy_and_cc_are_never_flipped` is rescoped: the `CY` **channel** and its flow-angle derivatives are never flipped, but `CY_P`/`CY_R` are, and the test now pins both halves. A new `test_no_other_solver_needs_a_pitch_rate_entry` records why tornado is the only map affected (flow5 emits `CYp`/`CYr` but no q-derivative; `datcom_parse._COEF_NAMES` extracts no rate derivative at all; AVL is native)
- `web/src/Results.tsx` labels from the **run**, not the editor. `const beta = aircraft == null ? 0 : aeroBeta(aircraft)` meant editing Beta after a run relabelled every curve to a condition the data was not flown at; it now reads `flownBeta(runPayloads)` off `payload.axes.beta`, which `_analyze_result` already fills from `_flown_beta` — no schema change was needed. A `(beta=0)` mark is a provenance claim, so `resultsView.test.ts` pins both directions: an editor-only sideslip must not relabel a β=0 run, and a flown sideslip must stay disclosed when the editor reads 0
- `web/src/aeroFigures.ts`'s Prandtl comment said the curve "never reads `AERO["BETA"]`, so it really is at the aircraft's sideslip" — inverted. `lifting_line`/`stability` take no beta, so it is **always** at β=0; the behaviour (left unmarked, it is a closed-form reference curve, not a solver run) is right and the reason is now stated so nobody reverts it
- `test_frd_sign_agreement.py`'s `betha` claim was two errors: `tornado_io.py:384` has read `math.radians(aero_beta(ac))` since Task 3.1, **and** Cessna 172 does carry `AERO["BETA"] = 0.0` explicitly, so the assertion is satisfied by a stated zero rather than by the key's absence. It is now guarded on the value, so giving the model a sideslip fails loudly instead of quietly mixing conditions
- `UPDATES.md:1.36.0` named a helper that does not exist: the flow5 β-flat guard is `test_gui_aero_beta.py::test_every_stab_derivative_flow5_emits_is_marked_beta_flat`, not `assert_all_flow5_stab_derivatives_labelled`
- **New known limitation, recorded not fixed: flow5's `Clb` is mesh-dependent.** On Cessna 172 at alpha = 4 deg it measures -0.0736 at mesh `('5','3')`, **+0.0018** at `('10','5')`, -0.0530 at `('10','10')` and -0.0593 at `('20','10')`, against AVL's -0.059 and Tornado's -0.054. At `('10','5')` it goes positive and `|Clb|` is ~30× too small, which reads as a sign flip rather than as a convergence failure. This is mesh convergence, **not** a frame error, and must not be map-flipped: it would break the good mesh. Both UIs default flow5 to `('10','10')` (`aid/mesh_params.py:13`, `api/aid_web/analyze.py:31`), where it agrees with AVL, so the default path is sound. Newly visible because 1.36.0 put flow5 on the C_ℓβ panel; `test_flow5_overlay_signs.py:164` and `test_flow5_derivatives.py:122` assert `Clb < 0` at one mesh only, so nothing warns a future maintainer

## 1.36.0 - One sign convention (Forward-Right-Down), flow5 lateral coverage, `AERO.BETA`
- `Python/src/aid/axes.py` is the **only** place in the repo where a solver sign is written down: `to_frd(solver, data)` / `from_frd(solver, data)` over measured per-channel maps for `datcom`, `tornado`, `avl`, `flow5`. A sign belongs there, never in a runner, parser or plot
- Every runner now returns Forward-Right-Down (x forward, y right, z down; roll right-wing-down, pitch nose-up, yaw nose-right) — `datcom_run.py:29`, `avl_io.py:328`, `flow5_io.py:133`, and the Tornado coefficients. Two deliberate exceptions, both later shown to be over-stated and corrected in 1.36.1: this entry said Tornado's `p`/`q`/`r` rate derivatives take **no** map entry (only the `p`/`r` ones do — `q` is about y, the axis the two frames share) and that `CY`/`CC` are never flipped by any solver (true of the channels, not of `CY_P`/`CY_R`). `datcom_controls.py` / `avl_controls.py` leave their control dicts raw on purpose
- `compare.py:265` applies `from_frd` to the Python leg before diffing raw MATLAB gold, so parity stays a real check instead of a tautology
- flow5 lateral coverage: the vendored helper now emits per-point `beta`, `CY`, `Cl`, `Cn`, `Cx`, `Cz`, `CDvis`, `CDind` plus twelve `StabDerivatives`, and `polar.beta_deg` genuinely reaches the solver through `Polar3D::setBetaSpec` (`polar3d.h:213`, read at `planetask.cpp:605`). flow5 was structurally absent from the lateral panels before; the design doc expected Deliverable 3's flow5 half might have to be deferred, and it was not. All twelve derivatives are finite — 629/629 in the suite, zero silent zeros
- `AERO["BETA"]` — sideslip in degrees, default `0.0` (`aid.aircraft.AERO_DEFAULTS`), read by Tornado and flow5, exposed in the PySide Aero tab, the API and the web app. Absent from `.mat`, `.jsonc` and a hand-built dict alike, and an absent value defers to the aircraft
- `(beta=0)` labelling is a property of the **channel**, not of the solver, and that distinction is load-bearing. DATCOM and AVL have no sideslip capability in their interfaces and stay at β=0 regardless. flow5 is split: its twelve `StabDerivatives` are frozen at β=0 because `computeStabilityDerivatives` and `computeAngularDerivatives` both hardcode `double beta(0.0)` (`panelanalysis.cpp:636,897`), while flow5's `CLa`/`Cma` are polar OLS slopes over the flown polar and therefore **do** follow β. `aid.solver_overlay.FLOW5_BETA_FLAT` names the flat twelve and `test_gui_aero_beta.py::test_every_stab_derivative_flow5_emits_is_marked_beta_flat` shouts if a 13th derivative is emitted unlisted. Getting this backwards makes the plot assert a provenance that is false. Labels go through `beta_zero_label` / `control_probe_label` (Python) and `betaSuffix` / `betaTitle` (web); each solver's payload `beta` is pinned to what it was actually run at
- Known limitations, not fixed: flow5's `CDvis` is identically `0` and `CDind` identically `CD`, because `flow5_run.cpp:301` calls `setViscous(false)` — the split is honest but degenerate, and nothing may present it as informative. A non-zero `AERO["BETA"]` is **not** a pure lateral perturbation in flow5: `betaSpec` rotates the mesh about the CG, shifting `CL` ~1.7% and `Cz` ~1.8%, so flow5's longitudinal channels must not be compared against DATCOM's or AVL's at β≠0
- Follow-ups deliberately left: `web/src/Results.tsx:617`'s fallback label needs a per-series β, i.e. a response-schema change; the flow5 β-flat guard warns rather than raises, and disables itself when the FLOW5 checkout is absent
- Pre-existing failures, not caused by this work — do not chase them: `test_naca456_ordinates[spec0|spec1]` and `test_project_docs` ×2 hardcode paths outside the repo (`Projects/FlightSimulation/USAF_DATCOM/naca456/`, `Projects/MDT/USAF_DATCOM/AircraftIntuitiveDesign`); `test_primary_all_solvers[DA20-C1|Learjet 23]` fail on Tornado **magnitude** with every sign matching; `test_e2e_primary` is downstream of those; `test_datcom_plot_cmp::test_sphere_...` is a gold/model shape mismatch; Navion's DATCOM SIGSEGVs and MATLAB's own gold records `failed`. Baseline `8 failed, 629 passed, 1 skipped`

## 1.35.1 - Beta=0 marks on the CL / C_m results panel
- `ResultsPanel.plot_stability` takes keyword-only `beta`, holds it on the widget, and labels the DATCOM and AVL series through `aid.solver_overlay.beta_zero_label`; the four bare `label="DATCOM"` / `label="AVL"` curves (CL and C_m, both vs-alpha plots) now read `"DATCOM (beta=0)"` / `"AVL (beta=0)"` when `AERO.BETA != 0`, and stay byte-identical at `BETA == 0`
- flow5's `CL`/`Cm` and Tornado keep their bare names: the polar forces and `state["betha"]` do follow the field. DATCOM and AVL have no sideslip capability at all
- `MainWindow._refresh_plots` hands the panel `beta=aero_beta(self.aircraft)`, the value `compare_tabs.plot` already took on the next line

## 1.35.0 - 15-point default alpha sweep
- `aid.alpha_schedule` adds `apply_alpha_default(ac)`; `ALPHA_POINTS = 15` is the density target. A sparse `AERO.ALSCHD` is refilled on the step ladder (`0.1`…`10.0`, the rungs DATCOM's `%.1f` `$FLTCON` carries exactly) to the count nearest 15, endpoints kept; a degenerate range collapses to one point, a 15-or-more input is left as stored, an absent key stays absent, and an envelope off the 0.1 grid gets no expansion at all rather than a lossy one
- Applied at all 10 Analyze entry points (5 in `aid_gui/main_window.py`, 5 in `aid_web/analyze.py`); the GUI's `_pre_solve_alpha_default` also mirrors it into the `AERO.ALSCHD` field, or the next `sync_fields_to_aircraft` reverts it, and `apply_units`/`apply_scale` re-read that field without disturbing it. Handbook and stability get no default
- Analyze → `File→Save` (`menus.py::_on_save`, unsynced by decision) persists the *expanded* schedule: byte-identical for the 18 rewritten models, but it normalises `T-38.jsonc`'s scalar `0` to `[0.0]` and the 4 int-valued models to floats — expect that diff when saving `T-38` or those 4 after a run
- 23 shipped models resampled: 18 rewritten, 4 already at 15+ and byte-identical, `T-38.jsonc` skipped (scalar `0`). Cessna 5 → 17, HK36 7 → 13, the other 16 rewritten 6 → 11
- Tornado solves one alpha, the upper-middle `ALSCHD` entry (`tornado_io.py:378`), so 6 → 11 moves it 4° → 6° on those 16 models and shifts their Tornado numbers. `test_compare_primary.py::test_primary_all_solvers[DA20-C1]` and `[Learjet 23]` compare Tornado against gold absent here, so they may newly fail once provisioned; `run_all.py`'s batch Tornado dumps move too. Navion and Cessna keep theirs, but Navion also asserts its DATCOM leg *fails*, and the gold pin can flip that
- Denser per-run work was accepted knowingly: DATCOM's `$FLTCON NALPHA` grows (`datcom_io.py:100`) and flow5 writes the whole `ALSCHD` (`flow5_io.py:79`), so the DATCOM and flow5 control legs — 2 paired solves per surface-delta, DATCOM skipping rudder — cost more. AVL's does not: `write_avl_control_case` hardcodes `A A 0` (`avl_controls.py:241`), one process per delta
- The gold check pins the fixture's 5-point sweep, because MATLAB's `cla`/`cma` are finite differences along the grid it is handed: at Cessna's shared alphas the 17-point sweep moves `cma` up to 7.7e-3 at α=8, 40% of the gold value there. `compare_to_matlab` flies the gold's `ALSCHD` for the DATCOM leg only; before, it passed just because shipped Cessna carried those 5 points. Regenerating the gold is the real fix, and needs the Windows MATLAB install
- `_compare_datcom`'s alignment branch is an identity on the production route, covered only by `test_datcom_gold_align.py`. Not dead code: it guards callers whose sweeps differ, and must never let sampling pass a mismatch
- Each solver entry in `Results/compare/<name>.json` records `alpha` and `alpha_source` (`gold` or `model`) — Cessna: datcom 5/gold, tornado and avl 17/model
- The 18 rewritten models write floats (`-4.0`) where the 4 untouched keep ints (`-9`) — `jsonc.py:53` via `json.dumps`, not drift, do not "fix" it — and now deliberately differ from `Matlab/fsroot/code/Models/*.mat`, which still hold the original 5-7 point schedules (Cessna `.mat` `[-4 0 4 8 12]` vs 17 points). `scripts/mat_to_jsonc.py` re-applies the default on conversion, so regenerating reproduces them
- Tests: `cd Python && PYTHONPATH=src python -m pytest tests -q`, `cd api && PYTHONPATH=../Python/src python -m pytest tests -q` (61 passed); Python's 17 failures are pre-existing, mostly missing `Results/` gold fixtures

## 1.34.1 - Saved results block hardening
- A `__proto__` solver name in a file's `results` block no longer replaces the parsed aircraft's prototype
- Tests guard the `results`-after-`unit` emit order and cross-check `api/aid_web/app.py`'s hand-written `Aircraft` constructor against `dataclasses.fields`

## 1.34.0 - Saved files carry analysis results
- Optional top-level `results` block in JSONC, `{solver, payload, raw}` per solver that ran; web Save omits it entirely when nothing ran
- Loading a file with `results` seeds `payloads`/`raws`, so the Aero overlays redraw without re-running a solver
- `aircraftForRequest` strips `results` from `/analyze`, `/models/validate`, `/stability`, and `/control-derivatives`
- `aid.Aircraft.results` and `aid/jsonc.py` carry it through load and save as an opaque dict, emitted without per-key doc comments; `GET /models/{name}` omits it when empty
- MATLAB is unchanged: `AID.m`'s save list still omits `Results`

## 1.33.2 - Handbook finish edge cases
- A zero-slope neutral-point error no longer aborts Tornado finish; CL and CD stay and plots refresh
- Trim mode 2 writes `HT.l` from X, x_ac, cbar, xmac, and XCG before the incidence solve
- Fuselage sketch Apply sets body area to `pi * ZU**2` at the new station count

## 1.33.1 - Tornado hooks after the inviscid save
- `MainWindow._finish_tornado` stores the inviscid Tornado dict before viscous strip, Cp paint, and neutral-point iteration
- A strip failure or `StaticMarginError` leaves `CL` and `CD` published

## 1.33.0 - handbook airfoil lateral dynamic tornado extras
- R1: `aid.naca456.ordinates` matches the Fortran `naca.gnu` ordinates
- R2: 4- and 5-digit NACA ordinates, vortex panel `a0`/`alpha0`/`Cm_ac`, and `section_slopes`
- R3: `aid.aero.aero` ports Aero.m through `x_ac` and `a *= pi/180`
- R4: `aircraft_cd0` is the handbook CD0, including the 1.25 interference factor once
- R5: trim mode 2 solves wing incidence, HT incidence, and angle of attack
- R6: `stamp_control_geometry` writes flap/elevator/rudder `tau`, flap `x_ac`/`l`, and aileron `Kb`
- R7: lateral-directional corrections, static derivatives, and dynamic derivatives
- R8: longitudinal dynamic `A`/`B` and short-period / phugoid roots
- R9: after Tornado, ask "Estimate Neutral Point?" offscreen never asks; Yes stores `results["N0"]`
- R10: Tornado Cp is painted on the 3D view; a geometry redraw clears it
- R11: Body tab Sketch opens the side/top fuselage editor; Adjust stays the station table
- R12: Calculations → Viscous Strip is off by default and stores `results["viscous"]` without replacing CL or CD
- R13: `apply_handbook` runs that sequence; Calculations uses it with `trim_fix='both'`

## 1.32.0 - AVL solved at each scheduled angle
- `run_avl_full` runs one AVL case per `AERO.ALSCHD` angle and returns totals and stability derivatives as arrays parallel to `alpha`
- Qt and web force, moment, and derivative charts plot those samples; AVL is not extended with `CLa` or any other slope
- MATLAB gold compare uses `ref`, the unconstrained OPER `x` (no `a a`) stored beside the sweep. For Cessna that printed alpha is about −1.90, not 0°. The plots use the `ALSCHD` samples only
- Tests: `cd Python && python -m pytest tests/test_avl_stack_cases.py tests/test_avl_write_case_sweep.py tests/test_avl_gold_sample.py tests/test_avl_run_cessna.py tests/test_solver_overlay.py -q` and `cd web && npm test`

## 1.31.1 - web AVL series color
- AVL coefficient lines and bars use magenta, the same marker color as the Qt overlay, so they no longer match DATCOM's default
- DATCOM stays the text color; Tornado stays red; flow5 stays yellow
- Tests: `cd web && npm test`

## 1.31.0 - control derivatives at a probe angle
- Handbook, DATCOM, Tornado, AVL, and flow5 return flap, aileron, elevator, and rudder slopes per degree at caller-chosen probes, including when the stored deflection is 0
- DATCOM has no rudder row (`datcom has no rudder namelist`)
- `POST /control-derivatives`; PySide Controls tab and the web results chart plot the probes
- Ordinary Analyze coefficients are unchanged

## 1.30.0 - web Aero coefficient tabs
- Web Aero tab plots the Qt coefficient categories from analysis raw on Forces, Moments, Derivatives, Downwash, Controls, Spanwise, and Sections
- Tornado spanwise and the Prandtl curve are included; handshake payload tables stay cl/cd/cm
- Tests: `cd web && npm test` and `cd web && npx tsc --noEmit`

## 1.29.1 - web API can import aid without a venv
- `./start-web.sh` puts `Python/src` on `PYTHONPATH` before uvicorn, so the fallback interpreter finds `aid` when `api/.venv` is missing
- Without that path the worker died with `ModuleNotFoundError: No module named 'aid'` and the start screen showed “API unreachable”
- Tests: `cd api && python -m pytest tests/test_start_web_script.py -q`

## 1.29.0 - web aerodynamics charts use axes and a grid
- CL, CD, and Cm vs α fill an axes box with numeric ticks and a grid, the same quantities the Qt plots show
- DATCOM no-data values (99999) are left off the scale so one sentinel cannot flatten the curve
- Tests: `cd web && npm test` (`payload.test.ts` chart layout, ticks, grid, sentinel scale)

## 1.28.0 - web geometry lofts airfoils, struts, and propeller
- Planforms use the PySide loft (`DATA` airfoil, quarter-chord, sweep, dihedral, incidence); wing, HT, and VT are sections instead of flat plates
- `NP` wing 2 is the strut pair; `NP` prop is the nose propeller, same axis map as `aid.viz`
- Opening a model frames the view on the aircraft (MATLAB `view(3)` direction) so the wing section, struts, and propeller are large enough to read
- Tests: `cd web && npm test` (`geom.test.ts` thickness, tail section, strut tip, propeller span)

## 1.27.0 - web geometry draws a solid body
- Body stations loft into closed sections (`R`, `ZU`, `ZL`; superellipse when `P` is not 1) and the Geometry view renders that skin, matching `Plot_Body`
- Tests: `cd web && npm test` (`web/src/geom.test.ts` elliptical section extents)

## 1.26.4 - start.sh uses PySide6 Qt plugins
- `./start.sh` sets `QT_PLUGIN_PATH` and `QT_QPA_PLATFORM_PLUGIN_PATH` to pip PySide6's plugins so xcb loads (conda `pigeon/bin/qt6.conf` points at Qt 6.7 plugins, which 6.11 rejects)
- Tests: `api/tests/test_start_web_script.py` (`test_start_sh_points_qt_plugins_at_pyside6`)

## 1.26.3 - start.sh reinstalls a stale editable aid
- `./start.sh` reinstalls `pip install -e Python` when `aid_gui` is missing or not this checkout (moved tree left a `pigeon` editable install pointing at `Projects/MDT/...`)
- Tests: `api/tests/test_start_web_script.py` (stale path reinstalls; matching path skips)

## 1.26.2 - README: web is CADAC sibling
- Idea/Architecture: `aid_gui` stays; `./start-web.sh` is the CADAC sibling (API :8002, Vite :5175). Quick start lists `api`/`web` tests.

## 1.26.1 - Analyze 400s, handshake error, cadacSession New
- `POST /analyze` maps `TimeoutExpired`, `ValueError`, `OSError`, `KeyError` (and prior `FileNotFoundError` / `CalledProcessError`) to HTTP 400 `{ok: false, error}`
- After Analyze, CADAC complete `!ok` or thrown fetch stores `handshakeError`; `lastPayload` / plots stay
- Non-empty `?cadacSession=` on first load calls `openNew()` (starter geometry GET still plan 5)
- Tests: `test_analyze_timeout_expired_is_400`; CADAC complete 500 / network error / success; `openNewIfCadacSession`

## 1.26.0 - AID web start-web.sh / kill-web.sh
- `./start-web.sh` kills any previous web instance then starts FastAPI :8002 + Vite :5175 (prefer `api/.venv`; PIDs in `.run/`)
- `./kill-web.sh` stop-only; re-run `./start-web.sh` to restart. Desktop PySide remains `./start.sh`
- README Running documents `./start-web.sh` and ports
- Tests: `api/tests/test_start_web_script.py` (ports 8002/5175; kill before start)

## 1.25.2 - analyzing generation token
- `runAnalyze` owns a generation token; `finally` clears `analyzing` only if this request still owns the in-flight analyze
- Field edits bump `revision` without stealing ownership, so Analyze re-enables after the request settles
- `openNew` / `openAircraft` still invalidate the token and clear the flag

## 1.25.1 - Results overlay axes + handshake JSON headers
- Overlay polylines share one domain per chart (`plotDomain`) so solvers compare on the same α/coeff scales
- `analyzing` always clears: `finally` on revision match; `openNew` / `openAircraft` reset the flag
- CADAC complete POST sends `Content-Type` and `Accept: application/json`

## 1.25.0 - AID web Results overlays + handshake
- Analyze button `POST /analyze` (DATCOM/Tornado/AVL/flow5); store `lastPayload` (overlays keyed by solver)
- `cadacCallbackUrl()`: `?cadacSession=` → `http://127.0.0.1:8001/handshake/sessions/${id}/complete`; after success `fetch(callback, { method: "POST", body: JSON.stringify(payload) })` with `source: "aid"`
- `Results.tsx` SVG CL, CD, Cm vs α; strokes DATCOM default, Tornado red, flow5 yellow; AVL uses default
- `POST /stability` `{aircraft}` → `aid.stability.aircraft_stability` dict; Results shows CG / static-margin text
- Geometry tab remains 3D; Aero tab right pane is Aerodynamics plots
- Tests: `web/src/cadacSession.test.ts`, `web/src/payload.test.ts`; `api/tests/test_stability.py` (Cessna live keys)

## 1.24.0 - AID web 3D Geometry view
- `web/src/geom.ts`: tessellate WG/HT/VT/BD to `{fuselage: polyline[], wings: {le, te}[]}`; `GeometryError`; `sceneFromConfig` `{ok:true, scene}` / `{ok:false, message}`; canvas `keepLastGood`
- `AircraftCanvas.tsx` R3F/drei: fuselage line segments + wing LE/TE meshes; Geometry tab plus right pane on form tabs
- Cessna WG `SSPN`/`CHRDR` fixture: geom span > 0; no PyVista numeric match
- Tests: `cd web && npm test` (`web/src/geom.test.ts`)

## 1.23.0 - AID web Extra + Control grids
- `+` ExtraTab: New Body / Propeller / New Wing / New HT / New VT fill `NB` 1×2 and `NP` 1×4 (pad `null`); Body 2/3, Prop, Wing 2, HT 2, VT 2 tabs when slots are dicts
- Load pads short `NP`/`NB`; adding Wing 2 writes `NP[0]` (CHRDR>0)
- Control: Flaps/Ailerons/Elevator/Rudder Inboard|Outboard from `CONTROL_BLOCKS` (`SPANFI`/`SPANFO`, …); no invented keys
- Tests: `cd web && npm test` (`web/src/extras.test.ts`)

## 1.22.1 - AID web chrome review fixes
- NACA blur keeps strings (`0012` not `12`); blank still `null`
- Recent local names stay listed and do not `GET /models/{name}`
- Validate failures use `validateError`; `ok: true` clears it (not `parseError`)
- Tests: `cd web && npm test`

## 1.22.0 - AID web React chrome
- `web/` Vite React 18 + Tailwind 3 (`darkMode: ["selector", ".dark"]`) + Zustand + Vitest; proxy `/models` `/analyze` → :8002; dev :5175
- Aircraft dict keys `WG, HT, VT, F, A, E, R, BD, NP, NB, AERO, plot_cmp, unit`; `aircraftFromJson` JSONC round-trip (Cessna `WG.CHRDR`)
- Field lists copied from PySide `PLANFORM_RP` / Control / Body stations / Aero (+ NACA); number fields commit on blur (`null` if blank)
- Start: New / Load examples / Open file (FileReader JSONC) / Recent (`aid-recent` last-5 names); theme `aid-theme` + `html.dark`
- Editor tabs Wing/HT/VT/Control/Body/Aero; Save downloads JSONC; no Extra `+` tab; r3f/three installed, no canvas yet
- Tests: `cd web && npm test`

## 1.21.0 - Analyze Tornado / AVL / flow5
- `POST /analyze` body `{aircraft, solver, mesh}`; omitted `solver` is `datcom` (Task 2 path unchanged)
- Tornado wraps `tornado_io` → `lattice_setup` / `set_boundary` / `solve` / `coeff_create` (default mesh `("10","5")`)
- AVL `run_avl_full`, flow5 `run_flow5`; default mesh `("10","10")`; AVL `CLtot`/`CDtot`/`Cmtot` map to mapper `CL`/`CD`/`Cm`
- Handshake `payload.solver` set to the requested solver; unknown solver or missing binary / `CalledProcessError` → HTTP 400 `{ok: false, error}`
- Tests: `api/tests/test_analyze_solvers.py` (monkeypatched solvers; no live Fortran/AVL/flow5)

## 1.20.0 - Analyze DATCOM mapper-shaped tables
- `POST /analyze` body `{aircraft}` runs `aid.datcom_run.run_datcom`; solver is datcom (Task 3 adds solver/mesh)
- Response `{ok, solver: "datcom", raw, payload}`: `raw` keeps the aid dict and adds mapper lists `{alpha, CL, CD, Cm, MACH}`; `payload` is handshake `{source: "aid", solver: "datcom", axes, tables: {cl, cd, cm}, ref: {}}`
- `to_handshake_payload(raw, mach)` (`payload_from_aid_raw` alias); NaN/Inf in leftover aid fields become JSON `null`
- `FileNotFoundError` / `CalledProcessError` → HTTP 400 `{ok: false, error}`
- Tests: `api/tests/test_analyze_datcom.py` (fixture + monkeypatch 400s + live Cessna skipif no wrapper)

## 1.19.0 - AID web API load/validate
- `api/` FastAPI package `aid-web` (editable `aid` from `../Python`, CORS 5173/5174/5175)
- `GET /models` lists `Python/models/*.jsonc` stems; `GET /models/{name}` returns `{ok, aircraft}` via `load_jsonc` + `asdict` (drop `cg_data` when None)
- `POST /models/validate` body `{aircraft}` → `{ok: true}` or `{ok: false, error}`; no bundled-model save
- Tests: `api/tests/test_load.py`

## 1.18.0 - run_flow5 Python wrapper
- `run_flow5_native`: temp deck JSON → `flow5_run --deck` → parsed stdout dict; `FileNotFoundError` if binary missing
- `run_flow5`: `write_flow5_deck` + `run_flow5_native` (replaces subprocess stub)
- `test_flow5_run_wrapper.py`: native vs wrapped CL/CD/Cm exact match on Cessna 172
- `test_e2e_flow5_cessna.py`: e2e spec — `allclose` atol=1e-6 on alpha/CL/CD/Cm, len(CL)==5

## 1.17.0 - flow5_run native PlaneTask solve
- `FLOW5/run/flow5_run.cpp`: full deck → foils/wings/`PlaneXfl`/`PlanePolar`/`PlaneTask` (T1 VLM2 inviscid); JSON from polar `getVariable`; minimal polar-only deck still returns zero skeleton
- `makePlane(false, true, false)` produces finite CL on Cessna 172 (10×10 mesh)
- `test_flow5_run_cessna_native.py`: asserts native CL not all zeros

## 1.16.0 - flow5_run JSON I/O skeleton
- `FLOW5/run/flow5_run`: CLI `--deck FILE` reads deck JSON, prints coefficient JSON (zeros of correct `alpha` length); usage → exit 2
- Vendored `nlohmann/json.hpp` v3.11.3; `FLOW5/run/CMakeLists.txt` builds executable with RPATH for `flow5-lib`/gmsh staging
- `test_flow5_run_cli.py`: usage exit 2 + deck skeleton JSON shape

## 1.15.1 - flow5-lib builds on Linux
- `FLOW5/flow5-lib/CMakeLists.txt`: OpenBLAS header compat, gmsh staging/download, `/usr/lib/x86_64-linux-gnu` link dirs, `TKXDESTEP`+`TKSTEP`, compile `gmesh_globals.cpp`
- `test_flow5_lib_builds.py`: asserts `FLOW5/build/.../libflow5-lib.so*` after cmake build
- `panelanalysis.cpp`: fix LAPACK `#elif`/`&info,)` typos blocking compile

## 1.15.0 - flow5 fourth solver (deck + GUI)
- Vendored GPL-3 flow5 under `FLOW5/` (`XFoil-lib`, `flow5-lib`, CMake superbuild); build with `cmake -S FLOW5 -B FLOW5/build`
- `write_flow5_deck`: AID JSONC → deck JSON (T1 VLM2, inviscid, thin surfaces, no fuselage); `run_flow5` invokes `FLOW5/run/flow5_run` subprocess
- Analyze menu → flow5; mesh dialog defaults 10×10; Stability/Aerodynamics overlays and Forces/Moments/Derivatives tabs plot flow5 when Analyze has run
- GPL-3 subprocess only — PySide does not link `flow5-lib`; no MATLAB gold for flow5; Cessna 172 e2e native vs AID `allclose` atol=1e-6 (`test_e2e_flow5_cessna.py`)

## 1.14.1 - Sections header contrast
- Column and group headers use dark bars with light bold 11pt text so they stay readable on dark KDE/Breeze themes

## 1.14.0 - Sections leftover table
- Sections leftover dump is a scrollable Qt table (not a matplotlib overlay): solver group headers, vector values in numbered columns, near-zeros shown as 0
- DATCOM section definitions stay a Wing/HT/VT grid above leftover when both exist

## 1.13.0 - Spanwise Tornado surface legend
- Spanwise tab labels each Tornado curve by surface (`Tornado Wing` / `HT` / `VT` / `Wing 2` / …) instead of `Tornado 2`
- Distinct linestyle and linewidth per surface (solid/dashed/dash-dot/dotted, decreasing width)
- `geo["name"]` set in `tornado_io`; `tornado_spanwise` stores it on each `{y, Cl}` series

## 1.12.0 - Python tabs match MATLAB field layout
- Wing/HT/VT/`+` extras: right-aligned labels, edit, unit suffix, gray breaks after MATLAB `xi`, visibility checkbox; NACA/DATA stay on Aero (and JSONC), not on planform
- Control: Flaps/Ailerons/Elevator/Rudder Inboard|Outboard grids (Span/Chord/Deflection); DATCOM-only extras (FTYPE, PHETE, Kb, …) no longer on the tab
- Body: Adjust, Station | Position | Shape table (11 rows; extra bodies 7 + X0/Y0/Z0), Circular Cross-Section; Shape cycles P like MATLAB
- Aero: same row style plus unit labels and CG Adjust / `%MAC` / slider; unit suffixes follow ft vs in

## 1.11.0 - File Recent submenu
- File → Recent lists the last 5 JSONC models (most recent first, filename label, full path tooltip)
- Recorded after File → Load and Help → Examples; re-open moves a path to the top; missing files are dropped
- Persisted in Qt QSettings (`AircraftIntuitiveDesign` / `AID`); tests isolate the store

## 1.10.3 - DATCOM elevator SPANFO clamp / AVL check_io retry
- Do not omit `$SYMFLP`/`$ASYFLP` solely because SPANFO > parent SSPN (DA20 elevator 4.7 vs HT 4.2764). Skip only SPANFO<=SPANFI or elevator when HT was omitted
- Unclamped DA20 elevator SIGSEGVs Digital DATCOM; write-time clamp SPANFO to parent SSPN (`DatcomInputWarning`); stored JSONC unchanged
- First gold mismatch after elevator restore was **Cm** from NX=24 vs stale 18-station MATLAB `datcom.json`; re-ran `run_aid_batch('DA20-C1','datcom')` (body_max=200). MATLAB batch still omits DA20 elevator (`SPANFI<0.01`); Python writes clamped elevator; compared CL/Cm/CD match
- GUI Analyze AVL with Inputs/Outputs calls `run_avl_full` (spacing retry), then previews the successful attempt’s `geometry.avl` / `geometry.run`

## 1.10.2 - DATCOM 80-col wrap / illegal HT omit / AVL spacing retry
- `_write_namelist_array` matches MATLAB `format_wrapped_array`: 10 values/line, wrap at 80 columns; BODY `body_max=200` (no 18-station downsample)
- Write-time omit DATCOM-illegal HT/VT (stored SSPNE<0, SSPNE>SSPN, zero area) and illegal `$SYMFLP`/`$ASYFLP` spans; JSONC unchanged; `DatcomInputWarning`
- AVL: if `geometry.st` missing, retry weighted-outboard (`sspace=-1.1`), equal span, then slightly finer/coarser nj
- Live 23: DATCOM 19/23 finite CL (new: Orbiter, Navion, 727, HK36, T-38, plus wrap-unblocked ASW-20/DA20/Rocket Prop/B-1/737/747). AVL 22/23 (T-34C CLa=5.073). Still NaN/Inf: SR-71, Enterprise, XB-70, X-Wing. Sphere VLM still body-only
- Sphere MATLAB `datcom.json` gold is from the old 18-station body; NX=200 CD differs until gold is re-run

## 1.10.1 - Isolate hotkey reaches PyVista interactor
- Event filter on the plotter widget (`QtInteractor` on-screen; key-accepting host offscreen) calls `isolate_from_key` and returns False so VTK still gets the key
- Test sends `QKeyEvent` via `QApplication.sendEvent` to `plotter_widget()`, not only `MainWindow.keyPressEvent`

## 1.10.0 - Context menu, isolate, background, profile sketcher
- 3D context menu: Reset Plot; View Side/Top/Front (MATLAB `view` az/el); Background Load/Hide/Flip/Rotate
- Isolate hotkey fades other components from the selected tab; Reset Plot restores visibility and `view(3)`
- Background tracing loads a PNG/JPG as an XZ back-plane actor (Hide removes it; replot keeps it)
- Body tab Adjust opens a station table (X, ZU, ZL, R, P); Apply writes `ac.BD` and replots
- Estimate CG actor pick and 5 px drag-gate unchanged

## 1.9.0 - Help Examples / Quick Start / control legend
- Help → Examples: `QFileDialog` at `Python/models/*.jsonc` (no `.mat`), then `load_aircraft` with `source_stem`
- Help → Quick Start: first-run dialog (Load/Examples, edit tabs, Analyze DATCOM/Tornado/AVL, Results Geometry/Stability/Aerodynamics) plus User's Manual button (`AID_Documentation.pdf`)
- Control legend is the MATLAB disabled Help labels (`Initialize_GUI.m` 198–216), not a stub; User's Manual unchanged

## 1.8.0 - Plus tab extra parts
- `+` buttons New Body, Propeller, New Wing, New HT, New VT fill `NP` 1×4 / `NB` 1×2 and add tabs Body 2/3, Prop, Wing 2, HT 2, VT 2
- Load recreates extra tabs when those slots are non-null (Cessna Wing 2+Prop, Enterprise Body 2); File New strips them
- Planform extras use the same fields as Wing/HT/VT; extra bodies match the Body tab plus X0/Y0/Z0; `cmp(5+)` checkboxes gate `plot_cmp` / viz
- New-wing winglet dialog (offscreen defaults No); defaults from MATLAB `addPart` (`L` from body length)
- Field keys `NP[i].` / `NB[j].`; Aero / Estimate CG unchanged

## 1.7.2 - Estimate CG pick ignores orbit drag
- Left-click pick defers until release; movement >5 px (orbit) does not open the weight dialog
- `left_clicking=True` and actor identity mapping unchanged

## 1.7.1 - Estimate CG pick, %MAC, recompute path
- 3D pick: `enable_mesh_picking(use_actor=True, left_clicking=True)`; map actor via `_mesh_actor_names`; no fallback to mesh 0
- `%MAC` no longer clamps mass-weighted XCG while Estimate CG is on
- `recompute_aero_cg` on `apply_field_edit` and when toggling Estimate CG on if the table has weight
- Extra-planform tips `NP{1}tip`/`NP{2}tip`/`NP{3}tip` map to columns 4–6

## 1.7.0 - Aero tab MATLAB AP + Estimate CG
- Aero tab: ZCG, XI, YI, wing root/tip NACA, tail NACA; `%MAC` checkbox and CG slider bound to `AERO.XCG` (MAC range vs body X)
- Estimate CG: 3×10 `ac.cg_data`, click-part numeric X/Z/weight dialog, mass-weighted `AERO.WT`/`XCG`/`ZCG` (apex offsets; plot_cmp gates extra parts)
- Settings Estimate CG also disables ZCG and hides the slider; 3D pick uses viz surface names (`wing`, `ht`, …)

## 1.6.0 - DATCOM/AVL input clamps
- `write_for005` clamps MACH>0.6 to STMACH 0.6, SSPNE<0.01 to 0.01, NDELTA to 9; stored JSONC `AERO.MACH` / planform / DELTA unchanged; `DatcomInputWarning`
- NACA cell `Data.` or a file path uses a later numeric code (Box → `NACA-W-4-2412`); no tabulated `$WGSCHR`
- Tornado/AVL skip NP{4} propeller; T-34C AVL still fails (cosine spanwise spacing, 0.2 ft tip panel)
- DATCOM wrapper copies `datcom.out` after binary SIGSEGV; `run_datcom` parses a finite table when present (T-34C)
- Live: F-16 DATCOM ok at written 0.6; Box DATCOM ok; T-34C DATCOM ok; SR-71 DATCOM still NaN at 0.6; Orbiter DATCOM still no α table (BODY line >80 cols / HT stub); Sphere body-only unchanged; plot_cmp gates kept

## 1.5.5 - Tornado PCHIP duplicate-x
- `_slope2` skips Δx=0 airfoil stations and replaces non-finite camber slopes; `_pchip_interp` unique-sorts finite x before SciPy PCHIP
- Box and ERAU DBF Plane Tornado (`tornado_io` → lattice → boundary → solve → coeff, mesh 10×5) return finite CL, CD, Cm
- Cessna Tornado gold unchanged (existing coeff / matlab-gold tests)

## 1.5.4 - Sphere DATCOM plot_cmp
- `write_for005` gates HT/VT/body on `plot_cmp` (indices 1, 2, 3); wing always, matching `DATCOM_IO.m`
- Missing/short `plot_cmp` pads True (same as Tornado `_cmp_enabled`)
- Sphere `[0,0,0,1]` omits `$HTPLNF`/`$VTPLNF`; Cessna still writes all three; Sphere DATCOM keys match MATLAB gold at 1e-6

## 1.5.3 - Control-tab deflections update 3D geometry
- `Plot_Planform.m` hinge rotation is now in `aid.viz`: nonzero flap/aileron/elevator/rudder δ adds F/A/E/R meshes and blanks the parent TE (MATLAB `mean(DELTA)`)
- Control (and other) field edits sync into the aircraft and replot the 3D view without resetting the camera
- Zero δ still draws the clean airframe only; DA20-style loaded deflections show on Open

## 1.5.2 - Empty comparison plots filled
- DATCOM `for005` always writes `$SYMFLP`/`$ASYFLP` (MATLAB parity), so Cessna cruise at δ=0 still gets a HIGH LIFT table
- Forces now include \(C_Y, C_N, C_A\) plus per-wing / AVL extras; Moments include \(C_\ell, C_n\)
- Controls plots DATCOM \(\Delta C_L/\Delta C_m/\Delta C_{Di}\) and hinge-moment extras; Tornado `C*_d` and AVL deflections when those solvers return them
- Sections lists leftover Tornado/AVL scalars (extra \(p,q,r\), \(C_{Ya}\), \(C_{Dwing}\), …) that are not on the vs-α axes
- Cessna Analyze DATCOM+Tornado+AVL: every comparison axis has data

## 1.5.1 - Comparison tabs fill the canvas
- Tab figures resize to the widget (no left-clustered 5×3 inch plot); subplots use tight margins
- Larger tick/label fonts; vs-α axes share DATCOM α limits so sparse CYB/CNB are not zoomed to one point
- Comparison tabs get more of the Aerodynamics pane than the handbook drag plot

## 1.5.0 - Aerodynamics solver comparison tabs
- Results → Aerodynamics keeps 3D + handbook drag; adds tabs Forces, Moments, Derivatives, Downwash, Controls, Spanwise, Sections
- Each tab overlays DATCOM (α table), Tornado (run α + slope), AVL (totals + slope) when that Analyze has been run; missing solvers omitted
- `parse_for006` now exports XCP, downwash (ε, dε/dα, q/q∞), high-lift increments, and wing/HT/VT section scalars
- Analyze AVL keeps run-case totals (`CLtot`, `CDtot`, `Cmtot`, α) beside ST derivatives
- DATCOM NDM/99999 derivatives plot as NaN, not spikes

## 1.4.4 - DATCOM transonic NaN warning
- Mach > 0.6 (DATCOM STMACH) uses transonic wing-body fairing; F-16 at 0.7 (and Cessna at 0.7) get `CLB/CL = NaN` so CL/Cm stay NDM — not a missed Mach edit
- Warning names STMACH 0.6 and tells the user to stay at Mach ≤ 0.6 for subsonic methods; crest-critical (~0.73) is a separate higher-Mach failure

## 1.4.3 - DATCOM method-limit warning
- Analyze DATCOM shows a **warning** (not a traceback or critical crash) when the solver has no method: crest-critical Mach exceeded, NDM/empty table, or similar `*** … EXCEEDED/ERROR/FATAL/INVALID ***` banners
- Cessna-style `NDM PRINTED` legends do not warn; coefficients still plot when the table is finite
- F-16 Mach 0.8: warning names crest-critical Mach 0.73 and that CL/Cm are NDM

## 1.4.2 - F-16 DATCOM NDM is an honest fail
- F-16 Analyze DATCOM no longer tracebacks: Mach 0.8 exceeds crest-critical (~0.73) so DATCOM prints NDM/NaN (MATLAB gold already `datcom: failed`)
- `parse_for006` raises `no finite coefficients (missing or ND)` when the stability table has no numeric rows; notes crest-critical Mach when present
- GUI Analyze DATCOM shows a dialog on empty/NDM tables instead of crashing
- Multhopp body method falls back to Gilruth-White when body stations skip the wing chord (`cr_exp<=0`; F-16 load divide-by-zero)

## 1.4.1 - DATCOM writer NPTS clamp
- `$WGSCHR` NPTS clamped to 60 (SECI `/IWING/`); `$HTSCHR`/`$VTSCHR`/extra planforms to 50. Downsample XCORD/YUPPER/YLOWER together, keep 0 and 1, so Analyze cannot hang on 100–500-pt sections
- Harness: 60s Linux `timeout` on `./datcom` (MATLAB `system` has no Timeout option); non-zero/timeout fails the case
- NACA cell fallback: warn when `NACA{1}` is a file path and a later numeric code is used (section DATA not sent; NACA card used instead)

## 1.4.0 - DATCOM MAXNX=200 / MAXNPTS=500 namelist
- Fortran `datcom.f`: body NX 20→200, airfoil namelist NPTS 50→500; COMMON overlays resized; rebuild `DATCOM/datcom.bin`. Analysis still uses the first 60 airfoil points (`SECI` `/IWING/`); 500-pt input is not used
- TBFUNX: `L=1` before the XA search so tabulated `$WGSCHR` no longer SIGSEGVs when X is below all XA(I)
- MATLAB writer: `body_max` 200, NACA cell fallback (737Max), `NPTS` real, `TYPEIN=1.0` on `$WGSCHR`, no 18-pt downsample
- Harness: NX=25 CM atol 2e-3 (DATCOM body pitching-moment quadrature vs station count, not interpolator round-trip); NX=160 / NPTS=60 / 737Max pass

## 1.3.1 - MATLAB DATCOM_IO section-limit writer
- `DATCOM_IO.m`: NACA cell fallback (`NACA{2}='2412'` → `NACA-W-4-2412`); no `$WGSCHR` when a numeric code exists (737Max)
- Body `body_max` 18→200; `write_namelist_array` no longer downsamples; wrap ≤80 cols, 10 values/line
- Tabulated `$WGSCHR` uses `datcom_airfoil_xy` and real `NPTS=%.1f` (same NPTS fix in `datcom_write_wgschr`)

## 1.3.0 - GUI MATLAB parity
- Wing Mesh Parameters dialog on Analyze Tornado/AVL; batch/compare unchanged (10×5 / 10×10, no dialogs)
- Initial 3D camera matches MATLAB `view(3)` nose-on
- Aerodynamics tab: 60/40 splitter; Prandtl lift overlay (+ Tornado red after Analyze)
- Settings menu live: plot options, scale, units, calculations, Estimate CG, error check / scroll sensitivity

## 1.2.8 - MATLAB DATCOM section-limit RED harness
- `datcom_interp_sections.m`: body/airfoil interpolators + raw `$BODY`/`$WGSCHR` writers (no 18-pt downsample)
- `test_datcom_section_limits.m`: Cessna baseline must pass; NX=25/160, NPTS=60, 737Max must fail on today's DATCOM (TDD RED)

## 1.2.7 - Wing Mesh Parameters dialog
- `MeshDialog` QDialog: `mesh_fields(ac, solver)` labels/defaults, OK/Cancel, `values()` after accept
- Analyze wiring deferred to Task 8

## 1.2.6 - Settings menu MATLAB defaults
- Settings menu enabled with checkable actions matching `Initialize_GUI.m` defaults (`SettingsState`, `Scale A/C Size` label)
- Toggle-only wiring; Scale/Units/plot behavior deferred to later tasks

## 1.2.5 - GUI DATCOM exposed span
- Python GUI Analyze DATCOM now applies `AID.m` wing-body interference: `SSPNE = SSPN - (R_LE+R_TE)/2` from body-radius spline at LE/TE
- Cessna Cm at α=12 matches MATLAB GUI (−0.129), not batch gold (−0.156); batch/compare still uses stored JSONC SSPNE
- Approximated vs DATCOM intersection now agrees with MATLAB GUI (~11–12°)

## 1.2.4 - Stability Cm legend
- Cm plot now has the same series legend as MATLAB (`AID.m` `legend(ax{3},lgnd)`); DATCOM at α=12 is −0.1558, handbook Approximated is −0.124

## 1.2.3 - GUI Tornado stability overlays
- Python Stability Tornado now matches `AID.m` Analyze: handbook trim α (not mid-`ALSCHD`), moments about 25% MAC, intercepts `CL0=CL-CL_a*α`
- DATCOM/AVL/Approximated overlay formulas already matched MATLAB gold; Cessna intercepts locked in tests
- Batch compare vs `run_aid_batch` unchanged (mid-`ALSCHD`, origin ref)

## 1.2.2 - Plot axis limits
- Aerodynamics drag: xlim stall–Vmax, ylim `[0, WT/3]` (AID.m); DATCOM CL plot uses same CL ylim as Stability
- Geometry 3D has no 2D axes (unchanged)

## 1.2.1 - Stability plot y-limits
- CL-α ylim `[-0.5, max(2, 1.1 CL)]`; Cm-α ylim MATLAB `Cmlim` (was ±100 from axis crosshairs)

## 1.2.0 - Results Geometry / Stability / Aerodynamics
- Left **Results** strip: Plot radios (Geometry, Stability, Aerodynamics) and Stability text (`CG at xx% MAC` / `Aircraft is yy% stable`)
- `aid.stability`: handbook CG fraction, neutral point, static margin, CL/Cm slopes, CD0 (Cessna: 37% MAC, 13% stable)
- Geometry = PyVista 3D; Stability = CL-α and Cm-α (DATCOM/Tornado/AVL overlays after Analyze); Aerodynamics = 3D + drag vs speed

## 1.1.0 - PyVista 3D aircraft view
- `aid.viz`: loft WG/HT/VT/BD/NP/NB from existing JSONC `DATA`/body stations (`Plot_Planform.m` / `Plot_Body.m`)
- `aid_gui.view3d`: pyvistaqt `QtInteractor` in the same splitter (VTK lighting, axes off); headless `Plotter` when `QT_QPA_PLATFORM=offscreen`
- matplotlib remains only on the CL-vs-alpha results pane
- deps: `pyvista`, `pyvistaqt`

## 1.0.6 - Python GUI fits screen height
- Tabs wrapped in `QScrollArea` so the Control form no longer forces a ~1254px window
- On show, size is 960×600 (or available screen if smaller) and centered
- `View3D` uses a 4×3 inch figure so matplotlib sizeHint does not inflate the splitter

## 1.0.5 - Python GUI start.sh
- Root `start.sh`: Anaconda `pigeon` env (`$HOME/anaconda/envs/pigeon`), `pip install -e Python` if needed, launch `aid`
- `README.md`: Quick start uses `./start.sh`

## 1.0.4 - MATLAB GUI edit-field contrast
- `AID.m` / `Initialize_GUI.m`: edit `ForegroundColor` black so DATCOM field values stay readable on white boxes under MATLAB dark desktop

## 1.0.3 - README credits for AID, DATCOM, Tornado, AVL
- `README.md`: Credits table with original project links (Lietzau AID File Exchange, PDAS Digital Datcom, Melin Tornado, Drela/Youngren AVL)

## 1.0.2 - MATLAB GUI DATCOM path
- `AID.m`: `lib_path` from `mfilename` (not `which('code/AID.m')`); `addpath` code/Tornado/AVL so Analyze DATCOM still finds `DATCOM_IO` after `cd` into `DATCOM/`; restore pwd on error

## 1.0.1 - README full project description
- `README.md`: solvers, dual MATLAB/Python architecture, aircraft schema, 23 models, package/GUI map, non-goals, GitHub URL — still names `UPDATES.md` and the spec reading order

## 1.0.0 - Python AID GUI and solver parity
- `Python/tests/test_e2e_primary.py`: MATLAB Cessna batch + subprocess primary compare/GUI smoke
- `README.md`: Quick start — MATLAB `run_aid_batch`, `pip install -e .`, `aid` launch, pytest suite command
- Release: PySide6 GUI (Tasks 53–61), Python DATCOM/Tornado/AVL engine parity vs MATLAB gold on primary four (Navion DATCOM honest fail retained)

## 0.10.0 - aid console entry point and Settings stubs
- `Python/pyproject.toml`: `[project.scripts] aid = "aid_gui.app:main"`
- `Python/src/aid_gui/app.py`: `QApplication.instance() or QApplication(sys.argv)`; show `MainWindow`, `app.exec()`
- `Python/src/aid_gui/menus.py`: Settings menu with spec §14 disabled stubs (Scale, Estimate CG, Plot Options, Calculations, Units, Inputs/Outputs, Error Check, Scroll Sensitivity)
- `Python/tests/test_gui_entry.py`: entry point metadata + `main` callable smoke test

## 0.9.1 - GUI Analyze AVL missing-binary dialog
- `Python/src/aid_gui/main_window.py`: `run_avl` catches missing/failed AVL subprocess; `QMessageBox.critical` with `avl_bin()` path (spec §15)

## 0.9.0 - GUI Analyze DATCOM wiring and results plot
- `Python/src/aid_gui/main_window.py`: `run_datcom`/`run_tornado`/`run_avl` call engine; `last_results`; missing-binary `QMessageBox.critical` with path; refuse Analyze without aircraft
- `Python/src/aid_gui/results_panel.py`: matplotlib `alpha` vs `CL` plot after DATCOM
- `Python/tests/test_gui_analyze_datcom.py`: Cessna load + `run_datcom()` asserts `cl` length ≥ 3

## 0.8.1 - 3D view equal aspect from data ranges
- `Python/src/aid_gui/view3d.py`: `_set_equal_aspect()` uses axis ptp tuple instead of unit cube; guards zero Z range

## 0.8.0 - GUI 3D planform view placeholder
- `Python/src/aid_gui/view3d.py`: matplotlib `FigureCanvasQTAgg` wing outline; `line_count()` for plotted segments
- `Python/src/aid_gui/main_window.py`: `QSplitter` tabs | 3D canvas; `load_aircraft` refreshes view
- `Python/pyproject.toml`: add `matplotlib` dependency
- `Python/tests/test_gui_view3d.py`: Cessna load smoke test (`view3d`, `line_count() > 0`)

## 0.7.1 - GUI load skips missing optional keys
- `Python/src/aid_gui/tabs.py`: `populate_from_aircraft` uses `dict.get`; missing BD/control keys leave fields empty
- `Python/tests/test_gui_tabs_cessna.py`: DA20-C1 load smoke test (no ITYPE KeyError)

## 0.7.0 - aid_gui geometry/aero tabs and JSONC load
- `Python/src/aid_gui/tabs.py`: Wing/HT/VT planform RP fields, Control (F/A/E/R), Body (BD), Aero (ALSCHD/ALT/MACH/WT/XCG), `+` stub; field registry + `clear_fields`
- `Python/src/aid_gui/main_window.py`: `field_value(dotted)`; `wing_chrdr_value` via registry
- `Python/src/aid_gui/menus.py`: File→Load/Save via QFileDialog + `load_jsonc`/`save_jsonc`; New clears fields
- `Python/tests/test_gui_tabs_cessna.py`: Cessna AERO.MACH and WG.SSPN load smoke test

## 0.6.0 - aid_gui Wing tab CHRDR field
- `Python/src/aid_gui/tabs.py`: Wing tab with `Root Chord` `QLineEdit` bound to `WG.CHRDR`
- `Python/src/aid_gui/main_window.py`: `load_aircraft`, `wing_chrdr_value`; central tab widget
- `Python/tests/test_gui_wing_chrdr.py`: Cessna 172 loads CHRDR=2 into Wing field

## 0.5.3 - aid_gui Help menu
- `Python/src/aid_gui/menus.py`: Help submenu with `Examples`, `Quick Start`, `User's Manual`, `control legend`; User's Manual opens `AID_Documentation.pdf` via `QDesktopServices`
- `Python/tests/test_gui_help_menu.py`: offscreen Help submenu action labels smoke test

## 0.5.2 - aid_gui Analyze menu
- `Python/src/aid_gui/menus.py`: Analyze submenu with `DATCOM`, `Tornado`, `AVL` wired to MainWindow stub slots
- `Python/src/aid_gui/main_window.py`: stub `run_datcom`, `run_tornado`, `run_avl` methods
- `Python/tests/test_gui_analyze_menu.py`: offscreen Analyze submenu action labels smoke test

## 0.5.1 - aid_gui File menu
- `Python/src/aid_gui/menus.py`: File menu with `New`, `Load`, `Save`; New clears `aircraft`; Load/Save stub slots
- `Python/src/aid_gui/main_window.py`: calls `build_menus(self)` after init
- `Python/tests/test_gui_file_menu.py`: offscreen File menu action labels smoke test

## 0.5.0 - aid_gui main window shell
- `Python/src/aid_gui/`: `MainWindow` — title `Aircraft Intuitive Design Tool`, 960×600, `self.aircraft = None`; thin `app.main()` stub (entry point in Task 61)
- `Python/tests/test_gui_window.py`: offscreen title/size smoke test

## 0.4.0 - run_all batch script
- `Python/scripts/run_all.py`: loop `models/*.jsonc`, `run_python`, write spec §12 `Results/python/<name>/` dumps + `status.json`, `compare_to_matlab`; `--aircraft` filter
- `Python/tests/test_run_all_summary.py`: Cessna 172 `status.json` exists with honest `datcom` status

## 0.3.36 - DATCOM compare parser precision
- `compare.py`: DATCOM `cl`/`cm` tables use `_PARSER_ATOL` (1e-6), same as `cd`/`cla`/AVL — removed 1e-3 table override per spec §13

## 0.3.35 - Navion/DA20 Tornado setrudder parity
- `lattice.py`: `_setrudder3` — rotate HP col 1 with TEP cols 0/5 in first loop; skip TEP/HP cols in second loop (avoids double-rotation; matches MATLAB wake/TEP parity on flapped nx=1 panels)
- Round 1 retained: `tornado_io.py` `_fc_chord_matlab`/`fsym`, `avl_io.py` dihedral + stale `.st` cleanup, `_geometry19` hp/tep1 prealloc
- Primary compare 4/4 pass (Navion DATCOM still expected fail)

## 0.3.34 - Navion/DA20 geometry parity (partial)
- `tornado_io.py`: `_fc_chord_matlab()` — MATLAB linear `geo.c` indexing for `fc`; `fsym` from `DELTAR` schedule matches matrix-`if` (Navion aileron)
- `avl_io.py`: cumulative dihedral correction per `AVL_IO.m`; remove stale `geometry.st`/`.sb` before run (DA20/Navion AVL CLa gold)
- `lattice.py`: preallocate hinge/TEP arrays in `_geometry19` (no `np.resize` on hp/tep1)
- Tornado coeffs still RED on Navion/DA20 (TEP1/VORTEX backfill on some flapped panels)

## 0.3.33 - compare harness MATLAB vs Python
- `Python/src/aid/compare.py`: `run_python`, `compare_to_matlab` — DATCOM/Tornado/AVL chain, spec §13 tolerances, `Results/compare/<name>.json`; DATCOM crash → `failed` not abort
- `Python/tests/test_compare_primary.py`: primary four; Navion expects `not report["datcom"]["pass"]`, tornado+avl pass (others all-three pass)
- `Python/src/aid/tornado/lattice.py`: `flap_indices()` — MATLAB `find(geo.flapped')` column-major order (fixes DA20 lattice crash)
- `Python/src/aid/tornado/boundary.py`, `tornado_io.py`: flap order + Navion `DELTAR` array asymmetric aileron

## 0.3.32 - avl_io Write_Case and run_avl
- `Python/src/aid/avl_io.py`: `write_case`, `run_avl`, `run_avl_full` — port `AVL_IO.m` `Write_Case` and `./avl < geometry.run`; chain `tornado_io` → `write_avl_geometry` → case → subprocess → `parse_st`
- `Python/tests/test_avl_run_cessna.py`: Cessna mesh `("10","10")` asserts `CLa` vs MATLAB `avl.json` gold (atol 1e-6)

## 0.3.31 - avl_io CDp from WG.CD0
- `Python/src/aid/avl_io.py`: `#CDp` uses `WG.CD0` if present else `0` (matches `run_aid_batch.m`, not component sum)
- `Python/tests/test_avl_write_geometry.py`: asserts `#CDp` line equals `WG.CD0` to `%.3f`

## 0.3.30 - avl_io write geometry.avl
- `Python/src/aid/avl_io.py`: `write_avl_geometry(ac, geo, state, run_dir, ni, nj)` — port `AVL_IO.m` `Write_Input`/`Write_Surface`; `geometry.avl` header (MACH, IYsym/IZsym, Sref/Cref/Bref, XCG/ZCG, CDp); cap `nwing` at 3; cosine mesh when `nelem>=4`; `AFILE` side files (`WG.1`, …); flap/aileron controls
- `Python/tests/test_avl_write_geometry.py`: Cessna mesh `("10","10")` asserts `geometry.avl` with `SURFACE`/`SECTION`

## 0.3.29 - avl_parse parseSB and parseRunCaseHeader
- `Python/src/aid/avl_parse.py`: `parse_run_case_header(path)` — port `parseRunCaseHeader.m`; case-insensitive `Run case:`; alpha/beta/Mach/rates/totals; surfaces after `e =` (`line+2`, letter names, angle after `=`)
- `Python/src/aid/avl_parse.py`: `parse_sb(path)` — port `parseSB.m`; case-insensitive geometry-axis header; CXu…Cnr; surface CXdN…CndN from header surfaces
- `Python/tests/test_avl_parse_sb.py`: gold `geometry.sb` smoke test (skips when file absent)

## 0.3.28 - avl_parse parse_st
- `Python/src/aid/avl_parse.py`: `parse_st(path)` — port `parseST.m`; case-insensitive stability-axis header; bounded `find_value` scan for CLa…Cnr, `Xnp`→`NP`; `surface=[]`
- `Python/tests/test_avl_parse_st_gold.py`: Cessna `geometry.st` asserts `CLa`/`Cma` vs MATLAB `avl.json` gold (atol 1e-6)

## 0.3.27 - avl_parse find_value
- `Python/src/aid/avl_parse.py`: `find_value(lines, name, area="")` — port `findValue.m`; substring scan, first parseable float after keyword; 0-based line index; optional `(start, end)` area tuple
- `Python/tests/test_avl_find_value.py`: SAMPLE `"CLa"` → `4.5123`, `ln == 1`

## 0.3.26 - tornado coeff_create3
- `Python/src/aid/tornado/coeff.py`: `coeff_create(results, lattice, state, ref, geo)` — port `coeff_create3.m` + inlines `tarea`, `fSonicCP`; body-to-wind `B2WTransform`; `delta=0.0001` derivatives; `FORCE`/`MOMENTS` shape `(n_deriv, 3)`
- `Python/tests/test_tornado_cessna_coeff.py`: Cessna mesh `("10","5")` asserts `CL` vs MATLAB `tornado.json` gold (`rtol=1e-4`, `atol=1e-5`)
- `Python/src/aid/tornado_io.py`: `_cmp_enabled` — indices beyond `plot_cmp` default enabled (MATLAB batch `cmp(5:8)` Value=1); restores NP wing in Tornado geo (`npan=178`, CL parity)

## 0.3.25 - tornado solver
- `Python/src/aid/tornado/solver.py`: `solve(state, geo, lattice)` — port `solver.m` + nested `fastdw`/`mega`; `numpy.linalg.solve(w2, RHS.T)`; no waitbar; `pgcorr==1` via `isa_atmosphere`; returns `gamma`, `F`, `FORCE`, `M`, `MOMENTS`, `dwcond`
- `Python/tests/test_tornado_solver_gamma.py`: Cessna mesh `("10","5")` asserts finite `gamma`

## 0.3.24 - tornado ISAtmosphere
- `Python/src/aid/tornado/isa.py`: `isa_atmosphere(alt)` — port `ISAtmosphere.m` SI table interpolation (m); returns `rho`, `a`, `p`, `mu`; SSL/out-of-range fallback
- `Python/tests/test_tornado_isa.py`: sea-level `rho > 0`

## 0.3.23 - tornado set_boundary
- `Python/src/aid/tornado/boundary.py`: `set_boundary(lattice, geo, state)` — port `setboundary5.m` (steady + FD columns α/β/P/Q/R, flap columns via `lattice_setup`); attaches `RHS` shape `(6+n_flaps, npan)` (= MATLAB `bc.T` for solver)
- `Python/tests/test_tornado_boundary.py`: Cessna mesh `("10","5")` asserts `RHS`/`rhs` key present

## 0.3.22 - tornado lattice_setup review fixes
- `Python/src/aid/tornado/lattice.py`: `_slope2` TYPE 3 odd pad `np.insert(data, nx, data[nx-1])` (MATLAB row NX duplicate); `_setrudder3` inclusive spanwise strip loop; hinge `a1`/`b1` `.copy()`
- `Python/tests/test_tornado_lattice.py`: `test_slope2_odd_pad_cessna_zu` for 101-point Cessna foil

## 0.3.21 - tornado lattice_setup
- `Python/src/aid/tornado/lattice.py`: `lattice_setup(geo, state, mode)` — port `fLattice_setup2.m` (`geosetup15`, `wakesetup2`, `setrudder3`, `geometry19` + inlines); `COLLOC`/`VORTEX`/`N`/`XYZ`, `ref` lengths; test aliases `npan`/`X`/`Y`
- `Python/tests/test_tornado_lattice.py`: Cessna mesh `("10","5")` asserts nonzero panels

## 0.3.20 - tornado_io MATLAB round and foil layout
- `Python/src/aid/tornado_io.py`: `_matlab_round` for HT/VT/NP half-mesh (`round(2.5)→3`); varying-airfoil `x`/`z` columns are span stations; `geo.foil` indexed `[wing][partition][0|1]`
- `Python/tests/test_tornado_io_cessna.py`: HT `nx=3`/`ny=5`, VT chord `nx=3` per partition

## 0.3.19 - tornado_io geo/state builder
- `Python/src/aid/tornado_io.py`: `tornado_io(ac, mesh)` — port `Tornado_IO.m` `Write_Geometry` + flight state (`AS`, `rho`, mid-`ALSCHD` alpha); `plot_cmp` component flags; zero-deflection empty CS
- `Python/tests/test_tornado_io_cessna.py`: Cessna 172 mesh `("10","5")` asserts `geo.c[0,0]==2`, `state.betha==0`, `AS>0`

## 0.3.18 - datcom_run subprocess runner
- `Python/src/aid/datcom_run.py`: `run_datcom(ac, workdir)` — `write_for005`, `datcom_wrapper` subprocess (`check=True`, `timeout=120`), `parse_for006`
- `Python/tests/test_datcom_run_cessna.py`: Cessna 172 end-to-end CL vs MATLAB `datcom.json` gold (atol 1e-6)

## 0.3.17 - datcom_parse for006 stability tables
- `Python/src/aid/datcom_parse.py`: `parse_for006(text)` — static-stability table (`ALPHA`/`CD`/`CL`/`CM`/derivatives), flight `mach`/`alt`; ND sentinel `99999` for blank `CYB`/`CNB`
- `Python/tests/test_datcom_parse_gold.py`: Cessna 172 `datcom.out` vs MATLAB `datcom.json` gold for `alpha` and `cl`

## 0.3.16 - datcom_io write_for005 orchestrator
- `Python/src/aid/datcom_io.py`: `write_for005(ac, path, *, unit)` — assembles full for005 (DIM IN when inches, CASEID, FLTCON/OPTINS/SYNTHS/BODY, NACA-W/H/V + WGPLNF/HTPLNF/VTPLNF, controls, PLOT/NEXT CASE); `naca_ht_line`, `naca_vt_line` helpers
- `Python/tests/test_datcom_writer_cessna.py`: Cessna 172 full-file assert CASEID, $FLTCON, $WGPLNF, NACA-W-4-2412, PLOT/NEXT CASE

## 0.3.15 - datcom_io write controls SYMFLP ASYFLP
- `Python/src/aid/datcom_io.py`: `write_symflp(pt, lines)` — `$SYMFLP` (9 RF fields, wrap after 4th, NDELTA/DELTA); `write_asyflp(pt, lines)` — `$ASYFLP` (5 RC fields, NDELTA/DELTAL/DELTAR); `write_controls(ac, lines)` — flap/aileron/elevator when deflections nonzero; skip elevator when `E.SPANFI<0.01` (DA20 batch)
- `Python/tests/test_datcom_controls.py`: Cessna 172 zero-deflection must not crash; no `PLOT`

## 0.3.14 - datcom_io write WGPLNF wing
- `Python/src/aid/datcom_io.py`: `write_wgplnf(pt, lines, label='')` — `$WGPLNF` planform namelist (11 RP fields, 4-per-line wrap, TYPE=1.0$); optional `label` for HT/VT; SSPNOP span-from-tip conversion without mutating `pt`
- `Python/tests/test_datcom_wgplnf.py`: Cessna 172 asserts `$WGPLNF`, CHRDR=2, SSPN=6

## 0.3.13 - datcom_io write BODY and NACA-W
- `Python/src/aid/datcom_io.py`: `write_body(ac, lines)` — `$BODY` from `BD` (NX cap 18 linspace downsample, 12+6 array lines, S precision from min(S)); `naca_wing_line(ac)` — `NACA-W-{len}-{code}` from first `WG.NACA`; shared `_write_namelist_array` helper
- `Python/tests/test_datcom_body.py`: Cessna 172 asserts `$BODY` and `NACA-W-4-2412`

## 0.3.12 - datcom_io write OPTINS and SYNTHS
- `Python/src/aid/datcom_io.py`: `write_optins(ac, lines)` — `$OPTINS` from `WG.S/cbar/b` (last element for list S/cbar); `write_synths(ac, lines)` — DATCOM-safe `$SYNTHS` (no YW/YH, keeps YV) from `AERO`, `WG`, `HT`, `VT`
- `Python/tests/test_datcom_synths.py`: Cessna 172 asserts `$OPTINS` SREF=24 and `$SYNTHS` XCG=2.94

## 0.3.11 - datcom_io write FLTCON namelist
- `Python/src/aid/datcom_io.py`: `write_fltcon(ac, lines)` — `$FLTCON` block from `DATCOM_IO.m` (NALPHA/ALSCHD wrap at 10, NALT/ALT, NMACH/MACH, WT, LOOP=2.0)
- `Python/tests/test_datcom_fltcon.py`: Cessna 172 asserts `$FLTCON`, MACH, ALSCHD endpoints

## 0.3.10 - drag.py CD0 port
- `Python/src/aid/drag.py`: `drag(pt, unit, atm, wg_sref)` — planform and fuselage CD0 from `Drag.m`; Reynolds from `atm["Re"]` or `D*MACH*a/V` (MACH default 0.03)
- `Python/tests/test_drag_cessna.py`: Cessna 172 wing CD0 vs `.mat` gold; ALT via `np.asarray` reshape (scalar squeezed from loadmat)

## 0.3.9 - geometry.py break-span branch
- `Python/src/aid/geometry.py`: break-span branch from `Geometry.m` lines 5–67 — segmented `S`/`AR`/`cbar`/`TR`, equivalent taper via quadratic (`b_quad` not span), weighted sweep/dihedral, tip/break locations
- `Python/tests/test_geometry_break_span.py`: weighted `cbar` and total `S` asserts for kinked planform

## 0.3.8 - geometry.py linear taper branch
- `Python/src/aid/geometry.py`: `geometry(pt, angl, type)` — single linear taper from `Geometry.m` else branch; sweep/MAC block; break-span raises (Task 30)
- `Python/tests/test_geometry_cessna_linear.py`: Cessna 172 gold `S=24`, `cbar=2`, `AR=6`

## 0.3.7 - atmosphere.py ISA port
- `Python/src/aid/atmosphere.py`: `atmosphere(h_ft)` — piecewise theta/delta/sigma from `Atmosphere.m`, keys `T,P,D,V,a`
- `Python/tests/test_atmosphere.py`: sea-level ISA asserts `T≈518.69`, speed of sound, `D>0`

## 0.3.6 - mat_to_jsonc all 23 models
- `Python/scripts/mat_to_jsonc.py`: batch `.mat` → `Python/models/*.jsonc` via `load_mat`/`save_jsonc`
- `Python/models/*.jsonc`: 23 aircraft JSONC source models (incl. `Cessna 172.jsonc`)
- `Python/tests/test_mat_to_jsonc_all.py`: asserts 23 `.mat` ↔ 23 `.jsonc`
- `Python/src/aid/jsonc.py`: serialize NaN/Inf as JSON `null` for valid comment-stripped parse
- `Python/src/aid/aircraft.py`: default missing `unit` to `"ft"` (matches `run_aid_batch.m`)
- `Python/src/aid/field_docs.py`: TYPE, e0, CL, XCG/ZCG/WT, spanwise.*, BD X0/Y0/Z0/d_eq

## 0.3.5 - dumps_jsonc comments on every key
- `Python/src/aid/jsonc.py`: `dumps_jsonc(data, docs)` — pretty-print with `//` on every dict key via dotted DOCS lookup (NP→WG, NB→BD fallbacks)
- `Python/src/aid/aircraft.py`: `save_jsonc(ac, path)`, `load_jsonc(path)` — write/read JSONC round-trip via `asdict` + `field_docs.DOCS`
- `Python/src/aid/field_docs.py`: top-level section keys (WG, HT, …) and control derived fields (F.S, F.tau, F.l, F.x_ac, E.S, E.tau, R.S, R.tau)
- `Python/tests/test_jsonc_comments_every_key.py`: Cessna save asserts every `:` line has `//`

## 0.3.4 - load_mat preserves 2-D airfoil DATA
- `Python/src/aid/aircraft.py`: non-column 2-D arrays → nested lists (N×2 `DATA`); column vectors still flatten (ALSCHD)
- `Python/tests/test_aircraft_load_mat.py`: asserts `WG.DATA` is 101×2 nested list

## 0.3.3 - aircraft.load_mat from MATLAB .mat
- `Python/src/aid/aircraft.py`: `@dataclass Aircraft` + `load_mat(path)` — scipy loadmat, recursive mat_struct→dict, NP/NB empty doubles→None, field `i` preserved
- `Python/tests/test_aircraft_load_mat.py`: Cessna gold asserts `unit`, `WG.CHRDR`, `AERO.ALSCHD`

## 0.3.2 - JSONC comment stripper loads_jsonc
- `Python/src/aid/jsonc.py`: `loads_jsonc(text)` — line-oriented `//` stripper respecting quoted strings, then `json.loads`
- `Python/tests/test_jsonc_loads.py`: asserts WG/unit fields parse from JSONC sample with inline comments

## 0.3.1 - JSONC field documentation catalog
- `Python/src/aid/field_docs.py`: `DOCS` dict (248 dotted paths) from spec §6.1–6.4 and `Initialize_GUI.m` labels; WG/HT/VT derived keys (`S`, `cbar`, `AR`, …)
- `Python/tests/test_field_docs.py`: asserts Cessna wing/aero keys including `"Root Chord"` in `DOCS["WG.CHRDR"]`

## 0.3.0 - aid.paths models_dir
- `Python/src/aid/paths.py`: `models_dir()` → `repo_root() / "Python" / "models"`
- `Python/tests/test_paths.py`: `test_paths_resolve` asserts path helpers including `models_dir().name == "models"`

## 0.2.0 - MATLAB gold Results/matlab for all 23 models
- `run_aid_batch_all.m`: batch driver over `Models/*.mat`; per-model `try/catch`; skip when `status.json` already has all three solver fields; writes `Results/matlab/_summary.json`
- `Python/tests/test_matlab_batch_all.py`: asserts 23 summary rows and per-model `status.json`
- Gold batch: 23/23 attempted; primary four honest (Cessna/DA20/Learjet three-way `ok`; Navion datcom `failed`, tornado+avl `ok`)

## 0.1.24 - Primary gold test expects Navion DATCOM failed
- `Python/tests/test_matlab_gold_primary.py`: per-aircraft `EXPECTED` map; Navion `datcom: failed` (Linux binary exit 139), tornado/avl `ok`; DA20-C1 and Learjet 23 all three `ok`

## 0.1.23 - Honest primary gold status and usable coefficients
- `run_aid_batch.m`: `gold_datcom_ok`/`gold_tornado_ok` reject ND (`99999`) and empty/NaN; record `datcom: binary exit N` on crash; delete stale JSON on failure
- `DATCOM/datcom`: restored `set -e` (no `|| true` on segfault)
- `DATCOM_IO.m`: skip batch elevator `SYMFLP` when `E.SPANFI<0.01`; body write uses local `body` struct (no global `BD` mutation); `write_namelist_array` capped at 12+6
- `fLattice_setup2.m`: sanitize NaN/`<=0` `geo.T` before chord extrapolation (fixes Navion/DA20 Tornado NaN lattice)
- `AVL_IO.m`: cosine spacing only when `geo.nelem(k)>=4` (not all multi-section); retains tip NaN/degenerate-section fixes
- Navion DATCOM: `failed` (binary exit 139 segfault); DA20-C1 and Learjet 23 all three `ok` with finite coefficients

## 0.1.22 - MATLAB gold primary aircraft (Navion, DA20, Learjet)
- `run_aid_batch.m`: default `solver='all'` runs DATCOM+Tornado+AVL sequentially; per-solver dispatch preserved
- `DATCOM/datcom`: copy `datcom.out` even when `datcom.bin` segfaults (Navion)
- `DATCOM_IO.m`: `$BODY` arrays chunked 12+6 (max 18 stations; decimate longer bodies); `write_namelist_array` helper
- `AVL_IO.m`: scalar `WG.S(end)` refs; NaN tip chord fallback; cosine spacing for multi-section wings; skip degenerate tip sections; empty `.st` guard
- `Python/tests/test_matlab_gold_primary.py`: asserts Navion, DA20-C1, Learjet 23 all three `ok` in `status.json`
- Gold runs: `run_aid_batch('Navion')` etc. → `Results/matlab/<model>/` (gitignored)

## 0.1.21 - MATLAB gold AVL dump for Cessna 172
- `Matlab/fsroot/code/run_aid_batch.m`: `run_avl_gold` — mesh `{'10','10'}`, `Tornado_IO`/`AVL_IO(...,false)`/`parseST`, merges `status.json` (preserves `datcom`/`tornado: ok`); deletes stale `geometry.st`/`.sb` before run
- `Matlab/fsroot/code/AVL_IO.m`: IYsym/IZsym/Zsym line uses `%d %d %.1f` (AVL 3.52 rejects `0.0 0.0 0.0`)
- `Python/tests/test_matlab_gold_cessna_avl.py`: asserts `avl: ok`, `CLa` in `avl.json`, `geometry.st` present
- Gold run: `run_aid_batch('Cessna 172','avl')` → `Results/matlab/Cessna 172/avl.json` (gitignored)

## 0.1.20 - MATLAB gold Tornado dump for Cessna 172
- `Matlab/fsroot/code/run_aid_batch.m`: `run_tornado_gold` — mesh `{'10','5'}`, `Tornado_IO`/`fLattice_setup2(geo,state,0)`/`solver`/`coeff_create3`, merges `status.json` (preserves `datcom: ok`)
- `Matlab/fsroot/code/Tornado/fLattice_setup2.m`, `coeff_create3.m`: R2025b `size()` loop-index fixes (`numel` / `size(...,1)`)
- `Python/tests/test_matlab_gold_cessna_tornado.py`: asserts `tornado: ok` and `CL`/`CD`/`Cm` in `tornado.json`
- Gold run: `run_aid_batch('Cessna 172','tornado')` → `Results/matlab/Cessna 172/tornado.json` (gitignored)

## 0.1.19 - DATCOM_IO batch DATCOM-safe SYNTHS
- `Matlab/fsroot/code/DATCOM_IO.m`: `$SYNTHS` branch matches `'batch'` as well as `'DATCOM'` (no YW/YH)
- `Matlab/fsroot/code/run_aid_batch.m`: `run_datcom_gold` calls `DATCOM_IO(...,'batch',...)` per plan
- `Python/tests/test_datcom_io_batch.py`: asserts batch uses DATCOM-safe SYNTHS condition

## 0.1.18 - MATLAB gold DATCOM dump for Cessna 172
- `Matlab/fsroot/code/run_aid_batch.m`: `run_datcom_gold` — load `.mat`, hidden `cmp`/`opt` stubs, `DATCOM_IO`/`./datcom`/`datcomimport`, JSON to `Results/matlab/<model>/`
- `Python/tests/test_matlab_gold_cessna_datcom.py`: asserts `status.json` `datcom: ok` and coefficient fields in `datcom.json`
- Gold run: `run_aid_batch('Cessna 172','datcom')` → `Results/matlab/Cessna 172/` (gitignored)

## 0.1.17 - run_aid_batch JSON strip helpers
- `Matlab/fsroot/code/run_aid_batch.m`: stub main (`error('not implemented')`); local helpers `onoff`, `write_json`, `strip_datcom`, `strip_tornado`
- `Python/tests/test_run_aid_batch_helpers.py`: asserts file exists and helper function declarations present

## 0.1.16 - AID.m Tornado NP batch default
- `Matlab/fsroot/code/AID.m`: NP `questdlg` skipped when `choice=='batch'`; default `np='No'`
- `Python/tests/test_aid_tornado_batch_np.py`: asserts batch guard around NP estimate dialog

## 0.1.15 - DATCOM_IO batch dialog defaults
- `Matlab/fsroot/code/DATCOM_IO.m`: `Write_DATCOM` skips `questdlg` when `choice=='batch'`; default `owg`, `cg_calc=0`
- `Python/tests/test_datcom_io_batch.py`: asserts explicit `strcmp(choice,'batch')` guard in DATCOM_IO.m

## 0.1.14 - AVL_IO.m Linux binary
- `Matlab/fsroot/code/AVL_IO.m`: else-branch calls `./avl` (Task 10 binary); removed macOS `DYLD_LIBRARY_PATH` setenv
- `Python/tests/test_avl_io_patch.py`: asserts `./avl` invocation, no `avl3.35` in file

## 0.1.13 - AID.m Linux DATCOM wrapper
- `Matlab/fsroot/code/AID.m`: non-Windows DATCOM branch calls `system('./datcom')` instead of `./datcom.osx`
- `Python/tests/test_aid_datcom_patch.py`: asserts Linux branch uses wrapper, not macOS binary

## 0.1.12 - AVL batch quit smoke
- `Python/tests/test_avl_smoke.py`: runs `avl` with stdin `PLOP\ng\n\nQuit\n`; asserts exit 0 within 30s (Task 10 binary; no X11 fix needed)

## 0.1.11 - AVL 3.52 binary install
- `Python/tests/test_avl_binary.py`: asserts `AVL/run/avl` exists and is executable
- Built `AVL3.52rel09032025/bin/avl` via `make -f Makefile.gfortranDP avl`, copied to `AVL/run/avl` (binary gitignored; reproduce locally)

## 0.1.10 - AVL eispack gfortran build
- `Python/tests/test_avl_eispack.py`: asserts `eispack/libeispack.a` (or `*.a`) exists after local build
- Built `eispack/libeispack.a` via `make -f Makefile.gfortran` (archive gitignored; reproduce locally)

## 0.1.9 - plotlib gfortranDP Linux X11 paths
- `plotlib/config.make.gfortranDP`: `LINKLIB`/`INCDIR` aligned with Task 7 Linux X11 (`/usr/lib/x86_64-linux-gnu`, `/usr/include`)
- `Python/tests/test_avl_makefile_linux.py`: asserts gfortranDP plotlib template has no macOS X11 paths

## 0.1.8 - AVL plotlib gfortranDP build
- `Python/tests/test_avl_plotlib.py`: asserts `plotlib/libPlt_gDP.a` (or `libPlt.a`) exists after local build
- Built `plotlib/libPlt_gDP.a` via `make gfortranDP` (archive gitignored; reproduce locally)

## 0.1.7 - AVL Makefile Linux X11 path
- `bin/Makefile.gfortranDP`: `PLTLIB` uses `-L/usr/lib/x86_64-linux-gnu -lX11` instead of macOS `/opt/X11`
- `plotlib/config.make`: `LINKLIB`/`INCDIR` pointed at Linux X11 lib and headers
- `Python/tests/test_avl_makefile_linux.py`: asserts no `/opt/X11` in gfortranDP makefile

## 0.1.6 - MATLAB gold scalar check for Cessna 172.mat
- `Python/tests/test_cessna_mat_gold.py`: loads `Models/Cessna 172.mat` via MATLAB `-batch`, asserts WG/AERO gold scalars

## 0.1.5 - Decode URL-encoded model .mat filenames
- Renamed 12 `Models/*.mat` files (`%20` → space) via `urllib.parse.unquote`
- `Python/tests/test_model_filenames.py`: asserts 23 models, no `%20` in names

## 0.1.4 - DATCOM smoke BODY fix and coefficient asserts
- `test_datcom_wrapper_smoke.py`: circular `$BODY` uses X+R only; tapered wing with SSPNE; assert coefficient table header in for006.dat

## 0.1.3 - DATCOM wrapper smoke test
- `Python/tests/test_datcom_wrapper_smoke.py`: runs `./datcom` with minimal namelist; asserts `for006.dat` contains CASEID and is >200 bytes

## 0.1.2 - DATCOM stdin wrapper script
- `Matlab/fsroot/code/DATCOM/datcom`: bash wrapper pipes `for005.dat` to `datcom.bin`, copies `datcom.out` → `for006.dat`
- `.gitignore`: stop ignoring wrapper; still ignore `datcom.bin`
- `Python/tests/test_datcom_wrapper.py`: asserts wrapper exists, references inputs/outputs, is executable

## 0.1.1 - DATCOM binary compile test
- `Python/tests/test_datcom_binary.py`: asserts `Matlab/fsroot/code/DATCOM/datcom.bin` exists and is executable (build locally from `../datcom/datcom.f` via gfortran)

## 0.1.0 - README, UPDATES, aid.paths bootstrap
- README.md and UPDATES.md per project-docs rule (idea, architecture, reading order)
- Python package skeleton: `pyproject.toml`, `src/aid/paths.py` (repo root discovery via `AID.m`)

## 0.0.1 - Project git repository
- Nested git repo at AircraftIntuitiveDesign (not the parent MDT repo)
- `.gitignore`: executables, objects, PDFs, Results, images, solver runtime output; keep source and aircraft inputs
