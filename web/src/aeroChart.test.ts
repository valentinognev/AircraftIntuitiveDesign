import { expect, it } from "vitest";
import type { ControlBars, HingeBars } from "./aeroFigures";
import {
  barFill,
  barLegend,
  controlBarCategories,
  groupedBarCategories,
  hingeBarCategories,
  hlineSegment,
  knownSolverRaws,
  layoutBars,
  lineSeriesDomain,
  seriesLegend,
  stabilityAlphaOf,
} from "./aeroChart";
import { chartLayout } from "./payload";

it("keeps datcom, tornado, avl, and flow5 raws and drops other keys", () => {
  const datcom = { cl: [0.2] };
  const flow5 = { CL: [0.1] };
  expect(
    knownSolverRaws({
      datcom,
      flow5,
      panel: { CL: [1] },
      tornado: null,
      avl: [1, 2],
    }),
  ).toEqual({ datcom, flow5 });
});

it("reads a finite stability alpha and ignores anything else", () => {
  expect(stabilityAlphaOf(null)).toBeNull();
  expect(stabilityAlphaOf(undefined)).toBeNull();
  expect(stabilityAlphaOf({})).toBeNull();
  expect(stabilityAlphaOf({ alpha: Number.NaN })).toBeNull();
  expect(stabilityAlphaOf({ alpha: Number.POSITIVE_INFINITY })).toBeNull();
  expect(stabilityAlphaOf({ alpha: "2" })).toBeNull();
  expect(stabilityAlphaOf({ alpha: 2.5 })).toBe(2.5);
});

it("labels a line series with its name, otherwise the solver", () => {
  expect(seriesLegend({ solver: "tornado", name: "Prandtl" })).toBe("Prandtl");
  expect(seriesLegend({ solver: "datcom" })).toBe("datcom");
  expect(seriesLegend({ solver: "avl", name: "" })).toBe("avl");
});

it("includes an hline's first y in the domain and draws it across the plot", () => {
  const domain = lineSeriesDomain([
    { solver: "datcom", stroke: "currentColor", kind: "line", x: [0, 2], y: [0, 1] },
    { solver: "tornado", stroke: "red", kind: "hline", x: [0, 2], y: [4, 9] },
  ]);
  expect(domain).toEqual({ xmin: 0, xmax: 2, ymin: 0, ymax: 4 });

  const plot = chartLayout().plot;
  const seg = hlineSegment(4, domain!, plot);
  expect(seg).toEqual({
    x1: plot.x,
    y1: plot.y,
    x2: plot.x + plot.width,
    y2: plot.y,
  });
  expect(hlineSegment(Number.NaN, domain!, plot)).toBeNull();
});

it("leaves a no-data hline off the scale", () => {
  const domain = lineSeriesDomain([
    { solver: "datcom", stroke: "currentColor", kind: "line", x: [0, 2], y: [0, 1] },
    { solver: "tornado", stroke: "red", kind: "hline", x: [0, 2], y: [99999] },
  ]);
  expect(domain).toEqual({ xmin: 0, xmax: 2, ymin: 0, ymax: 1 });
  expect(hlineSegment(99999, domain!, chartLayout().plot)).toBeNull();
});

it("skips null bar slots and keeps every category label", () => {
  const plot = chartLayout().plot;
  const laid = layoutBars(
    groupedBarCategories([
      { label: "Clp", tornado: 1, avl: null },
      { label: "Cmq", tornado: null, avl: -2 },
    ]),
    plot,
  );
  expect(laid.labels.map((label) => label.label)).toEqual(["Clp", "Cmq"]);
  expect(laid.bars.map((bar) => ({ key: bar.key, label: bar.label }))).toEqual([
    { key: "tornado", label: "Clp" },
    { key: "avl", label: "Cmq" },
  ]);
  expect(laid.domain).toEqual({ xmin: -0.5, xmax: 1.5, ymin: -2, ymax: 1 });
  expect(laid.bars[0].height).toBeGreaterThan(0);
  expect(laid.bars[1].height).toBeGreaterThan(0);
  expect(laid.bars[0].x).toBeLessThan(laid.bars[1].x);
  expect(laid.labels[0].x).toBeCloseTo(plot.x + plot.width / 4);
});

