import { expect, it } from "vitest";
import {
  aeroTabs,
  type AeroFigure,
  type AeroTab,
  type BarFigure,
  type ControlBars,
  type HingeBars,
  type LineFigure,
  type TableFigure,
} from "./aeroFigures";
import { seriesLegend } from "./aeroChart";
import type { OverlayPointSeries, SolverRaws } from "./coeffOverlay";

const PER_RAD = 180 / Math.PI;

function tab(tabs: AeroTab[], label: string): AeroTab {
  const found = tabs.find((item) => item.label === label);
  expect(found, label).toBeDefined();
  return found as AeroTab;
}

function figure(figures: AeroFigure[], title: string): AeroFigure {
  const found = figures.find((item) => item.title === title);
  expect(found, title).toBeDefined();
  return found as AeroFigure;
}

function lines(parent: AeroTab, title: string): LineFigure {
  const found = figure(parent.figures, title);
  expect(found.kind).toBe("lines");
  return found as LineFigure;
}

function bars(parent: AeroTab, title: string): BarFigure {
  const found = figure(parent.figures, title);
  expect(found.kind).toBe("bars");
  return found as BarFigure;
}

function table(parent: AeroTab, title: string): TableFigure {
  const found = figure(parent.figures, title);
  expect(found.kind).toBe("table");
  return found as TableFigure;
}

function yAt(series: OverlayPointSeries, deg: number): number {
  const index = series.x.findIndex((x) => x === deg);
  expect(index).toBeGreaterThanOrEqual(0);
  return series.y[index];
}

function datcomSeries(fig: LineFigure): OverlayPointSeries {
  const series = fig.series.filter((item) => item.solver === "datcom");
  expect(series).toHaveLength(1);
  return series[0];
}

it("returns the seven tabs in order when every figure is empty", () => {
  const tabs = aeroTabs({}, null, null);
  expect(tabs.map((item) => item.id)).toEqual([
    "forces",
    "moments",
    "derivatives",
    "downwash",
    "controls",
    "spanwise",
    "sections",
  ]);
  expect(tabs.map((item) => item.label)).toEqual([
    "Forces",
    "Moments",
    "Derivatives",
    "Downwash",
    "Controls",
    "Spanwise",
    "Sections",
  ]);

  const forces = tab(tabs, "Forces");
  expect(forces.figures.map((item) => item.title)).toEqual([
    "CL",
    "CD",
    "CY",
    "CN",
    "CA",
    "CDind",
    "CDvis",
    "e",
    "Per-wing / AVL extras",
  ]);
  for (const title of ["CL", "CD", "CY", "CN", "CA", "CDind", "CDvis", "e"]) {
    const fig = lines(forces, title);
    expect(fig.series).toEqual([]);
    expect(fig.xlabel).toBe("α (deg)");
    expect(fig.ylabel).toBe(title);
  }
  expect(bars(forces, "Per-wing / AVL extras").groups).toEqual([]);

  const moments = tab(tabs, "Moments");
  expect(moments.figures.map((item) => item.title)).toEqual(["Cm", "Cl", "Cn", "Xcp", "NP"]);
  for (const title of ["Cm", "Cl", "Cn", "Xcp", "NP"]) {
    expect(lines(moments, title).series).toEqual([]);
  }

  const derivatives = tab(tabs, "Derivatives");
  expect(derivatives.figures.map((item) => item.title)).toEqual([
    "CLα",
    "Cmα",
    "CYβ",
    "Cnβ",
    "Clβ",
    "Clp",
    "Cmq",
    "Cnr",
    "CLp",
    "CLq",
    "CLr",
    "p, q, r (per rad)",
  ]);
  for (const title of ["Clp", "Cmq", "Cnr", "CLp", "CLq", "CLr"]) {
    expect(lines(derivatives, title).series).toEqual([]);
  }
  expect(bars(derivatives, "p, q, r (per rad)").groups).toEqual([
    { label: "Clp", tornado: null, avl: null },
    { label: "Cmq", tornado: null, avl: null },
    { label: "Cnr", tornado: null, avl: null },
    { label: "CLp", tornado: null, avl: null },
    { label: "CLq", tornado: null, avl: null },
    { label: "CLr", tornado: null, avl: null },
  ]);

  const downwash = tab(tabs, "Downwash");
  expect(downwash.figures.map((item) => [item.kind, item.title])).toEqual([
    ["lines", "ε"],
    ["lines", "dε/dα"],
    ["lines", "q/q∞"],
  ]);

  const controls = tab(tabs, "Controls");
  expect(controls.figures.map((item) => [item.kind, item.title])).toEqual([
    ["control-bars", "Control increments"],
    ["lines", "ΔCDi"],
    ["lines", "Control extras"],
  ]);
  expect(lines(controls, "ΔCDi").series).toEqual([]);
  expect(lines(controls, "Control extras").series).toEqual([]);

  expect(lines(tab(tabs, "Spanwise"), "Spanwise lift").series).toEqual([]);
  expect(tab(tabs, "Sections").figures).toEqual([]);
});

