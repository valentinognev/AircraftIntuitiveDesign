# Forward-Right-Down sign convention, and flow5 lateral coverage

## Problem

Coefficient overlays in `aid_gui/compare_tabs.py` and `web/src/aeroFigures.ts` draw
DATCOM, Tornado, AVL and flow5 on one axis without checking that the four solvers
agree on sign. They do not. Measured on B-1 Lancer at alpha = 6 deg:

| coefficient | DATCOM | Tornado | AVL |
|---|---|---|---|
| axial | `ca = -0.022` | `CX = -0.0418` | `CXtot = +0.0315` |
| normal | `cn = +0.577` | `CZ = +0.544` | `CZtot = -0.6175` |
| yaw moment (per rad) | `cnb = +0.117` | `Cn_b = -0.268` | `Cnb = +0.174` |
| roll moment (per rad) | `clb = -0.090` | `Cl_b = +0.020` | `Clb = -0.028` |

Three separate frame disagreements, reproduced on Cessna 172, Navion, DA20-C1,
Learjet 23 and F-16:

1. **AVL's axial and normal forces are mirrored.** AVL prints
   `Standard axis orientation, X fwd, Z down` in every `.st`
   (`Matlab/fsroot/code/AVL/AVL3.52rel09032025/src/aoutput.f`), so `CXtot = -CDtot`
   and `CZtot = -CLtot` exactly. DATCOM and Tornado are both aft-positive /
   up-positive.
2. **Tornado's roll and yaw moments are mirrored.** Its body frame is
   x **aft**, y right, z up, so `cross(r, F)` yields `Cl` left-wing-down and `Cn`
   nose-left. AVL and DATCOM are right-wing-down and nose-right.
3. **flow5 emits no lateral or axial data at all**, so most panels are
   structurally empty for it rather than wrong.

Root cause of (1) and (2) is that nothing in the repo records what frame each
solver reports in, so `compare_tabs.py:139-211` maps keys straight through.

Root cause of (3) is `FLOW5/run/flow5_run.cpp`: `polar_to_json` (line 349) reads
only `PlanePolar` variables 1 (alpha), 4 (CL), 5 (CD) and 9 (Cm), and line 284
calls `setComputeDerivatives(false)`, so `StabDerivatives` is never computed.

## Goal

Every solver's coefficients reach the plots, the API payload, the web overlay and
the Sections table in **one** convention, **Forward-Right-Down** (F-R-D): x
forward, y right, z down; moments roll right-wing-down, pitch nose-up, yaw
nose-right. That is AVL's native frame and the standard aerospace convention, so
AVL needs no change and MATLAB-gold parity stays checkable.

Two consequences worth stating plainly:

- **With `AERO.BETA = 0` (the default) flow5 stays longitudinal-only for the
  vs-alpha panels**, and that is the state Deliverable 2 ships. DATCOM's
  `$FLTCON` (`../datcom/datcom.f:1590`) has no sideslip variable and AVL's
  run-case menu (`atrim.f:292-302`) offers only bank/CL/velocity/mass/density/
  gravity/CG, so neither can be flown at beta != 0. A flow5 `CY` curve at
  beta = 5 deg would be the only non-zero lateral curve on the panel and would
  misrepresent the others, so Deliverable 3 keeps `BETA = 0` as the default and
  requires the `(beta=0)` label on DATCOM/AVL whenever it is not. flow5's value
  at the default is its **derivatives**, which are directly comparable.
- **Tornado's rate derivatives already agree** (`Cl_P` -0.486 vs AVL `Clp` -0.470;
  `Cn_R` -0.286 vs `Cnr` -0.212) and `Cm` is already standard. Only `Cl`/`Cn` and
  the roll/yaw **beta** derivatives flip. A blanket frame flip would be wrong.

## Measured conventions

Derived from each solver's own output, not from documentation, and each verified
against the identity that defines it.

