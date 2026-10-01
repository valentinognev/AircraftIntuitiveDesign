import { expect, it } from "vitest";
import {
  alphaGrid,
  seriesDerivative,
  seriesVsAlpha,
  type OverlayPointSeries,
} from "./coeffOverlay";

const PER_RAD = 180 / Math.PI;

function yAt(series: OverlayPointSeries, deg: number): number {
  const index = series.x.findIndex((x) => x === deg);
  expect(index).toBeGreaterThanOrEqual(0);
  return series.y[index];
}

it("builds an 80-point grid from DATCOM alpha endpoints", () => {
  const grid = alphaGrid({ datcom: { alpha: [-4, 0, 8] } }, null);
  expect(grid).toHaveLength(80);
  expect(grid[0]).toBe(-4);
  expect(grid[79]).toBe(8);
});

it("builds a 100-point stability grid when DATCOM alpha is missing", () => {
  const grid = alphaGrid({}, 2);
  expect(grid).toHaveLength(100);
  expect(grid[0]).toBe(-10);
  expect(grid[99]).toBe(20);
});

it("returns an empty alpha grid without DATCOM alpha or stability alpha", () => {
  expect(alphaGrid({}, null)).toEqual([]);
  expect(alphaGrid({ datcom: {} }, null)).toEqual([]);
});

it("drops DATCOM samples whose absolute value is at least 99998", () => {
  const series = seriesVsAlpha(
    { datcom: { alpha: [0, 2], cl: [0.1, 99999] } },
    null,
    { datcom: "cl" },
  );
  expect(series).toEqual([
    {
      solver: "datcom",
      stroke: "currentColor",
      x: [0],
      y: [0.1],
      kind: "line",
    },
  ]);
});

it("reconstructs Tornado CL so one degree of CL_a adds 1", () => {
  const raws = {
    datcom: { alpha: [0, 1] },
    tornado: { alpha: 0, CL: 0.5, CL_a: PER_RAD },
  };
  const series = seriesVsAlpha(raws, null, { tornado: ["CL", "CL_a"] });
  expect(series).toHaveLength(1);
  expect(series[0].solver).toBe("tornado");
  expect(series[0].stroke).toBe("red");
  expect(series[0].kind).toBe("line");
  expect(yAt(series[0], 0)).toBeCloseTo(0.5, 12);
  expect(yAt(series[0], 1)).toBeCloseTo(0.5 + 1, 12);
});

it("treats Tornado alpha as degrees when applying the per-radian slope", () => {
  const series = seriesVsAlpha(
    {
      datcom: { alpha: [2, 3] },
      tornado: { alpha: 2, CL: 0.5, CL_a: PER_RAD },
    },
    null,
    { tornado: ["CL", "CL_a"] },
  );
  expect(series).toHaveLength(1);
  expect(yAt(series[0], 2)).toBeCloseTo(0.5, 12);
  expect(yAt(series[0], 3)).toBeCloseTo(0.5 + 1, 12);
});

it("reads Tornado alpha and CL when they are one-element lists", () => {
  const series = seriesVsAlpha(
    {
      datcom: { alpha: [0, 1] },
      tornado: { alpha: [0], CL: [0.5], CL_a: PER_RAD },
    },
    null,
    { tornado: ["CL", "CL_a"] },
  );
  expect(yAt(series[0], 0)).toBeCloseTo(0.5, 12);
  expect(yAt(series[0], 1)).toBeCloseTo(0.5 + 1, 12);
});

it("omits Tornado when the value has no slope key", () => {
  const series = seriesVsAlpha(
    {
      datcom: { alpha: [0, 1] },
      tornado: { alpha: 0, CL: 0.5 },
    },
    null,
    { tornado: ["CL", "CL_a"] },
  );
  expect(series).toEqual([]);
});

it("plots AVL CL at the solved angles and ignores CLa", () => {
  const series = seriesVsAlpha(
    {
      datcom: { alpha: [0, 1] },
      avl: { alpha: [-4, 0, 4], CLtot: [0.1, 0.4, 0.7], CLa: PER_RAD },
    },
    null,
    { avl: "CLtot" },
  );
  expect(series).toHaveLength(1);
  expect(series[0]).toMatchObject({
    solver: "avl",
    stroke: "magenta",
    kind: "line",
    x: [-4, 0, 4],
    y: [0.1, 0.4, 0.7],
  });
});