it("puts DATCOM cl only on Forces CL and drops the 99999 sample", () => {
  const tabs = aeroTabs(
    { datcom: { alpha: [0, 2], cl: [0.42, 99999], cd: [0.2, 0.3] } },
    null,
    null,
  );
  const cl = datcomSeries(lines(tab(tabs, "Forces"), "CL"));
  expect(cl.y).toEqual([0.42]);
  expect(cl.x).toEqual([0]);
  expect(cl.y).not.toContain(99999);
  expect(cl.stroke).toBe("currentColor");

  for (const item of tabs) {
    for (const fig of item.figures) {
      if (fig.kind !== "lines") continue;
      if (item.label === "Forces" && fig.title === "CL") continue;
      for (const series of fig.series) {
        expect(series.y).not.toContain(0.42);
        expect(series.y).not.toContain(99999);
      }
    }
  }
  expect(datcomSeries(lines(tab(tabs, "Forces"), "CD")).y).toEqual([0.2, 0.3]);
});

it("reconstructs Tornado CL and CL_a inside Forces CL the same way as the one-degree overlay", () => {
  const tabs = aeroTabs(
    {
      datcom: { alpha: [0, 1] },
      tornado: { alpha: 0, CL: 0.5, CL_a: PER_RAD },
    },
    null,
    null,
  );
  const series = lines(tab(tabs, "Forces"), "CL").series;
  expect(series).toHaveLength(1);
  expect(series[0].solver).toBe("tornado");
  expect(series[0].stroke).toBe("red");
  expect(series[0].kind).toBe("line");
  expect(yAt(series[0], 0)).toBeCloseTo(0.5, 12);
  expect(yAt(series[0], 1)).toBeCloseTo(1.5, 12);
  expect(lines(tab(tabs, "Forces"), "CD").series).toEqual([]);
});

