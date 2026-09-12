import { expect, it } from "vitest";
import { aircraftFromJson, emptyAircraft } from "./aircraft";
import {
  GeometryError,
  keepLastGood,
  sceneFromConfig,
  tessellate,
} from "./geom";

/** Cessna 172 JSONC subset — WG SSPN/CHRDR from Python/models/Cessna 172.jsonc. */
const CESSNA_SUBSET = {
  WG: {
    CHRDR: 2,
    CHRDTP: 2,
    SSPN: 6,
    SAVSI: 0,
    DHDADI: 3,
    X: 2.2,
    Y: 0,
    Z: 1.15,
  },
  HT: { CHRDR: 1.3, CHRDTP: 0.8, SSPN: 2.5, X: 8.75, Y: 0, Z: 0.25 },
  VT: { CHRDR: 5, CHRDTP: 1, SSPN: 2, SAVSI: 15, X: 5, Y: 0, Z: 0.25 },
  F: {},
  A: {},
  E: {},
  R: {},
  BD: {
    NX: 16,
    X: [0.0, 0.33, 0.5, 0.75, 1.0, 1.65, 1.9, 2.0, 2.34, 3.0, 4.0, 5.0, 6.0, 7.0, 9.0, 10.0],
    ZU: [0, 0.17, 0.35, 0.44, 0.52, 0.67, 0.85, 1.11, 1.23, 1.3, 1.2, 0.82, 0.67, 0.58, 0.44, 0.34],
    ZL: [-0.02, -0.2, -0.47, -0.62, -0.77, -0.82, -0.84, -0.84, -0.83, -0.8, -0.76, -0.7, -0.61, -0.5, -0.15, 0.1],
    R: [0.01, 0.3, 0.49, 0.62, 0.7, 0.75, 0.75, 0.75, 0.76, 0.8, 0.8, 0.75, 0.5, 0.4, 0.2, 0.1],
  },
  NP: [null, null, null, null],
  NB: [null, null],
  AERO: {},
  plot_cmp: [1, 1, 1, 1],
  unit: "ft",
};

function wingSpanY(wing: { le: { y: number }[]; te: { y: number }[] }): number {
  const ys = [...wing.le, ...wing.te].map((p) => p.y);
  return Math.max(...ys) - Math.min(...ys);
}

it("Cessna WG span is greater than 0 in geom", () => {
  const ac = aircraftFromJson(CESSNA_SUBSET);
  const tess = tessellate(ac);
  expect(tess.wings.length).toBeGreaterThan(0);
  expect(wingSpanY(tess.wings[0])).toBeGreaterThan(0);
});

it("tessellate throws GeometryError for negative WG.SSPN", () => {
  const ac = aircraftFromJson({ ...CESSNA_SUBSET, WG: { ...CESSNA_SUBSET.WG, SSPN: -1 } });
  expect(() => tessellate(ac)).toThrow(GeometryError);
});

it("sceneFromConfig returns ok scene for Cessna subset", () => {
  const result = sceneFromConfig(aircraftFromJson(CESSNA_SUBSET));
  expect(result.ok).toBe(true);
  if (result.ok) {
    expect(result.scene.fuselage.length).toBeGreaterThan(0);
    expect(result.scene.wings.length).toBeGreaterThan(0);
  }
});

it("sceneFromConfig returns ok false and message on GeometryError", () => {
  const ac = aircraftFromJson({ ...CESSNA_SUBSET, WG: { ...CESSNA_SUBSET.WG, SSPN: -1 } });
  const result = sceneFromConfig(ac);
  expect(result.ok).toBe(false);
  if (!result.ok) expect(result.message.length).toBeGreaterThan(0);
});

it("keepLastGood retains prior scene on GeometryError", () => {
  const good = sceneFromConfig(aircraftFromJson(CESSNA_SUBSET));
  expect(good.ok).toBe(true);
  if (!good.ok) return;
  const last = good.scene;
  const fail = sceneFromConfig(
    aircraftFromJson({ ...CESSNA_SUBSET, WG: { ...CESSNA_SUBSET.WG, SSPN: Number.NaN } }),
  );
  const kept = keepLastGood(fail, last);
  expect(kept.warning).not.toBeNull();
  expect(kept.scene).toBe(last);
});

it("empty aircraft tessellates without throwing", () => {
  const tess = tessellate(emptyAircraft());
  expect(tess.fuselage).toEqual([]);
  expect(tess.wings).toEqual([]);
});