it("places tornado left of avl in one category and anchors bars at zero", () => {
  const plot = chartLayout().plot;
  const laid = layoutBars(groupedBarCategories([{ label: "Clp", tornado: 1, avl: 2 }]), plot);
  expect(laid.bars.map((bar) => bar.key)).toEqual(["tornado", "avl"]);
  expect(laid.bars[0].x).toBeLessThan(laid.bars[1].x);
  expect(laid.domain?.ymin).toBe(0);
  expect(laid.domain?.ymax).toBe(2);
  const dy = 2;
  const yOf = (value: number) => plot.y + plot.height - ((value - 0) / dy) * plot.height;
  expect(laid.bars[0].y).toBeCloseTo(yOf(1));
  expect(laid.bars[0].y + laid.bars[0].height).toBeCloseTo(yOf(0));
});

it("turns control and hinge figures into labeled slots, skipping nulls at layout", () => {
  const controls: ControlBars = {
    kind: "control-bars",
    title: "Control increments",
    groups: [{ label: "flap", dcl: 0.1, dcm: null }],
    tornado: [{ key: "CL_d", values: [0.2, 0.3] }],
  };
  expect(controlBarCategories(controls).map((cat) => cat.label)).toEqual(["flap", "CL_d", "CL_d"]);
  const hinge: HingeBars = {
    kind: "hinge-bars",
    title: "DATCOM hinge / max-lift",
    groups: [{ label: "flap", cha: null, chd: 1, dclMax: null }],
  };
  const plot = chartLayout().plot;
  const laid = layoutBars(hingeBarCategories(hinge), plot);
  expect(laid.labels.map((label) => label.label)).toEqual(["flap"]);
  expect(laid.bars.map((bar) => bar.key)).toEqual(["chd"]);
});

it("paints AVL bars magenta so they are not the DATCOM default", () => {
  expect(barFill("avl")).toBe("magenta");
  expect(barFill("avl")).not.toBe(barFill("dcl"));
  expect(barFill("tornado")).toBe("red");
});

it("prefers an explicit series label over the solver name", () => {
  expect(seriesLegend({ solver: "datcom", label: "datcom (beta=0)" })).toBe("datcom (beta=0)");
  expect(seriesLegend({ solver: "avl", name: "Prandtl", label: "avl (beta=0)" })).toBe(
    "avl (beta=0)",
  );
  expect(seriesLegend({ solver: "avl", label: "" })).toBe("avl");
});

// R31: the bar figures name their solver in the legend, and a bar whose data was
// computed at beta = 0 whatever the Aero tab asked for is marked -- which is every
// DATCOM bar and AVL's, since neither has a sideslip capability at all.

it("marks the AVL bar legend beta=0 at a sideslip and leaves Tornado alone", () => {
  const categories = groupedBarCategories([{ label: "Clp", tornado: -0.4, avl: -0.3 }]);
  expect(barLegend(categories, 5)).toEqual([
    { key: "tornado", label: "Tornado" },
    { key: "avl", label: "AVL (beta=0)" },
  ]);
  expect(barLegend(categories, 0)).toEqual([
    { key: "tornado", label: "Tornado" },
    { key: "avl", label: "AVL" },
  ]);
});

it("defaults the bar legend's beta to zero", () => {
  const categories = groupedBarCategories([{ label: "Clp", tornado: -0.4, avl: -0.3 }]);
  expect(barLegend(categories)).toEqual(barLegend(categories, 0));
});

// README.md:44 is the rule, and it is about provenance, not naming: "any series that
// was not computed at that sideslip gets ` (beta=0)` appended ... DATCOM and AVL are
// marked everywhere, having no sideslip capability at all." The hinge bars are DATCOM
// `high_lift` blocks under names that describe the quantity rather than the solver,
// which is what the old test here took as an exemption. Naming is not the rule, and
// these are the same blocks as the ΔCDi curve this file already marks.
it("marks the DATCOM hinge bars, whose names describe the quantity and not the solver", () => {
  const categories = hingeBarCategories({
    title: "hinge",
    groups: [{ label: "d1", cha: 0.3, chd: 0.4, dclMax: 1.2 }],
  });
  expect(barLegend(categories, 5).map((item) => item.label)).toEqual([
    "cha (beta=0)",
    "chd (beta=0)",
    "dclMax (beta=0)",
  ]);
  // README.md:44 also requires every label at BETA == 0 to be byte-identical.
  expect(barLegend(categories, 0).map((item) => item.label)).toEqual(["cha", "chd", "dclMax"]);
});