it("maps force and moment coefficient keys onto the named line figures", () => {
  const raws: SolverRaws = {
    datcom: { alpha: [0, 1] },
    tornado: {
      alpha: 0,
      CD: 0.5,
      CD_a: PER_RAD,
      CY: 0.5,
      CY_a: PER_RAD,
      CZ: 0.5,
      CZ_a: PER_RAD,
      CX: 0.5,
      CX_a: PER_RAD,
      Cm: 0.5,
      Cm_a: PER_RAD,
      Cl: 0.5,
      Cl_a: PER_RAD,
      Cn: 0.5,
      Cn_a: PER_RAD,
    },
    avl: { alpha: [-4, 0, 4], CDtot: [0.01, 0.02, 0.04], CZtot: [-0.2, -0.5, -0.7], CXtot: [0.02, 0.03, 0.05], CYtot: [0, 0, 0] },
    flow5: { alpha: [0, 2], CL: [0.7, 99999], CD: [0.15, 0.16], Cm: [0.01, 0.02] },
  };
  const tabs = aeroTabs(raws, null, null);
  const forces = tab(tabs, "Forces");
  const moments = tab(tabs, "Moments");

  for (const title of ["CD", "CY", "CN", "CA"]) {
    const series = lines(forces, title).series.find((item) => item.solver === "tornado");
    expect(series, title).toBeDefined();
    expect(yAt(series as OverlayPointSeries, 1)).toBeCloseTo(1.5, 12);
  }
  const cdAvl = lines(forces, "CD").series.find((item) => item.solver === "avl");
  expect(cdAvl).toMatchObject({
    solver: "avl",
    x: [-4, 0, 4],
    y: [0.01, 0.02, 0.04],
    kind: "line",
    stroke: "magenta",
  });
  const cnAvl = lines(forces, "CN").series.find((item) => item.solver === "avl");
  expect(cnAvl).toMatchObject({ x: [-4, 0, 4], y: [-0.2, -0.5, -0.7] });
  const caAvl = lines(forces, "CA").series.find((item) => item.solver === "avl");
  expect(caAvl).toMatchObject({ x: [-4, 0, 4], y: [0.02, 0.03, 0.05] });
  const cyAvl = lines(forces, "CY").series.find((item) => item.solver === "avl");
  expect(cyAvl).toMatchObject({ x: [-4, 0, 4], y: [0, 0, 0] });

  const flowCl = lines(forces, "CL").series.find((item) => item.solver === "flow5");
  expect(flowCl).toMatchObject({
    stroke: "yellow",
    kind: "line",
    x: [0, 2],
    y: [0.7, 99999],
  });

  for (const title of ["Cm", "Cl", "Cn"]) {
    const series = lines(moments, title).series.find((item) => item.solver === "tornado");
    expect(series, title).toBeDefined();
    expect(yAt(series as OverlayPointSeries, 1)).toBeCloseTo(1.5, 12);
  }
  expect(lines(moments, "Cl").series.some((item) => item.solver === "datcom")).toBe(false);
  expect(lines(moments, "Xcp").series).toEqual([]);
});

it("plots DATCOM xcp on Moments Xcp and leaves Tornado off that figure", () => {
  const tabs = aeroTabs(
    {
      datcom: { alpha: [0, 3], xcp: [1.5, 99999] },
      tornado: { alpha: 0, xcp: 9, CL: 0.5, CL_a: PER_RAD },
    },
    null,
    null,
  );
  const xcp = lines(tab(tabs, "Moments"), "Xcp");
  expect(xcp.series).toHaveLength(1);
  expect(datcomSeries(xcp).y).toEqual([1.5]);
});

it("expands per-wing Tornado bars and AVL extra scalars", () => {
  const tabs = aeroTabs(
    {
      tornado: {
        CLwing: [0.1, 0.2, 0.3, 0.4, 0.5],
        CDwing: [0.01],
        CC: 0.08,
      },
      avl: { CDind: 0.02, NP: 1.5 },
    },
    null,
    null,
  );
  expect(bars(tab(tabs, "Forces"), "Per-wing / AVL extras").groups).toEqual([
    { label: "CLwing1", tornado: 0.1, avl: null },
    { label: "CLwing2", tornado: 0.2, avl: null },
    { label: "CLwing3", tornado: 0.3, avl: null },
    { label: "CLwing4", tornado: 0.4, avl: null },
    { label: "CDwing", tornado: 0.01, avl: null },
    { label: "CC", tornado: 0.08, avl: null },
    { label: "CDind", tornado: null, avl: 0.02 },
    { label: "Xnp", tornado: null, avl: 1.5 },
  ]);
});