| | AVL | DATCOM | Tornado | flow5 | handbook |
|---|---|---|---|---|---|
| axial (`CX`/`ca`) | **forward+** | aft+ | aft+ | aft+ (`Cx`, var 57, **flips**) | n/a |
| side (`CY`) | right+ | right+ | right+ | right+ (`Cy`, var 8, no flip) | right+ |
| normal (`CZ`/`cn`) | **down+** | up+ | up+ | up+ (`Cz`, var 58, **flips**) | n/a |
| roll (`Cl`/`cl`) | right-wing-down+ | same | **left-wing-down+** | `Cli()`: **left-wing-down+** (flips); `Clb`: right-wing-down+ (ok) | same |
| pitch (`Cm`) | nose-up+ | same | same | same | same |
| yaw (`Cn`/`cn`) | nose-right+ | same | **nose-left+** | `Cn()`: **nose-left+** (flips); `Cnb`: nose-right+ (ok) | same |

Evidence:

- **AVL** — `Results/python/B-1 Lancer/avl/geometry.st:12` prints the frame;
  `CZtot = -CLtot` and `CXtot = -CDtot` to all printed digits on every model
  checked.
- **DATCOM** — its table header is `ALPHA CD CL CM CN CA XCP` with **uppercase**
  CN and CA, i.e. forces (`datcom_parse.py:28`). Confirmed by the wind/body
  rotation holding exactly: `CL = CN*cos(a) - CA*sin(a)` and
  `CD = CN*sin(a) + CA*cos(a)` for Cessna 172 at alpha = 4 deg gives
  `0.516` and `0.037` against the printed `0.516` / `0.037`. Lowercase `cl`/`cnb`
  are moments and follow the standard. `XCP` is printed as `CM/CN`
  (`datcom.f:1010`, `INTERM` line 1010 of the `INTERM` subroutine) and is
  therefore **not** flipped by this change.
- **Tornado** — `coeff.py:80-95` builds `b2w` whose first row is the drag
  direction, so `CX = CD*cos(a) - CL*sin(a)` (verified: Cessna at alpha = 4 deg
  gives `-0.01946` against the printed `-0.01940`). With x aft, `cross()` in
  `tornado/solver.py:154` yields left-wing-down `Cl` and nose-left `Cn`. The
  `p`/`q`/`r` derivatives use the same cross product on rotation rates and land
  standard, which is why only the beta terms flip.
- **flow5** — **every channel that needs a flip gets one, and nothing already
  F-R-D is touched.** `Cx`/`Cy`/`Cz`/`Cli`/`Cn` (polar variables 57, 8, 58, 12,
  13) are all native non-F-R-D and all four *distinct* signs flip (`CY` is the
  exception: `Cy()` is already right-positive, and the whole `StabDerivatives`
  block is already F-R-D). So flow5's map is
  `{"Cx": -1, "Cz": -1, "Cl": -1, "Cn": -1}`.
  - `Cx()`/`Cz()` (`aeroforces.h:72,74`) are `m_Fff.x/S` and `m_Fff.z/S` in the
    frame x **aft**, z **up** — DATCOM's and Tornado's native frame, hence the
    `{"CX": -1, "CZ": -1}` / `{"ca": -1, "cn": -1}` entries in `_SIGN_MAP`.
    Settled by `Cx = CD·cosα − CL·sinα` holding to 1.3e-13 at all 17 alphas
    (aft-positive) and by `Cz(α=0, β=0) = CL(α=0) = +0.131536` to 4.8e-13 with
    positive lift (up-positive). An earlier draft of this bullet claimed these
    needed no flip by identifying them with Tornado's frame while ignoring the
    flip `_SIGN_MAP` already applies to Tornado; that argument is withdrawn.
  - `Cy()` (`aeroforces.h:73`) is `m_Fff.y/S` with `y` = **right**, which is
    already F-R-D and is why `CY` is never flipped.
  - `Cli()`/`Cn()` are **left-wing-down / nose-left positive**, i.e. the
    negatives of the F-R-D moments. `Cli()`/`Cni()` project `m_Mi` onto
    `m_CFWind.Idir()`/`Kdir()` (`aeroforces.cpp:84,120,52`) = `windDirection`,
    which is the **negative** of the stability axis `m_CFStab` is built with at
    `aeroforces.cpp:55`. Measured at alpha = 0, β = +5 deg:
    `Cli = +0.0047339` vs `Clb·β = −0.0046262`, `Cni = −0.0142629` vs
    `Cnb·β = +0.0147063`. The comments at `aeroforces.h:87-88` and `:97-98`
    ("starboard wing goes down is >0", "nose goes to starboard is >0") are
    **wrong**; do not trust them.
  - `StabDerivatives::{CYb, Clb, Cnb}` are already F-R-D (they project onto the
    stability axes `is`/`ks` at `panelanalysis.cpp:663-665`, applied at
    `:844-846`, and `stabderivatives.cpp:129-137` scales positively), and so are
    `CXa`/`CZa` (`CXa ≈ CL − dCD/dα` matches
    `Longitudinal_Dynamic_Stability.m:22`; `CZa ≈ −dCL/dα` is negative like
    `:35`).
