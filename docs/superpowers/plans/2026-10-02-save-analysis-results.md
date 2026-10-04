# Persist analysis results in saved aircraft JSONC

Goal: a file saved from the web UI (Save button) carries the analysis results of
every solver that was run, so `Analyses/Cessna172.jsonc` ends up holding all four
solvers (`datcom`, `tornado`, `avl`, `flow5`).

Approved in chat by the user on 2026-10-02. No spec file — this bounded design is
the authority.

## Global Constraints

These bind every task. Reviewers get them verbatim.

- **New top-level key, optional.** Exactly one new key, `"results"`, emitted after
  `"unit"`. Nothing else in the model format changes.
- **Shape.** `results` maps solver name to
  `{ "solver": <string>, "payload": <object>, "raw": <object> }`.
  `payload` is the handshake payload from `POST /analyze` (`source`, `solver`,
  `axes`, `tables`, `ref`). `raw` is the full `POST /analyze` `raw` object,
  including the Tornado lattice. Both are stored verbatim — no reshaping,
  no trimming, no key filtering.
- **Omit when empty.** When no solver has run, the `results` key is absent
  entirely — not `{}`, not `null`. Files saved without analyzing stay
  byte-identical to today's output.
- **Only solvers that ran appear.** A partial run writes a partial `results`.
- **Restoring.** Loading a file that has `results` repopulates the store's
  accumulated results so the Aero plots draw immediately.
- **Stale results survive edits.** Re-running one solver overwrites only that
  solver's entry. Editing geometry does not clear other solvers' entries, and
  re-saving writes them back. This matches the store's existing behaviour, where
  `payloads` / `raws` are not cleared on edit.
- **Defensive parse.** A `results` block that is malformed, empty, or of the wrong
  shape is ignored — `aircraftFromJson` returns the aircraft without `results` and
  does not throw. A malformed block must never make a model file unopenable.
- **Python preserves, does not interpret.** Python carries `results` through
  load and save as an opaque dict. It is not parsed into solver structures, not
  plotted, and not fed to any solver.
- **Opaque emission.** The `results` subtree is emitted without per-key doc
  comments. `aid/jsonc.py` requires a `field_docs.DOCS` entry for every nested key
  path, which opaque solver output cannot satisfy.
- **No regressions.** Every existing test that passes before this work still
  passes after. Geometry-only files keep their exact current shape.
- **No new documentation files.** Only `README.md` and `UPDATES.md` may be
  edited, and only in Task 6.
- **MATLAB is out of scope.** `AID.m:1543`'s save allow-list omits `Results` too,
  but MATLAB parity was explicitly not requested.
- **No "Run all four" button.** The user runs Analyze four times and saves.

## Task 1: Web model carries an optional `results` block

`web/src/aircraft.ts` gains the type surface; `web/src/aircraft.test.ts` gains the
tests. Write the tests first and watch them fail.

Add to `aircraft.ts`:

- `export type SavedSolverResult = { solver: string; payload: Record<string, unknown>; raw: Record<string, unknown> };`
- `results?: Record<string, SavedSolverResult>` on `AircraftDict`.
- `aircraftFromJson` parses `rec.results` defensively per the Global Constraints:
  a non-object, an empty object, an entry missing `solver`/`payload`/`raw`, or an
  entry whose values are not objects all cause that entry — or the whole block —
  to be dropped. It must not throw. A valid block is kept as-is.
- `aircraftToJson` emits `results` only when it is present and non-empty.
  `emptyAircraft()` gets no `results`.

Tests in `web/src/aircraft.test.ts` (follow the existing file's style and
assertion conventions):

1. A valid `results` block survives `aircraftFromJson` → `aircraftToJson`
   unchanged.
2. Absent `results` in → absent `results` out.
3. `results: {}` in → absent `results` out.
4. `results: null`, `results: "x"`, `results: []` → absent out, no throw.
5. An entry missing `payload` is dropped; the surviving sibling entries are kept.
6. An entry whose `payload` is an array is dropped; no throw.

## Task 2: Store restores results on load and exposes them for save

`web/src/store.ts` plus a new test file `web/src/resultsStore.test.ts`. Write the
tests first and watch them fail.

Behaviour:

- `openAircraft` seeds `payloads`, `raws`, `lastPayload`, and `handbook` from the
  loaded `results` block, per entry: `payloads[solver]` gets `payload`, `raws[solver]`
  gets `raw`. `lastPayload` gets the entry of the most recently saved solver —
  take the last key of the block in file order, which is the one the user saved
  last. Skip `handbook`: it comes from `POST /analyze` and has no stored
  counterpart, so it stays `null` after a load.
- `openAircraft` with no `results` block resets them to `{}` / `null`, exactly as
  today. Same for `openNew`.