it("bars a one-element AVL extra and plots a sweep as a line", () => {
  const one = aeroTabs({ avl: { alpha: [2], CDind: [0.02], NP: [1.5] } }, null, null);
  expect(bars(tab(one, "Forces"), "Per-wing / AVL extras").groups).toEqual([
    { label: "CDind", tornado: null, avl: 0.02 },
    { label: "Xnp", tornado: null, avl: 1.5 },
  ]);
  expect(lines(tab(one, "Forces"), "CDind").series[0]).toMatchObject({
    solver: "avl",
    x: [2],
    y: [0.02],
    kind: "line",
  });

  const sweep = aeroTabs(
    {
      avl: {
        alpha: [-4, 0, 4],
        CDind: [0.01, 0.02, 0.03],
        CDvis: [0.001, 0.002, 0.003],
        e: [0.8, 0.81, 0.82],
        NP: [1.1, 1.2, 1.3],
      },
    },
    null,
    null,
  );
  expect(bars(tab(sweep, "Forces"), "Per-wing / AVL extras").groups).toEqual([]);
  expect(lines(tab(sweep, "Forces"), "CDind").series[0]).toMatchObject({
    solver: "avl",
    stroke: "magenta",
    kind: "line",
    x: [-4, 0, 4],
    y: [0.01, 0.02, 0.03],
  });
  expect(lines(tab(sweep, "Forces"), "CDvis").series[0].y).toEqual([0.001, 0.002, 0.003]);
  expect(lines(tab(sweep, "Forces"), "e").series[0].y).toEqual([0.8, 0.81, 0.82]);
  expect(lines(tab(sweep, "Moments"), "NP").series[0]).toMatchObject({
    solver: "avl",
    x: [-4, 0, 4],
    y: [1.1, 1.2, 1.3],
    kind: "line",
  });
});

it("reads derivative bar Clp from Tornado Cl_P and keeps every rate group", () => {
  const tabs = aeroTabs(
    {
      tornado: { Cl_P: 0.33 },
      avl: { Cmq: -0.44 },
    },
    null,
    null,
  );
  expect(bars(tab(tabs, "Derivatives"), "p, q, r (per rad)").groups).toEqual([
    { label: "Clp", tornado: 0.33, avl: null },
    { label: "Cmq", tornado: null, avl: -0.44 },
    { label: "Cnr", tornado: null, avl: null },
    { label: "CLp", tornado: null, avl: null },
    { label: "CLq", tornado: null, avl: null },
    { label: "CLr", tornado: null, avl: null },
  ]);
});

it("drops a multi-angle AVL rate from the bar and plots it per degree", () => {
  const tabs = aeroTabs(
    {
      datcom: { alpha: [0, 1] },
      tornado: { Cl_P: PER_RAD },
      avl: { alpha: [-4, 0, 4], Clp: [PER_RAD, PER_RAD, PER_RAD] },
    },
    null,
    null,
  );
  const derivatives = tab(tabs, "Derivatives");
  expect(bars(derivatives, "p, q, r (per rad)").groups[0]).toEqual({
    label: "Clp",
    tornado: PER_RAD,
    avl: null,
  });
  const fig = lines(derivatives, "Clp");
  const avl = fig.series.find((item) => item.solver === "avl");
  expect(avl?.kind).toBe("line");
  expect(avl?.x).toEqual([-4, 0, 4]);
  expect(avl?.y.every((value) => Math.abs(value - 1) < 1e-12)).toBe(true);
  const tornado = fig.series.find((item) => item.solver === "tornado");
  expect(tornado?.kind).toBe("hline");
  expect(tornado && yAt(tornado, 0)).toBeCloseTo(1, 12);
});

it("plots derivative lines with seriesDerivative scaling", () => {
  const tabs = aeroTabs(
    {
      datcom: { alpha: [0, 1], cla: [0.2, 99999] },
      tornado: { CL_a: PER_RAD },
      flow5: { CLa: PER_RAD },
    },
    null,
    null,
  );
  const fig = lines(tab(tabs, "Derivatives"), "CLα");
  expect(fig.xlabel).toBe("α (deg)");
  expect(fig.ylabel).toBe("CLα");
  const datcom = fig.series.find((item) => item.solver === "datcom");
  expect(datcom).toMatchObject({ kind: "line", x: [0], y: [0.2] });
  const tornado = fig.series.find((item) => item.solver === "tornado");
  expect(tornado?.kind).toBe("hline");
  expect(tornado && yAt(tornado, 0)).toBeCloseTo(1, 12);
  expect(tornado && yAt(tornado, 1)).toBeCloseTo(1, 12);
  const flow = fig.series.find((item) => item.solver === "flow5");
  expect(flow?.kind).toBe("hline");
  expect(flow?.stroke).toBe("yellow");
  expect(lines(tab(tabs, "Derivatives"), "CYβ").series).toEqual([]);
});