- **handbook** — `Matlab/fsroot/code/Lateral_Static_Stability.m:100` yields
  `Cnβ > 0`, `Clβ < 0`, `CYβ < 0`, i.e. already F-R-D. No entry needed.

## Global Constraints

- Sign normalization happens in the **parsers**, not in the plots. `compare.py`
  applies the inverse map to the Python side before diffing raw MATLAB gold, so
  parity against `Results/matlab/*.json` stays a real check rather than a
  tautology.
- Parser entry points stay raw. `parse_for006`, `parse_st`, `parse_sb` and
  `parse_run_case_header` are compared key-for-key against gold in
  `test_datcom_parse_gold.py` and `test_avl_parse_st_gold.py`; only the
  `*_run` / `coeff_create` wrappers normalize.
- `CY` and `CC` are **not** flipped by anything. `CC` is already the wind-axis
  side-force coefficient (`coeff.py:104`).
- The raw solver vectors `F`, `M`, `FORCE`, `MOMENTS` are **not** flipped. They
  are solver internals, already excluded from the Sections table
  (`compare_tabs.py:522-534`), and `FORCE` is needed to rebuild `cp`. They are
  the one documented place the pre-normalization frame survives, and the API
  `raw` payload carries them.
- No coefficient changes value in magnitude. This is a sign change only.
- `AERO.BETA` is Python-only. `AID.m`'s save list is unchanged, the same
  treatment `cg_data` and `results` already get.
- flow5 keeps its OLS `CLa`/`Cma` keys so `test_e2e_flow5_cessna.py` does not
  move. `StabDerivatives::Cma` is asserted to agree with the OLS slope inside a
  tolerance instead of replacing it.

## Deliverable 1 — `aid/axes.py`

New module `Python/src/aid/axes.py`, the only place in the repo that encodes a
sign:

```python
_SIGN_MAP: dict[str, dict[str, int]] = {
    "avl": {},
    "datcom": {"ca": -1, "cn": -1},
    "tornado": {
        "CX": -1, "CZ": -1, "Cl": -1, "Cn": -1,
        "CX_a": -1, "CZ_a": -1, "Cl_a": -1, "Cn_a": -1,
        "Cl_b": -1, "Cn_b": -1,
        "Cl_P": -1, "Cl_Q": -1, "Cl_R": -1,
        "Cn_P": -1, "Cn_Q": -1, "Cn_R": -1,
        "CX_d": -1, "CZ_d": -1, "Cl_d": -1, "Cn_d": -1,
    },
    "flow5": {},
}

def to_frd(solver: str, data: Mapping) -> dict: ...
def from_frd(solver: str, data: Mapping) -> dict: ...
```

- `to_frd` returns a shallow copy with each listed key multiplied by its sign.
  Scalars and nested lists of floats are both handled; numpy arrays stay arrays.