it("plots a scalar AVL CLtot at its alpha and omits AVL when alpha is missing", () => {
  const series = seriesVsAlpha(
    { avl: { alpha: 4, CLtot: 0.2 } },
    9,
    { avl: "CLtot" },
  );
  expect(series).toEqual([
    {
      solver: "avl",
      stroke: "magenta",
      x: [4],
      y: [0.2],
      kind: "line",
    },
  ]);
  expect(seriesVsAlpha({ avl: { CLtot: 0.2 } }, 2, { avl: "CLtot" })).toEqual([]);
});

it("plots flow5 on its own alpha and keeps no-data values", () => {
  const series = seriesVsAlpha(
    { flow5: { alpha: [0, 4], CL: [0.2, 99999] } },
    null,
    { flow5: "CL" },
  );
  expect(series).toEqual([
    {
      solver: "flow5",
      stroke: "yellow",
      x: [0, 4],
      y: [0.2, 99999],
      kind: "line",
    },
  ]);
});

it("draws Tornado derivatives as a per-degree horizontal on the alpha grid", () => {
  const raws = {
    datcom: { alpha: [-4, 0, 8] },
    tornado: { CL_a: PER_RAD },
  };
  const series = seriesDerivative(raws, null, { tornado: "CL_a" });
  expect(series).toHaveLength(1);
  expect(series[0].solver).toBe("tornado");
  expect(series[0].stroke).toBe("red");
  expect(series[0].kind).toBe("hline");
  expect(series[0].x).toEqual(alphaGrid(raws, null));
  expect(series[0].y).toHaveLength(80);
  for (const y of series[0].y) expect(y).toBeCloseTo(1, 12);
});

it("plots AVL CLa only at solved angles, in per degree", () => {
  const series = seriesDerivative(
    { avl: { alpha: [-4, 0, 4], CLa: [PER_RAD, PER_RAD, PER_RAD] } },
    null,
    { avl: "CLa" },
  );
  expect(series[0].x).toEqual([-4, 0, 4]);
  expect(series[0].y.every((value) => Math.abs(value - 1) < 1e-12)).toBe(true);
  expect(series[0].kind).toBe("line");
});

it("treats a one-element AVL alpha as one solved angle for a scalar derivative", () => {
  const series = seriesDerivative(
    { avl: { alpha: [4], CLa: PER_RAD } },
    null,
    { avl: "CLa" },
  );
  expect(series).toHaveLength(1);
  expect(series[0].kind).toBe("line");
  expect(series[0].x).toEqual([4]);
  expect(Math.abs(series[0].y[0] - 1) < 1e-12).toBe(true);
  expect(
    seriesDerivative(
      { avl: { alpha: [-4, 0, 4], CLa: PER_RAD } },
      null,
      { avl: "CLa" },
    ),
  ).toEqual([]);
});

it("plots a scalar AVL derivative as one per-degree point at its alpha", () => {
  const series = seriesDerivative(
    { avl: { alpha: 4, CLa: PER_RAD } },
    null,
    { avl: "CLa" },
  );
  expect(series).toHaveLength(1);
  expect(series[0].kind).toBe("line");
  expect(series[0].x).toEqual([4]);
  expect(Math.abs(series[0].y[0] - 1) < 1e-12).toBe(true);
});

it("omits an AVL derivative when alpha and the value differ in length", () => {
  expect(
    seriesDerivative(
      { avl: { alpha: [-4, 0, 4], CLa: [PER_RAD, PER_RAD] } },
      null,
      { avl: "CLa" },
    ),
  ).toEqual([]);
});

it("draws flow5 derivatives as a per-degree horizontal and does not spread AVL without alpha", () => {
  const raws = {
    datcom: { alpha: [0, 10] },
    avl: { CLa: PER_RAD },
    flow5: { CLa: PER_RAD },
  };
  const series = seriesDerivative(raws, null, { avl: "CLa", flow5: "CLa" });
  expect(series.map((item) => item.solver)).toEqual(["flow5"]);
  expect(series[0].stroke).toBe("yellow");
  expect(series[0].kind).toBe("hline");
  expect(series[0].x).toEqual(alphaGrid(raws, null));
  expect(series[0].y).toHaveLength(80);
  for (const y of series[0].y) expect(y).toBeCloseTo(1, 12);
});

it("plots DATCOM derivatives on DATCOM alpha, not the 80-point grid", () => {
  const raws = {
    datcom: { alpha: [-4, 0, 8], cla: [0.05, 99999, 0.07] },
  };
  const series = seriesDerivative(raws, null, { datcom: "cla" });
  expect(alphaGrid(raws, null)).toHaveLength(80);
  expect(series).toEqual([
    {
      solver: "datcom",
      stroke: "currentColor",
      x: [-4, 8],
      y: [0.05, 0.07],
      kind: "line",
    },
  ]);
});