it("plots downwash from DATCOM alpha and ignores Tornado", () => {
  const tabs = aeroTabs(
    {
      datcom: { alpha: [0, 5], epslon: [1.25, 2.5], depsda: [0.1, 0.2] },
      tornado: { alpha: [0, 5], epslon: [9, 9], depsda: [8, 8] },
    },
    null,
    null,
  );
  const downwash = tab(tabs, "Downwash");
  const eps = lines(downwash, "ε");
  expect(eps.xlabel).toBe("α (deg)");
  expect(eps.ylabel).toBe("ε");
  expect(eps.series).toEqual([
    {
      solver: "datcom",
      stroke: "currentColor",
      kind: "line",
      x: [0, 5],
      y: [1.25, 2.5],
    },
  ]);
  expect(datcomSeries(lines(downwash, "dε/dα")).y).toEqual([0.1, 0.2]);
  expect(lines(downwash, "q/q∞").series).toEqual([]);
  for (const fig of downwash.figures) {
    if (fig.kind !== "lines") continue;
    expect(fig.series.some((item) => item.solver === "tornado")).toBe(false);
    for (const series of fig.series) expect(series.y).not.toContain(9);
  }
});

it("builds control increments, induced-drag lines, and hinge bars from high-lift blocks", () => {
  const config = "abcdefghijklmnopQRSTUVWXYZ1234";
  const tabs = aeroTabs(
    {
      datcom: {
        high_lift: [
          {
            config,
            delta: 15,
            dcl: 0.2,
            dcm: -0.05,
            dcdi_alpha: [0, 4],
            dcdi: [0.01, 99999],
            cha: 0.3,
            chd: 0.4,
            dcl_max: 1.2,
          },
          { delta: 10, dcl: 0.1, dcm: 0 },
        ],
      },
      tornado: { CL_d: [[0.5, 0.6]], CY_d: [1], CL: [9] },
    },
    null,
    null,
  );
  const controls = tab(tabs, "Controls");
  const increments = figure(controls.figures, "Control increments") as ControlBars;
  expect(increments.kind).toBe("control-bars");
  expect(increments.groups).toEqual([
    { label: "abcdefghijklmnopQRSTUVWX", dcl: 0.2, dcm: -0.05 },
    { label: "δ=10", dcl: 0.1, dcm: 0 },
  ]);
  expect(increments.tornado).toEqual([
    { key: "CL_d", values: [0.5, 0.6] },
    { key: "CY_d", values: [1] },
  ]);

  const dcdi = lines(controls, "ΔCDi");
  expect(dcdi.ylabel).toBe("ΔCDi");
  expect(dcdi.xlabel).toBe("α (deg)");
  expect(dcdi.series).toEqual([
    {
      solver: "datcom",
      stroke: "currentColor",
      kind: "line",
      x: [0],
      y: [0.01],
    },
  ]);

  const hinge = figure(controls.figures, "DATCOM hinge / max-lift") as HingeBars;
  expect(hinge.kind).toBe("hinge-bars");
  expect(hinge.groups).toEqual([
    { label: "abcdefghijklmnop", cha: 0.3, chd: 0.4, dclMax: 1.2 },
    { label: "δ=10", cha: null, chd: null, dclMax: null },
  ]);
  expect(controls.figures.some((item) => item.title === "Control extras")).toBe(false);
  expect(controls.figures.some((item) => item.title === "AVL control deflection")).toBe(false);
});