- Keys not in the map are passed through by identity, including `surface`
  (a list of dicts), `high_lift` (a list of blocks) and `cp`.
- `from_frd` is `to_frd` with the signs inverted, and exists only for
  `compare.py`.
- An unknown solver name raises `KeyError` rather than silently passing through.

Call sites:

| file | where |
|---|---|
| `datcom_run.py:25` | wrap the `parse_for006` result with `to_frd("datcom", ...)` |
| `tornado/coeff.py` | `to_frd("tornado", out)` as the return value |
| `flow5_io.py:110` | `to_frd("flow5", ...)` |
| `avl_io.py:312` `stack_avl_cases` | `to_frd("avl", out)`, identity, kept for documentation |
| `compare.py:240` `_compare_coeffs` | `from_frd(solver, python)` before any key comparison |

The four control-derivative modules are **not** blanket-wrapped, because their
lateral keys come from different places:

| module | `CY` | `Cl` / `Cn` | action |
|---|---|---|---|
| `tornado/control_deriv.py:146-148` | `CC` (wind axis) | `coeffs["Cl"]`, `coeffs["Cn"]` | wrap with `to_frd("tornado", ...)` |
| `avl_controls.py:149` | AVL `.sb` `CYdN` | AVL `.sb` `CldN`/`CndN` | identity, documented |
| `datcom_controls.py:107-109` | `None` (guard at line 99) | `cl`/`cn` lowercase parser keys, already standard | identity, documented |
| `flow5_controls.py` | n/a until Deliverable 2 | n/a until Deliverable 2 | wrap in Deliverable 2 |

`handbook_controls.py` and `stability.py` are untouched — both already F-R-D.

## Deliverable 2 — flow5 lateral coverage

### Spikes (gate the rest of the piece)

Answered by Task 2.0; evidence in
`.superpowers/sdd/2026-10-03-frd-sign-convention-plan/task-2.0-report.md`.