- A new selector `resultsForSave()` returns the merged block: loaded entries plus
  entries from `payloads` / `raws`, with a freshly run solver winning over a
  loaded one for the same solver name. It returns `undefined` when the merge is
  empty, matching the "omit when empty" constraint.
- `aircraft.results` stays in sync is **not** required — the store keeps results
  in `payloads` / `raws`; `resultsForSave` is the single source for saving.

Tests: build a store, set an aircraft with a `results` block, call
`openAircraft`, assert `payloads` / `raws` / `lastPayload`. Assert
`resultsForSave()` returns all four solvers after four `runAnalyze` calls
(mock `postAnalyze`), returns `undefined` after a load with no block, and that a
re-run of one solver keeps the other three.

## Task 3: Save writes the `results` block into the download

`web/src/api.ts` and `web/src/Editor.tsx` plus tests. Write the tests first and
watch them fail.

- `downloadAircraft(aircraft, stem, results?)` takes the merged block and writes
  it into the serialized object via `aircraftToJson`. With `results` omitted or
  empty, the serialized bytes are identical to today's output.
- `Editor.tsx`'s Save button passes `store.getState().resultsForSave()`.

Test the serialized payload, not the DOM: assert on the object handed to the
`Blob` constructor (existing tests may already stub `Blob` / `URL`; follow them).

## Task 4: Python preserves `results` opaquely through load and save

`Python/src/aid/aircraft.py` and `Python/src/aid/jsonc.py`, plus a new test file
`Python/tests/test_aircraft_results.py`. Write the tests first and watch them
fail.

- `Aircraft` gains `results: dict | None = None` as the last field, so every
  existing positional or keyword construction keeps working.
- `_aircraft_from_dict` keeps `d.get("results")` when it is a non-empty dict;
  otherwise `None`. A malformed value becomes `None` rather than an error, matching
  the defensive-parse constraint.
- `save_jsonc` drops `results` when it is `None` or empty, so output for
  geometry-only aircraft is unchanged.
- `load_mat` sets `results=None`.
- `aid/jsonc.py`: in `_emit_dict_contents`, when the key path is exactly
  `["results"]`, emit the subtree with `json.dumps(..., indent=4)` behind a
  single `// Analysis results, keyed by solver` comment instead of recursing for
  per-key docs. Without this, `_lookup_doc` raises `KeyError` on the first opaque
  solver key.
- `Python/src/aid/field_docs.py`: no entry needed for `results`, because the
  opaque branch does not consult `DOCS`. Confirm this is true by test, not by
  reading.

Tests:

1. Load a fixture JSONC with a `results` block; `save_jsonc` it; reload; the
   `results` subtree compares equal to the original. Use a nested `raw` with at
   least three levels and mixed types, to prove nothing is dropped or reshaped.
2. `save_jsonc` on an aircraft with `results=None` produces a file whose text is
   byte-identical to the same aircraft saved before this change. Establish that
   baseline by checking out the pre-change `save_jsonc` output for
   `Python/models/Cessna 172.jsonc` first.
3. A `results` block containing `//`-looking content inside strings still reloads
   (the loader strips line comments; confirm opaque round-trip does not corrupt
   string values that contain `//`).
4. Malformed `results` (`null`, `[]`, `"x"`, `{}`) loads as `None`.

## Task 5: API preserves `results` across the HTTP boundary

`api/aid_web/app.py` plus `api/tests/test_load.py`. Write the tests first and
watch them fail.

- `aircraft_to_json` pops `results` when it is `None` or empty, so
  `GET /models/{name}` output for the 23 stock models is unchanged — no
  `"results": null` leaking into responses.
- `aircraft_from_json` passes `results=data.get("results")` through, so a
  round-trip through the API does not silently drop it.

Tests: `GET /models/{name}` for a stock model has no `results` key; an aircraft
with results passes through `aircraft_to_json` / `aircraft_from_json` unchanged.

## Task 6: Update `README.md` and `UPDATES.md`

No code. Update only these two files, per the project's documentation standard.

- `UPDATES.md`: new top entry. This is a feature, so bump the subversion. Read the
  current version at the top of the file first and bump from what is actually
  there.
- `README.md`: line 61's `web/` paragraph says "Save is client download." Extend it
  to state that the saved JSONC carries a `results` block with the `payload` and
  `raw` of every solver run, that the block is omitted when nothing ran, and that
  loading a file restores the results. Mention that Python preserves the key
  opaquely.

## Manual step (the user, not an agent)

After all six tasks land: run the web app, open Cessna 172, click Analyze four
times (DATCOM, Tornado, AVL, flow5), click Save, and place the download at
`Analyses/Cessna172.jsonc`. Confirm the file has a `results` block with all four
keys. Agents do not drive the browser.