it("plots AVL control deflection instead of hinge bars when surface is present", () => {
  const tabs = aeroTabs(
    {
      datcom: { high_lift: [{ config: "flap", dcl: 1, dcm: 0, cha: 0.2 }] },
      avl: { surface: [{ angle: 5 }, { name: "aileron", angle: -2 }] },
    },
    null,
    null,
  );
  const controls = tab(tabs, "Controls");
  const deflection = lines(controls, "AVL control deflection");
  expect(deflection.ylabel).toBe("δ (deg)");
  expect(deflection.series).toEqual([
    {
      solver: "avl",
      stroke: "magenta",
      kind: "line",
      x: [0, 1],
      y: [5, -2],
    },
  ]);
  expect(controls.figures.some((item) => item.kind === "hinge-bars")).toBe(false);
});

it("draws spanwise handbook as Prandtl and one Tornado wing", () => {
  const tabs = aeroTabs(
    {
      tornado: {
        spanwise: [{ name: "Main", y: [1, 2], Cl: [0.5, 0.6] }, { y: [3], Cl: [0.7] }],
      },
    },
    null,
    { y: [0, 10], Cl: [0.2, 0.4] },
  );
  const fig = lines(tab(tabs, "Spanwise"), "Spanwise lift");
  expect(fig.xlabel).toBe("y (ft)");
  expect(fig.ylabel).toBe("Cl");
  expect(fig.series).toEqual([
    {
      solver: "datcom",
      stroke: "currentColor",
      kind: "line",
      name: "Prandtl",
      x: [0, 10],
      y: [0.2, 0.4],
    },
    {
      solver: "tornado",
      stroke: "red",
      kind: "line",
      name: "Tornado Main",
      x: [1, 2],
      y: [0.5, 0.6],
    },
    {
      solver: "tornado",
      stroke: "red",
      kind: "line",
      name: "Tornado Wing",
      x: [3],
      y: [0.7],
    },
  ]);
});

it("omits the Prandtl series when handbook y and Cl differ in length", () => {
  const tabs = aeroTabs({ tornado: {} }, null, { y: [0, 1], Cl: [0.2] });
  expect(lines(tab(tabs, "Spanwise"), "Spanwise lift").series).toEqual([]);
});

it("formats the section cm0 row and omits the table when sections are missing", () => {
  const withSections = aeroTabs(
    {
      datcom: {
        sections: {
          wing: { cm0: 0.1, alpha_ideal: Number.NaN, cl_ideal: 1e-12, cla: 1e-6, xac: 10000 },
          ht: { cm0: -0.25 },
        },
      },
    },
    null,
    null,
  );
  const defs = table(tab(withSections, "Sections"), "Section definition");
  expect(defs.columns).toEqual(["Quantity", "Wing", "HT", "VT"]);
  expect(defs.rows.map((row) => row.cells[0])).toEqual([
    "alpha_ideal",
    "alpha_zl",
    "cl_ideal",
    "cm0",
    "cla",
    "cla_mach0",
    "xac",
    "t_c",
    "le_radius",
    "delta_y",
  ]);
  const cm0 = defs.rows.find((row) => row.cells[0] === "cm0");
  expect(cm0?.cells).toEqual(["cm0", "0.1", "-0.25", ""]);
  expect(defs.rows.find((row) => row.cells[0] === "alpha_ideal")?.cells[1]).toBe("");
  expect(defs.rows.find((row) => row.cells[0] === "cl_ideal")?.cells[1]).toBe("0");
  expect(defs.rows.find((row) => row.cells[0] === "cla")?.cells[1]).toBe("1.0000e-6");
  expect(defs.rows.find((row) => row.cells[0] === "xac")?.cells[1]).toBe("1.0000e+4");
  expect(tab(withSections, "Sections").figures.some((item) => item.title === "Other coefficients")).toBe(
    false,
  );

  const missing = aeroTabs({ datcom: { cl: [0.1], alpha: [0] } }, null, null);
  expect(tab(missing, "Sections").figures.some((item) => item.title === "Section definition")).toBe(
    false,
  );
});