1. **Can beta != 0 be driven from Python?** **GO** — via `PlanePolar`, not via
   the opp list. `PlaneTask::setOppList` (`planetask.cpp:107-111`) fills
   `m_AngleList` only, but `PlaneTask::run` reads beta for a T1 polar from
   `m_pPlPolar->betaSpec()` (`planetask.cpp:605`), and `Polar3D` exposes
   `setBetaSpec(double)` (`polar3d.h:213`, "The sideslip angle for type 1, 2, 4
   polars", `polar3d.h:277`). Measured: `setBetaSpec(5)` drives `Cy()` from
   `-6.7e-07` to `-0.0357` and flips sign under `setBetaSpec(-5)`. The mesh is
   rotated by `m_Beta` about the CG (`planetask.cpp:748`), not yawed, so the CG
   and reference frame are correct and the spec's rejected fallback is not
   needed. The deck key is still `polar.beta_deg` → `pPlPolar->setBetaSpec(...)`.
   *Caveat:* the `StabDerivatives` dump is **beta-independent** — every value is
   identical at beta = 0, +5 and −5 — because `computeStabilityDerivatives`
   builds its axes from `objects::windDirection(alphaeq, 0.0)`
   (`panelanalysis.cpp:660`). Derivatives must be labelled `(beta=0)`.
   Also confirmed: a `beta_deg` key in the deck is silently ignored today
   (byte-identical output), and *any* unknown key at any level is silently
   ignored — nlohmann does not reject unknown keys — while a **missing** required
   key aborts with SIGABRT (rc 134) on an assertion inside `json_number`.
2. **Does `computeStability` return finite numbers** for the locked
   thin-surface `VLM2` setup that `flow5_run.cpp:226` warns about? **GO** — all
   629 printed `StabDerivatives` values across all 17 Cessna opps are finite;
   zero NaN, zero silent `0.0`. At alpha = 0: `CYb = -0.4107 < 0`,
   `Clb = -0.0530 < 0`, `Cnb = +0.1685 > 0`, matching the prediction and AVL.
3. **Are `StabDerivatives::Clb`/`Cnb` standard or raw body-axis?** **GO —
   already standard F-R-D, no flip.** `computeTranslationDerivatives` projects
   the raw moment difference onto the *stability* axes
   `is = {-cosa,0,-sina}`, `ks = {sina,0,-cosa}` (`panelanalysis.cpp:663-665`,
   used at `:845-846`), and `stabderivatives.cpp:132,135` scale by a strictly
   positive factor. Confirmed against the measured signs.
   **The same file's `AeroForces::Cli()`/`Cni()` are the *negatives* of these**
   and need `{"Cl": -1, "Cn": -1}` if polar variables 12/13 are exposed
   (`planepolar.cpp:569-570`: `case 12: return AF.Cli();`,
   `case 13: return AF.Cn();`). The comments at `aeroforces.h:87-88` and
   `:97-98` ("starboard wing goes down is >0", "nose goes to starboard is >0")
   are **wrong**: `Cli()` projects `m_Mi` onto `m_CFWind.Idir()` =
   `windDirection(alpha,beta)` (`aeroforces.cpp:84`, `:52`), which is the
   *opposite* vector to the `is` used for `Lv`, because `m_CFStab` is set with
   `{-cosa,0,-sina}` (`aeroforces.cpp:55`). Measured at alpha = 0, beta = +5:
   `Cli() = +0.00473` where the physical roll moment is `Clb·beta_rad =
   -0.00463`, and `Cni() = -0.01426` where `Cnb·beta_rad = +0.01471`.
4. **Are `Cx`/`Cz` (polar variables 57/58) aft+/up+ or forward+/down+?** — i.e.
   does the `_SIGN_MAP`'s DATCOM/Tornado rule (`{"ca": -1, "cn": -1}`,
   `{"CX": -1, "CZ": -1}`) apply to flow5's `getVariable(57)`/`getVariable(58)`?
   **GO — flip both.** flow5's `AeroForces` reports *body-axis* components in a
   frame that is x **aft**, z **up** (`aeroforces.h:72-74`, `m_Fff.x/S`,
   `m_Fff.z/S`), which is **not** the F-R-D frame the rest of this document
   targets. It is the same frame as DATCOM's and Tornado's *native* output,
   which is exactly why `_SIGN_MAP` flips `ca`/`cn`/`CX`/`CZ` for those two
   solvers. An earlier draft of this item claimed no flip was needed; that
   argument was self-defeating — it identified flow5 with Tornado's frame and
   then drew the opposite conclusion from the rule this document already applies
   to Tornado. It is withdrawn. Settling numbers, all at alpha = 0, beta = 0:

   | channel | measurement | identity it settles | verdict |
   |---|---|---|---|
   | `Cx` (var 57) | `Cx = +0.0012434` at α=0 | `Cx = CD·cosα − CL·sinα` holds to **1.3e-13** at all 17 alphas, so `Cx` is the **aft-positive** axial component | flip (`-1`) |
   | `Cz` (var 58) | `Cz = +0.131536` at α=0 | `Cz = Fff.z/S` and `Cz(α=0) = CL(α=0) = +0.131536` to 4.8e-13, with positive lift ⇒ positive `Cz` ⇒ **z_geom up**, so `Cz` is **up-positive**. (The `Cz = CL` equality is the α=0 special case — `CL` is a wind-axis projection and `Cz` a body one, so they diverge with α, up to 1.2e-2 at α=12.) | flip (`-1`) |
   | `Cl` (var 12) | `Cli = +0.0047339` at β = +5 | opposite to `Clb·β = −0.0046262` | flip (`-1`) |
   | `Cn` (var 13) | `Cni = −0.0142629` at β = +5 | opposite to `Cnb·β = +0.0147063` | flip (`-1`) |
   | `CXa` | `+0.059466` | `≈ CL − dCD/dα` = `+0.059491` at α=0 | **no entry** |
   | `CZa` | `−5.256228` | `≈ −CLa − CD` = `−5.255571` at α=0 | **no entry** |

   `CXa` and `CZa` get no entry because each **is** the repo's own gold
   expression, measured, with the gold's sign:

   - `CXa` matches `Longitudinal_Dynamic_Stability.m:22`
     `CXa = AC.CL - AC.CDa;`. Measured residual `CXa − (CL − dCD/dα)` stays within
     `2.6e-6 … 2.6e-4` over the 15 interior points, i.e. ≤0.1 %.
   - `CZa` matches `Longitudinal_Dynamic_Stability.m:35`
     `CZa = -AC.CLa - AC.CD;`. Measured
     residual `CZa − (−dCL/dα − CD)` is **flat at −6.6e-4 … −5.7e-4** across all
     15 interior points, whereas the `CD`-less form `CZa − (−dCL/dα)` drifts
     monotonically from −0.0009 to **−0.0607**, tracking −`CD` (which runs
     0.00098 → 0.0602 over the sweep). The `CD` term is therefore **real and
     required**; the flat residual is just the second-order truncation
     difference between flow5's internal `deltaspeed = 0.001 m/s` finite
     difference and a pointwise central difference of the polar.

   Both are already **down-positive** as the gold consumes them — `:45`
   `Za = CZa*Q*WG.S(end)/m;` for `CZa`, and `:30` `Xa = CXa*Q*WG.S(end)/m;` for
   `CXa` — so raw flow5 `CZa` (negative, `−5.2562`) and raw `CXa` (positive,
   `+0.0595`) are already F-R-D and take **no entry**. The spec's provisional
   `{"CXa": -1, "CZa": -1}` is wrong in both directions: flipping `CZa` would
   take a correct negative to a wrong positive, and flipping `CXa` would break
   the one channel that already matches gold.

   Note `dCL/dα` is genuinely α-dependent over the sweep (`−dCL/dα` runs
   −5.248 at α=−4 to −4.947 at α=12), which is why the OLS
   `CLa = 5.1769701450913255` is 1.5 % off the *local* slope at α=0. Use the
   local slope when checking a per-point `CZa`; use the OLS `CLa` only when
   comparing to the gold's sweep-wide heuristic.

   **Open, and not load-bearing:** `Fff·is = −S·CD` holds exactly (α=0:
   `Fff·is = −0.0027724707751` vs `S·CD = 0.0027724708`), so algebraically
   `CXa` should carry **no** `CL` term — yet it measurably does. The
   `deltaspeed = 0.001 m/s` perturbation at `panelanalysis.cpp:655` is applied to
   a field of magnitude `u0 = 10.207 m/s` while `forces()` holds `QInf = 1.0`
   internally (`p3analysis.cpp:884`), so the perturbed RHS and the force
   normalisation are probably not scaled consistently, but this is **not
   proved**. It is **not** a blocker: `CXa` takes **no** `_SIGN_MAP` entry, so an
   unexplained additive term cannot affect any sign, and
   `d(CD)/dα`-only variants of `CXa` are not exposed anywhere. Left open
   deliberately; changing `FLOW5/` physics is a Non-goal. Full numbers in
   `.superpowers/sdd/2026-10-03-frd-sign-convention-plan/task-2.0-report.md`.

