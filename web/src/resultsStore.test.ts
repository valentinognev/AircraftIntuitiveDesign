import { afterEach, expect, it, vi } from "vitest";
import type { SavedSolverResult } from "./aircraft";
import type { HandshakePayload } from "./payload";
import { createStore } from "./store";

const SOLVERS = ["datcom", "tornado", "avl", "flow5"];

afterEach(() => {
  vi.unstubAllGlobals();
});

it("openAircraft seeds payloads and raws from the loaded results block", () => {
  stubFetch();
  const store = createStore();
  const saved = {
    tornado: savedResult("tornado", 1),
    avl: savedResult("avl", 1),
    datcom: savedResult("datcom", 1),
  };
  store.getState().openAircraft(withResults(saved), "mine.jsonc");
  expect(store.getState().payloads).toEqual({
    tornado: saved.tornado.payload,
    avl: saved.avl.payload,
    datcom: saved.datcom.payload,
  });
  expect(store.getState().raws).toEqual({
    tornado: saved.tornado.raw,
    avl: saved.avl.raw,
    datcom: saved.datcom.raw,
  });
});

it("lastPayload after a load is the last key of the block in file order", () => {
  stubFetch();
  const store = createStore();
  const saved = {
    tornado: savedResult("tornado", 1),
    avl: savedResult("avl", 1),
    datcom: savedResult("datcom", 1),
  };
  store.getState().openAircraft(withResults(saved), "mine.jsonc");
  expect(Object.keys(store.getState().payloads)).toEqual(["tornado", "avl", "datcom"]);
  expect(store.getState().lastPayload).toEqual(saved.datcom.payload);
});

it("a load leaves handbook null and restores the aircraft results block", () => {
  stubFetch();
  const store = createStore();
  const saved = { datcom: savedResult("datcom", 1) };
  store.getState().openAircraft(withResults(saved), "mine.jsonc");
  expect(store.getState().handbook).toBeNull();
  expect(store.getState().aircraft!.results).toEqual(saved);
});

it("a load with no results block resets payloads, raws, lastPayload, and handbook", () => {
  stubFetch();
  const store = createStore();
  store.getState().openAircraft(withResults({ datcom: savedResult("datcom", 1) }), "a.jsonc");
  store.getState().openAircraft(baseAircraftJson(), "b.jsonc");
  expect(store.getState().payloads).toEqual({});
  expect(store.getState().raws).toEqual({});
  expect(store.getState().lastPayload).toBeNull();
  expect(store.getState().handbook).toBeNull();
});

it("openNew clears results restored by a previous load", () => {
  stubFetch();
  const store = createStore();
  store.getState().openAircraft(withResults({ datcom: savedResult("datcom", 1) }), "a.jsonc");
  store.getState().openNew();
  expect(store.getState().payloads).toEqual({});
  expect(store.getState().raws).toEqual({});
  expect(store.getState().lastPayload).toBeNull();
});

it("resultsForSave returns all four solvers after four Analyze clicks", async () => {
  stubFetch();
  const store = createStore();
  store.getState().openNew();
  for (const solver of SOLVERS) await store.getState().runAnalyze(solver);
  const block = store.getState().resultsForSave();
  expect(Object.keys(block!)).toEqual(SOLVERS);
  expect(block!.datcom).toEqual(savedResult("datcom", 1));
  expect(block!.tornado).toEqual(savedResult("tornado", 1));
  expect(block!.avl).toEqual(savedResult("avl", 1));
  expect(block!.flow5).toEqual(savedResult("flow5", 1));
});

it("resultsForSave is undefined when nothing ran and nothing was loaded", () => {
  stubFetch();
  const store = createStore();
  expect(store.getState().resultsForSave()).toBeUndefined();
  store.getState().openNew();
  expect(store.getState().resultsForSave()).toBeUndefined();
  store.getState().openAircraft(baseAircraftJson(), "b.jsonc");
  expect(store.getState().resultsForSave()).toBeUndefined();
});

it("re-running one solver keeps the other three and the fresh run wins", async () => {
  stubFetch();
  const store = createStore();
  store.getState().openNew();
  for (const solver of SOLVERS) await store.getState().runAnalyze(solver);
  await store.getState().runAnalyze("datcom");
  const block = store.getState().resultsForSave();
  expect(Object.keys(block!)).toEqual(SOLVERS);
  expect(block!.datcom).toEqual(savedResult("datcom", 2));
  expect(block!.tornado).toEqual(savedResult("tornado", 1));
  expect(block!.avl).toEqual(savedResult("avl", 1));
  expect(block!.flow5).toEqual(savedResult("flow5", 1));
});

it("resultsForSave merges loaded entries with the freshly run ones", async () => {
  stubFetch(2);
  const store = createStore();
  const loaded = { datcom: savedResult("datcom", 1), flow5: savedResult("flow5", 1) };
  store.getState().openAircraft(withResults(loaded), "a.jsonc");
  await store.getState().runAnalyze("datcom");
  const block = store.getState().resultsForSave();
  expect(Object.keys(block!)).toEqual(["datcom", "flow5"]);
  expect(block!.datcom).toEqual(savedResult("datcom", 2));
  expect(block!.flow5).toEqual(loaded.flow5);
});

it("resultsForSave omits an entry whose raw is not an object", () => {
  const store = createStore();
  store.setState({ payloads: { datcom: handshake("datcom", 1) }, raws: { datcom: "not an object" } });
  expect(store.getState().resultsForSave()).toBeUndefined();
});

function baseAircraftJson(): Record<string, unknown> {
  return {
    WG: { CHRDR: 2 },
    HT: {},
    VT: {},
    F: {},
    A: {},
    E: {},
    R: {},
    BD: {},
    NP: [null, null, null, null],
    NB: [null, null],
    AERO: {},
    plot_cmp: [1, 1, 1, 1],
    unit: "ft",
  };
}

function withResults(results: Record<string, SavedSolverResult>): Record<string, unknown> {
  return { ...baseAircraftJson(), results };
}

function handshake(solver: string, attempt: number): HandshakePayload {
  return {
    source: "aid",
    solver,
    axes: { mach: [0.2], alpha: [-2, 0, 4], beta: [0] },
    tables: {
      cl: [[0.1, 0.3, 0.6]],
      cd: [[0.02, 0.03, 0.04]],
      cm: [[0, -0.01, -0.03]],
    },
    ref: { mac: 1.4 + attempt / 10 },
  };
}

function solverRaw(solver: string, attempt: number): Record<string, unknown> {
  return {
    solver,
    alpha: [-2, 0, 4],
    cl: [0.1, 0.3, 0.6],
    lattice: { nodes: [[0, 0, 0], [1, 1, 1]], fields: ["cp"] },
    attempt,
  };
}

function savedResult(solver: string, attempt: number): SavedSolverResult {
  return { solver, payload: handshake(solver, attempt), raw: solverRaw(solver, attempt) };
}

function stubFetch(firstAttempt = 1): void {
  vi.stubGlobal("location", { search: "" });
  const attempts = new Map<string, number>();
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (!String(input).includes("/analyze")) {
        return { ok: true, status: 200, json: async () => ({ ok: false, summary: [] }) };
      }
      const { solver } = JSON.parse(String(init?.body)) as { solver: string };
      const attempt = (attempts.get(solver) ?? firstAttempt - 1) + 1;
      attempts.set(solver, attempt);
      return {
        ok: true,
        status: 200,
        json: async () => ({
          ok: true,
          solver,
          raw: solverRaw(solver, attempt),
          payload: handshake(solver, attempt),
        }),
      };
    }),
  );
}