it("lists Tornado L in other coefficients and skips CL", () => {
  const tabs = aeroTabs(
    {
      datcom: {
        high_lift: [{ delta: [0.5, 1.5], dcl_max: 0.1, ignored: [4] }],
      },
      tornado: {
        CL: [0.9],
        L: [1.25],
        Zed: [3],
        tooLong: [1, 2, 3, 4, 5, 6, 7, 8, 9],
        grid: [
          [1, 2],
          [3, 4],
        ],
        spanwise: [{ y: [1], Cl: [0.2] }],
      },
      avl: { bonus: 2.5 },
      flow5: { L: [7] },
    },
    null,
    null,
  );
  const leftover = table(tab(tabs, "Sections"), "Other coefficients");
  expect(leftover.columns).toEqual(["Quantity", "1", "2"]);
  expect(leftover.rows).toEqual([
    { header: true, cells: ["DATCOM high-lift", "", ""] },
    { cells: ["HL0 delta", "0.5", "1.5"] },
    { cells: ["HL0 dcl_max", "0.1", ""] },
    { header: true, cells: ["Tornado", "", ""] },
    { cells: ["L", "1.25", ""] },
    { cells: ["Zed", "3", ""] },
    { header: true, cells: ["AVL", "", ""] },
    { cells: ["bonus", "2.5", ""] },
  ]);
  const quantities = leftover.rows.map((row) => row.cells[0]);
  expect(quantities).not.toContain("CL");
  expect(quantities).not.toContain("tooLong");
  expect(quantities).not.toContain("grid");
  expect(quantities).not.toContain("spanwise");
  expect(quantities).not.toContain("ignored");
  expect(leftover.rows.some((row) => row.cells.includes("7"))).toBe(false);
});

it("uses a Value column when every leftover row has one number", () => {
  const tabs = aeroTabs({ tornado: { L: [1.25], CL: [0.9] } }, null, null);
  const leftover = table(tab(tabs, "Sections"), "Other coefficients");
  expect(leftover.columns).toEqual(["Quantity", "Value"]);
  expect(leftover.rows).toEqual([
    { header: true, cells: ["Tornado", ""] },
    { cells: ["L", "1.25"] },
  ]);
});

function displayName(series: OverlayPointSeries): string {
  return series.label ?? series.solver;
}

it("threads the sideslip from aeroTabs into the series labels", () => {
  const raws: SolverRaws = {
    datcom: { alpha: [0, 2], cl: [0.1, 0.2] },
    avl: { alpha: [0, 2], CLtot: [0.1, 0.2] },
  };
  const swept = aeroTabs(raws, null, null, 5);
  expect(lines(tab(swept, "Forces"), "CL").series.map(displayName)).toEqual([
    "datcom (beta=0)",
    "avl (beta=0)",
  ]);
  const upright = aeroTabs(raws, null, null);
  expect(lines(tab(upright, "Forces"), "CL").series.map(displayName)).toEqual(["datcom", "avl"]);
});

it("labels the flow5 derivative panels at a sideslip", () => {
  const raws: SolverRaws = {
    tornado: { CL_a: PER_RAD },
    flow5: { CLa: PER_RAD },
  };
  const swept = aeroTabs(raws, null, null, 5);
  expect(lines(tab(swept, "Derivatives"), "CLα").series.map(displayName)).toEqual([
    "tornado",
    "flow5 (beta=0)",
  ]);
});

it("leaves the spanwise panels unlabelled at a sideslip", () => {
  const swept = aeroTabs({ tornado: {} }, null, { y: [0, 1], Cl: [0.2, 0.3] }, 5);
  const span = lines(tab(swept, "Spanwise"), "Spanwise lift").series;
  expect(span.map((item) => item.label)).toEqual([undefined]);
  expect(span.map(seriesLegend)).toEqual(["Prandtl"]);
});