**Revised flow5 sign map: `{"Cx": -1, "Cz": -1, "Cl": -1, "Cn": -1}`.** Nothing
else in flow5's map flips. Note the two *pairs* flip for opposite reasons and
must not be collapsed: `Cx`/`Cz` flip because of the **force** frame
(x aft / z up vs F-R-D), `Cl`/`Cn` flip because of a **sign error** in flow5's
own `AeroForces` moment projection relative to its `StabDerivatives`.

### C++ changes

`FLOW5/run/flow5_run.cpp`:

- line 284: `setComputeDerivatives(false)` -> `true`, plus
  `setKeepOpps(true)` (`Task3D`) so `planeOppList()` is populated after `run()`.
- after `pPlaneTask->run()`, read the stored `PlaneOpp` list and emit its
  `StabDerivatives`: `CXa`, `CZa`, `Cma`, `CYb`, `CYp`, `CYr`, `Clb`, `Clp`,
  `Clr`, `Cnb`, `Cnp`, `Cnr`, `XNP`. Take them from the **alpha = 0** point (or
  the point nearest it), not the whole sweep, and label them `(beta=0)`.
- `polar_to_json` additionally emits the per-point variables it never read:
  `2` Beta, `6` CDviscous, `7` CDinduced, `8` CY, `12` Cl, `13` Cn.
