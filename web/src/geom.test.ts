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

function wingSpanY(wing: { rows: { y: number }[][] }): number {
  const ys = wing.rows.flat().map((p) => p.y);
  return Math.max(...ys) - Math.min(...ys);
}

const THICK_FOIL = [
  [1, 0],
  [0.5, -0.2],
  [0, 0],
  [0.5, 0.2],
  [1, 0],
];

function zSpan(points: { z: number }[]): number {
  const zs = points.map((p) => p.z);
  return Math.max(...zs) - Math.min(...zs);
}

it("wing root uses DATA airfoil thickness", () => {
  const ac = aircraftFromJson({
    ...CESSNA_SUBSET,
    WG: { ...CESSNA_SUBSET.WG, TC: 0.01, DATA: THICK_FOIL },
  });
  const root = tessellate(ac).wings.find((wing) => wing.name === "wing")?.rows[0] ?? [];
  expect(zSpan(root)).toBeGreaterThan(0.7);
});

it("horizontal and vertical tails use airfoil thickness", () => {
  const ac = aircraftFromJson({
    ...CESSNA_SUBSET,
    HT: { ...CESSNA_SUBSET.HT, TC: 0.01, DATA: THICK_FOIL },
    VT: { ...CESSNA_SUBSET.VT, TC: 0.01, DATA: THICK_FOIL },
  });
  const tess = tessellate(ac);
  const ht = tess.wings.find((wing) => wing.name === "ht")?.rows[0] ?? [];
  const vt = tess.wings.find((wing) => wing.name === "vt")?.rows[0] ?? [];
  expect(zSpan(ht)).toBeGreaterThan(0.4);
  const ys = vt.map((p) => p.y);
  expect(Math.max(...ys) - Math.min(...ys)).toBeGreaterThan(1.5);
});

it("draws wing struts and a propeller disk from NP", () => {
  const ac = aircraftFromJson({
    ...CESSNA_SUBSET,
    NP: [
      { CHRDR: 0.3, CHRDTP: 0.3, SSPN: 5, DHDADI: 17, X: 2.5, Y: 0, Z: 0 },
      null,
      null,
      { CHRDR: 0.3125, CHRDTP: 0.15625, SSPN: 1.25, i: 30, TWISTA: 30, X: 0.29, Y: 0, Z: 0 },
    ],
  });
  const tess = tessellate(ac);
  const strut = tess.wings.find((wing) => wing.name === "wing 2" && wing.rows.some((row) => row.some((p) => p.y > 1)));
  const tip = strut?.rows[strut.rows.length - 1][0];
  expect(tip).toBeDefined();
  expect(tip?.z ?? 0).toBeGreaterThan(1.2);
  expect(tip?.y ?? 0).toBeGreaterThan(4);
  const prop = tess.wings.filter((wing) => wing.name === "prop").flatMap((wing) => wing.rows.flat());
  expect(zSpan(prop)).toBeGreaterThan(0.8);
});

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

it("body stations loft into closed elliptical sections", () => {
  const ac = aircraftFromJson(CESSNA_SUBSET);
  const tess = tessellate(ac);
  expect(tess.fuselage).toHaveLength(CESSNA_SUBSET.BD.X.length);
  const i = 9;
  const ring = tess.fuselage[i];
  expect(ring.length).toBeGreaterThan(4);
  expect(ring.every((p) => p.x === CESSNA_SUBSET.BD.X[i])).toBe(true);
  const ys = ring.map((p) => p.y);
  const zs = ring.map((p) => p.z);
  expect(Math.max(...ys)).toBeCloseTo(CESSNA_SUBSET.BD.R[i]);
  expect(Math.min(...ys)).toBeCloseTo(-CESSNA_SUBSET.BD.R[i]);
  expect(Math.max(...zs)).toBeCloseTo(CESSNA_SUBSET.BD.ZU[i]);
  expect(Math.min(...zs)).toBeCloseTo(CESSNA_SUBSET.BD.ZL[i]);
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
