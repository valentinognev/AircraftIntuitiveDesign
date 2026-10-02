import { afterEach, expect, it, vi } from "vitest";

const effects = vi.hoisted<(() => unknown)[]>(() => []);

vi.mock("react", () => ({
  useState: (init: unknown) => [typeof init === "function" ? init() : init, () => {}],
  useSyncExternalStore: (_subscribe: unknown, getSnapshot: () => unknown) => getSnapshot(),
  useEffect: (effect: () => unknown) => void effects.push(effect),
}));

import { emptyAircraft, type SavedSolverResult } from "./aircraft";
import type { HandshakePayload } from "./payload";
import { Results } from "./Results";
import store from "./store";

afterEach(() => {
  vi.unstubAllGlobals();
  effects.length = 0;
  store.setState({
    aircraft: null,
    payloads: {},
    raws: {},
    lastPayload: null,
    handbook: null,
    lastStability: null,
  });
});

it("the control-derivatives request body carries no results block", async () => {
  loadAircraftWithResults();
  const body = await controlDerivativesBody();
  expect(body.solver).toBe("handbook");
  expect(body.deltas_deg).toEqual([0, 5]);
  expect("results" in body.aircraft).toBe(false);
  expect(body.aircraft).toEqual(geometryJson());
});

it("the control-derivatives request leaves the store results in place", async () => {
  const results = { datcom: savedResult("datcom"), tornado: savedResult("tornado") };
  loadAircraftWithResults(results);
  await controlDerivativesBody();
  expect(store.getState().aircraft!.results).toEqual(results);
  expect(Object.keys(store.getState().payloads)).toEqual(["datcom", "tornado"]);
  expect(Object.keys(store.getState().raws)).toEqual(["datcom", "tornado"]);
});

it("no control-derivatives request is made before a solver runs", async () => {
  store.setState({ aircraft: { ...emptyAircraft(), results: { datcom: savedResult("datcom") } } });
  const bodies = await runControlDerivatives();
  expect(bodies).toHaveLength(0);
});

async function controlDerivativesBody(): Promise<ControlDerivBody> {
  const bodies = await runControlDerivatives();
  expect(bodies).toHaveLength(1);
  return JSON.parse(bodies[0]) as ControlDerivBody;
}

async function runControlDerivatives(): Promise<string[]> {
  const bodies: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      bodies.push(String(init?.body ?? ""));
      return { ok: true, status: 200, json: async () => ({}) };
    }),
  );
  Results({});
  for (const effect of effects) effect();
  await new Promise((resolve) => setTimeout(resolve, 0));
  return bodies;
}

function loadAircraftWithResults(results?: Record<string, SavedSolverResult>): void {
  const block = results ?? { datcom: savedResult("datcom") };
  store.setState({
    aircraft: { ...emptyAircraft(), results: block },
    payloads: { datcom: block.datcom.payload, ...(block.tornado ? { tornado: block.tornado.payload } : {}) },
    raws: { datcom: block.datcom.raw, ...(block.tornado ? { tornado: block.tornado.raw } : {}) },
    lastPayload: block.datcom.payload,
  });
}

function geometryJson(): Record<string, unknown> {
  return JSON.parse(JSON.stringify(emptyAircraft())) as Record<string, unknown>;
}

function savedResult(solver: string): SavedSolverResult {
  return {
    solver,
    payload: handshake(solver),
    raw: {
      solver,
      lattice: { nodes: [[0, 0, 0], [1, 1, 1]], fields: ["cp", "cl"] },
      note: "verbatim",
    },
  };
}

function handshake(solver: string): HandshakePayload {
  return {
    source: "aid",
    solver,
    axes: { mach: [0.2], alpha: [-2, 0, 4], beta: [0] },
    tables: {
      cl: [[0.1, 0.3, 0.6]],
      cd: [[0.02, 0.03, 0.04]],
      cm: [[0, -0.01, -0.03]],
    },
    ref: { mac: 1.4 },
  };
}

type ControlDerivBody = {
  aircraft: Record<string, unknown>;
  solver: string;
  deltas_deg: number[];
};