- deck gains optional `polar.beta_deg`, default `0.0`, applied as
  `pPlPolar->setBetaSpec(beta_deg)` (spike 1). `getVariable(2)` then returns
  the sideslip actually flown, which is the round-trip assertion for Task 2.1.
- `skeleton_output` (line 299) gains the same keys so the failure path keeps the
  schema.

`FLOW5/flow5-lib/objects3d/analysis3d/planepolar.cpp`:

- `getVariable` ends at `case 56` on line 651, so `case 57: return
  m_AF.at(index).Cx();` and `case 58: return m_AF.at(index).Cz();` are free.
  **Both are wanted** — spike 4 settled their signs (`Cx` aft+, `Cz` up+, both
  flipping) — so keep this block. `s_VariableNames` (line 509) gains the
  matching two entries (`"Cx"`, `"Cz"`) so `listVariable` stays aligned.
  Caveat for Task 2.1's tests: `Cx` is a body-axis *projection*, so it goes
  negative at sideslip (`Cx = −0.000914` at β = 5 deg while `CD = +0.002197`)
  and is not a drag coefficient. Assert its sign at β = 0 only.

Python:

- `write_flow5_deck(ac, mesh, beta=0.0)` writes `beta_deg`.
- `run_flow5(ac, mesh, beta=0.0)` passes it through.
- flow5's sign map entry becomes
  `{"Cx": -1, "Cz": -1, "Cl": -1, "Cn": -1}` (spikes 3/4). Nothing else in
  flow5's map flips — `CY` and all `StabDerivatives` keys pass through.

Build: `cmake --build FLOW5/build -j 28` (the tree already exists; only
`flow5_run.cpp` recompiles plus a relink — `planepolar.cpp` is untouched).

## Deliverable 3 — `AERO.BETA`

- `Aircraft` gains `AERO["BETA"]` in degrees, default `0.0`, as a JSONC key with
  a comment (`aid/jsonc.py` requires a comment on every key, enforced by
  `test_jsonc_comments_every_key.py`). Not written by `AID.m`.
- PySide Aero tab: a `Beta (deg)` number field, committed on blur, `null` when
  blank, laid out like the existing `AERO` rows.
- Web Aero tab: same field; `api/aid_web/analyze.py` accepts `beta` on
  `POST /analyze` and `POST /stability`.
- Tornado: `tornado_io` / the GUI set `state["betha"] = radians(beta)`.
- flow5: `run_flow5(..., beta=beta)`.
- DATCOM and AVL: unchanged, they stay at beta = 0. When `AERO["BETA"] != 0`,
  `compare_tabs.py` and `web/src/aeroFigures.ts` append ` (beta=0)` to the
  DATCOM and AVL series labels so a mixed condition is visible rather than
  silent.

## Non-goals

- Changing DATCOM methods, AVL theory, Tornado's physics or flow5's solver. The
  `wind1` freestream expression in `tornado/solver.py:149-153` (a transcription
  of `Matlab/fsroot/code/Tornado/solver.m:131`, missing its `sin(betha)`
  y-component) is a separate finding and is **not** touched here.
- Rotating the raw solver vectors `F`/`M`/`FORCE`/`MOMENTS`.
- Adding a sideslip capability to DATCOM or AVL, which their interfaces do not
  have.