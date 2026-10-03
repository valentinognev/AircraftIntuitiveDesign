import { solverStroke } from "./payload";
import {
  seriesDerivative,
  seriesVsAlpha,
  type OverlayPointSeries,
  type SolverRaw,
  type SolverRaws,
} from "./coeffOverlay";

export type LineFigure = {
  kind: "lines";
  title: string;
  ylabel: string;
  xlabel: string;
  series: OverlayPointSeries[];
};

export type BarGroup = { label: string; tornado: number | null; avl: number | null };
export type BarFigure = { kind: "bars"; title: string; groups: BarGroup[] };

export type TableFigure = {
  kind: "table";
  title: string;
  columns: string[];
  rows: { cells: string[]; header?: boolean }[];
};

export type ControlBars = {
  kind: "control-bars";
  title: string;
  groups: { label: string; dcl: number | null; dcm: number | null }[];
  tornado: { key: string; values: number[] }[];
};

export type HingeBars = {
  kind: "hinge-bars";
  title: string;
  groups: { label: string; cha: number | null; chd: number | null; dclMax: number | null }[];
};

export type AeroFigure = LineFigure | BarFigure | TableFigure | ControlBars | HingeBars;
export type AeroTab = { id: string; label: string; figures: AeroFigure[] };

type VsSpec = {
  datcom?: string;
  tornado?: [string, string | null];
  avl?: string;
  flow5?: string;
};

type DerivSpec = { datcom?: string; tornado?: string; avl?: string; flow5?: string };

/** DATCOM prints NDM / ND as 99999; drop |y| >= 99998. */
const ND_ABS = 99998;

const SECTION_FIELDS = [
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
] as const;

const HL_KEYS = ["delta", "dcl_max", "dcd_min", "clad", "cha", "chd"] as const;

const TORNADO_CONTROL_KEYS = [
  "CL_d",
  "Cm_d",
  "CD_d",
  "Cl_d",
  "Cn_d",
  "CY_d",
  "CZ_d",
  "CX_d",
  "CC_d",
] as const;

/** Qt `_SKIP_LEFTOVER` — keys already drawn on the other tabs. */
const SKIP_LEFTOVER = new Set([
  "cp",
  "sonicpanels",
  "sonicWarning",
  "sonicCP",
  "sonicFraction",
  "F",
  "M",
  "FORCE",
  "MOMENTS",
  "gamma",
  "dwcond",
  "spanwise",
  "vlm_mode",
  "surface",
  "alpha",
  "cl",
  "cd",
  "cm",
  "cn",
  "ca",
  "xcp",
  "cla",
  "cma",
  "cyb",
  "cnb",
  "clb",
  "q_qinf",
  "epslon",
  "depsda",
  "high_lift",
  "sections",
  "mach",
  "alt",
  "CL",
  "CD",
  "CY",
  "CZ",
  "CX",
  "Cl",
  "Cm",
  "Cn",
  "CL_a",
  "CD_a",
  "CY_a",
  "CZ_a",
  "CX_a",
  "Cl_a",
  "Cm_a",
  "Cn_a",
  "CY_b",
  "Cn_b",
  "Cl_b",
  "Cl_P",
  "Cm_Q",
  "Cn_R",
  "CL_P",
  "CL_Q",
  "CL_R",
  "CLwing",
  "CL_d",
  "Cm_d",
  "CD_d",
  "CLtot",
  "CDtot",
  "CYtot",
  "CZtot",
  "CXtot",
  "Cltot",
  "Cmtot",
  "Cntot",
  "CLa",
  "Cma",
  "CYb",
  "Cnb",
  "Clb",
  "Clp",
  "Cmq",
  "Cnr",
  "CLp",
  "CLq",
  "CLr",
  "CDind",
  "CDvis",
  "e",
  "NP",
  "CL0",
  "Cm0",
]);

const RATE_GROUPS: { label: string; tornado: string; avl: string }[] = [
  { label: "Clp", tornado: "Cl_P", avl: "Clp" },
  { label: "Cmq", tornado: "Cm_Q", avl: "Cmq" },
  { label: "Cnr", tornado: "Cn_R", avl: "Cnr" },
  { label: "CLp", tornado: "CL_P", avl: "CLp" },
  { label: "CLq", tornado: "CL_Q", avl: "CLq" },
  { label: "CLr", tornado: "CL_R", avl: "CLr" },
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function has(raw: SolverRaw | undefined, key: string): boolean {
  return !!raw && Object.prototype.hasOwnProperty.call(raw, key);
}

function finiteScalar(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (!Array.isArray(value)) return null;
  for (const item of value) {
    if (typeof item === "number" && Number.isFinite(item)) return item;
  }
  return null;
}

function alphaLines(
  title: string,
  raws: SolverRaws,
  stabilityAlpha: number | null,
  spec: VsSpec,
  beta: number,
): LineFigure {
  return {
    kind: "lines",
    title,
    ylabel: title,
    xlabel: "α (deg)",
    series: seriesVsAlpha(raws, stabilityAlpha, spec, beta),
  };
}

function derivLines(
  title: string,
  raws: SolverRaws,
  stabilityAlpha: number | null,
  spec: DerivSpec,
  beta: number,
): LineFigure {
  return {
    kind: "lines",
    title,
    ylabel: title,
    xlabel: "α (deg)",
    series: seriesDerivative(raws, stabilityAlpha, spec, beta),
  };
}

function lineFigure(title: string, ylabel: string, xlabel: string, series: OverlayPointSeries[]): LineFigure {
  return { kind: "lines", title, ylabel, xlabel, series };
}

function forceExtras(raws: SolverRaws): BarGroup[] {
  const groups: BarGroup[] = [];
  const tornado = raws.tornado;
  for (const key of ["CLwing", "CDwing", "CYwing"] as const) {
    if (!has(tornado, key)) continue;
    const value = tornado?.[key];
    const wings =
      typeof value === "number"
        ? [value]
        : Array.isArray(value)
          ? value.map((item) => (typeof item === "number" ? item : Number.NaN))
          : [];
    const shown = wings.slice(0, 4);
    for (let i = 0; i < shown.length; i++) {
      if (!Number.isFinite(shown[i])) continue;
      const suffix = wings.length > 1 ? String(i + 1) : "";
      groups.push({ label: `${key}${suffix}`, tornado: shown[i], avl: null });
    }
  }
  if (has(tornado, "CC")) {
    const cc = finiteScalar(tornado?.CC);
    if (cc != null) groups.push({ label: "CC", tornado: cc, avl: null });
  }
  const avl = raws.avl;
  for (const [key, label] of [
    ["CDind", "CDind"],
    ["CDvis", "CDvis"],
    ["e", "e"],
    ["NP", "Xnp"],
  ] as const) {
    if (!has(avl, key)) continue;
    const raw = avl?.[key];
    if (Array.isArray(raw) && raw.length !== 1) continue;
    const value = finiteScalar(raw);
    if (value == null) continue;
    groups.push({ label, tornado: null, avl: value });
  }
  return groups;
}

function rateAvl(value: unknown): number | null {
  if (Array.isArray(value) && value.length !== 1) return null;
  return finiteScalar(value);
}

function rateBars(raws: SolverRaws): BarGroup[] {
  return RATE_GROUPS.map((group) => ({
    label: group.label,
    tornado: finiteScalar(raws.tornado?.[group.tornado]),
    avl: rateAvl(raws.avl?.[group.avl]),
  }));
}

function blockLabel(block: Record<string, unknown>, max: number): string {
  if (typeof block.config === "string") return block.config.slice(0, max);
  const delta = finiteScalar(block.delta) ?? 0;
  return `δ=${delta}`;
}

function flattenFinite(value: unknown): number[] {
  const out: number[] = [];
  const walk = (item: unknown) => {
    if (typeof item === "number" && Number.isFinite(item)) out.push(item);
    else if (Array.isArray(item)) item.forEach(walk);
  };
  walk(value);
  return out;
}

function pairDatcom(xRaw: unknown[], yRaw: unknown[]): { x: number[]; y: number[] } {
  const n = Math.min(xRaw.length, yRaw.length);
  const x: number[] = [];
  const y: number[] = [];
  for (let i = 0; i < n; i++) {
    const xv = xRaw[i];
    const yv = yRaw[i];
    if (typeof xv !== "number" || typeof yv !== "number") continue;
    if (!Number.isFinite(xv) || !Number.isFinite(yv)) continue;
    if (Math.abs(yv) >= ND_ABS) continue;
    x.push(xv);
    y.push(yv);
  }
  return { x, y };
}

/**
 * `(beta=0)` for the panels the overlay functions do not build, so a DATCOM or AVL
 * curve shown there is marked the same way as one shown on a Forces or Derivatives
 * panel. Only those two solvers need it: they cannot fly a sideslip, and Tornado's
 * spanwise curves really are at the requested one.
 *
 * `base` is the display name the legend already shows, so a named curve keeps its
 * name — the spanwise handbook curve keeps a bare "Prandtl", not "Prandtl (beta=0)".
 */
function betaSuffix(base: string, beta: number): { label?: string } {
  return beta === 0 ? {} : { label: `${base} (beta=0)` };
}

/** The same suffix on a table group header, which names its solver just as a legend does. */
function betaTitle(title: string, beta: number): string {
  return beta === 0 ? title : `${title} (beta=0)`;
}

function controlFigures(raws: SolverRaws, beta: number): AeroFigure[] {
  const blocks = Array.isArray(raws.datcom?.high_lift) ? raws.datcom.high_lift : [];
  const records = blocks.filter(isRecord);
  const increments: ControlBars = {
    kind: "control-bars",
    title: "Control increments",
    groups: records.map((block) => ({
      label: blockLabel(block, 24),
      dcl: finiteScalar(block.dcl),
      dcm: finiteScalar(block.dcm),
    })),
    tornado: TORNADO_CONTROL_KEYS.filter((key) => has(raws.tornado, key)).map((key) => ({
      key,
      values: flattenFinite(raws.tornado?.[key]),
    })),
  };

  const dcdi: OverlayPointSeries[] = [];
  for (const block of records) {
    if (!Array.isArray(block.dcdi_alpha) || !Array.isArray(block.dcdi)) continue;
    const samples = pairDatcom(block.dcdi_alpha, block.dcdi);
    dcdi.push({
      solver: "datcom",
      stroke: solverStroke("datcom"),
      kind: "line",
      x: samples.x,
      y: samples.y,
      ...betaSuffix("datcom", beta),
    });
  }

  const surfaces = raws.avl?.surface;
  const surfaceObjects =
    Array.isArray(surfaces) && surfaces.length > 0 && surfaces.every(isRecord) ? surfaces : null;
  let extra: AeroFigure;
  if (surfaceObjects) {
    extra = lineFigure(
      "AVL control deflection",
      "δ (deg)",
      "",
      [
        {
          solver: "avl",
          stroke: solverStroke("avl"),
          kind: "line",
          x: surfaceObjects.map((_, index) => index),
          y: surfaceObjects.map((surface) => finiteScalar(surface.angle) ?? 0),
          ...betaSuffix("avl", beta),
        },
      ],
    );
  } else if (records.length > 0) {
    const hinge: HingeBars = {
      kind: "hinge-bars",
      title: "DATCOM hinge / max-lift",
      groups: records.map((block) => ({
        label: blockLabel(block, 16),
        cha: finiteScalar(block.cha),
        chd: finiteScalar(block.chd),
        dclMax: finiteScalar(block.dcl_max),
      })),
    };
    extra = hinge;
  } else {
    extra = lineFigure("Control extras", "", "", []);
  }

  return [increments, lineFigure("ΔCDi", "ΔCDi", "α (deg)", dcdi), extra];
}

function numberArray(value: unknown): number[] | null {
  if (!Array.isArray(value)) return null;
  if (!value.every((item) => typeof item === "number" && Number.isFinite(item))) return null;
  return value as number[];
}

/**
 * The handbook's Prandtl curve is a closed-form `lifting_line` solution that never
 * reads AERO["BETA"], so it really is at the aircraft's sideslip and carries no
 * `(beta=0)` mark — same for Tornado's spanwise curves.
 */
function spanwiseSeries(
  raws: SolverRaws,
  handbook: { y: number[]; Cl: number[] } | null,
): OverlayPointSeries[] {
  const series: OverlayPointSeries[] = [];
  if (handbook && Array.isArray(handbook.y) && Array.isArray(handbook.Cl) && handbook.y.length === handbook.Cl.length) {
    const y = numberArray(handbook.y);
    const cl = numberArray(handbook.Cl);
    if (y && cl) {
      series.push({
        solver: "datcom",
        stroke: solverStroke("datcom"),
        kind: "line",
        name: "Prandtl",
        x: y,
        y: cl,
      });
    }
  }
  const wings = raws.tornado?.spanwise;
  if (!Array.isArray(wings)) return series;
  for (const wing of wings) {
    if (!isRecord(wing)) continue;
    const y = numberArray(wing.y);
    const cl = numberArray(wing.Cl);
    if (!y || !cl || y.length !== cl.length) continue;
    const surface = typeof wing.name === "string" && wing.name ? wing.name : "Wing";
    series.push({
      solver: "tornado",
      stroke: solverStroke("tornado"),
      kind: "line",
      name: `Tornado ${surface}`,
      x: y,
      y: cl,
    });
  }
  return series;
}

function fmtNumber(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "";
  const abs = Math.abs(value);
  if (abs < 1e-10) return "0";
  if (abs >= 1e-5 && abs < 1e4) return value.toFixed(6).replace(/0+$/, "").replace(/\.$/, "");
  return value.toExponential(4);
}

function sectionTable(raws: SolverRaws): TableFigure | null {
  const sections = raws.datcom?.sections;
  if (!isRecord(sections) || Object.keys(sections).length === 0) return null;
  const wing = isRecord(sections.wing) ? sections.wing : {};
  const ht = isRecord(sections.ht) ? sections.ht : {};
  const vt = isRecord(sections.vt) ? sections.vt : {};
  return {
    kind: "table",
    title: "Section definition",
    columns: ["Quantity", "Wing", "HT", "VT"],
    rows: SECTION_FIELDS.map((field) => ({
      cells: [field, fmtNumber(wing[field]), fmtNumber(ht[field]), fmtNumber(vt[field])],
    })),
  };
}

/** Scalar or a 1-d numeric array. `limit` slices; `rejectLonger` drops arrays past that length. */
function numbers1d(value: unknown, limit: number, rejectLonger: boolean): number[] | null {
  if (typeof value === "number") return [value];
  if (!Array.isArray(value) || value.length === 0) return null;
  if (rejectLonger && value.length > limit) return null;
  if (!value.every((item) => typeof item === "number")) return null;
  return (value as number[]).slice(0, limit);
}

function leftoverTable(raws: SolverRaws, beta: number): TableFigure | null {
  const groups: { title: string; rows: { qty: string; vals: number[] }[] }[] = [];
  const hlRows: { qty: string; vals: number[] }[] = [];
  const blocks = raws.datcom?.high_lift;
  if (Array.isArray(blocks)) {
    blocks.forEach((block, index) => {
      if (!isRecord(block)) return;
      for (const key of HL_KEYS) {
        if (!has(block, key)) continue;
        const vals = numbers1d(block[key], 8, false);
        if (!vals) continue;
        hlRows.push({ qty: `HL${index} ${key}`, vals });
      }
    });
  }
  if (hlRows.length > 0) groups.push({ title: betaTitle("DATCOM high-lift", beta), rows: hlRows });

  for (const [title, raw] of [
    ["Tornado", raws.tornado],
    ["AVL", raws.avl],
  ] as const) {
    if (!raw) continue;
    const rows: { qty: string; vals: number[] }[] = [];
    for (const key of Object.keys(raw).sort()) {
      if (SKIP_LEFTOVER.has(key)) continue;
      const vals = numbers1d(raw[key], 8, true);
      if (!vals) continue;
      rows.push({ qty: key, vals });
    }
    if (rows.length > 0) {
      groups.push({ title: title === "Tornado" ? title : betaTitle(title, beta), rows });
    }
  }
  if (groups.length === 0) return null;

  let maxN = 1;
  for (const group of groups) {
    for (const row of group.rows) maxN = Math.max(maxN, row.vals.length);
  }
  const columns = ["Quantity", ...(maxN === 1 ? ["Value"] : Array.from({ length: maxN }, (_, i) => String(i + 1)))];
  const rows: TableFigure["rows"] = [];
  for (const group of groups) {
    rows.push({ header: true, cells: [group.title, ...Array(maxN).fill("")] });
    for (const row of group.rows) {
      const cells = [row.qty, ...row.vals.map((value) => fmtNumber(value))];
      while (cells.length < columns.length) cells.push("");
      rows.push({ cells });
    }
  }
  return { kind: "table", title: "Other coefficients", columns, rows };
}

export function aeroTabs(
  raws: SolverRaws,
  stabilityAlpha: number | null,
  handbook: { y: number[]; Cl: number[] } | null,
  beta = 0,
): AeroTab[] {
  const section = sectionTable(raws);
  const leftover = leftoverTable(raws, beta);
  const sectionFigures: AeroFigure[] = [];
  if (section) sectionFigures.push(section);
  if (leftover) sectionFigures.push(leftover);

  return [
    {
      id: "forces",
      label: "Forces",
      figures: [
        alphaLines("CL", raws, stabilityAlpha, {
          datcom: "cl",
          tornado: ["CL", "CL_a"],
          avl: "CLtot",
          flow5: "CL",
        }, beta),
        alphaLines("CD", raws, stabilityAlpha, {
          datcom: "cd",
          tornado: ["CD", "CD_a"],
          avl: "CDtot",
          flow5: "CD",
        }, beta),
        alphaLines("CY", raws, stabilityAlpha, {
          tornado: ["CY", "CY_a"],
          avl: "CYtot",
        }, beta),
        alphaLines("CN", raws, stabilityAlpha, {
          datcom: "cn",
          tornado: ["CZ", "CZ_a"],
          avl: "CZtot",
        }, beta),
        alphaLines("CA", raws, stabilityAlpha, {
          datcom: "ca",
          tornado: ["CX", "CX_a"],
          avl: "CXtot",
        }, beta),
        alphaLines("CDind", raws, stabilityAlpha, { avl: "CDind" }, beta),
        alphaLines("CDvis", raws, stabilityAlpha, { avl: "CDvis" }, beta),
        alphaLines("e", raws, stabilityAlpha, { avl: "e" }, beta),
        { kind: "bars", title: "Per-wing / AVL extras", groups: forceExtras(raws) },
      ],
    },
    {
      id: "moments",
      label: "Moments",
      figures: [
        alphaLines("Cm", raws, stabilityAlpha, {
          datcom: "cm",
          tornado: ["Cm", "Cm_a"],
          avl: "Cmtot",
          flow5: "Cm",
        }, beta),
        alphaLines("Cl", raws, stabilityAlpha, {
          tornado: ["Cl", "Cl_a"],
          avl: "Cltot",
        }, beta),
        alphaLines("Cn", raws, stabilityAlpha, {
          tornado: ["Cn", "Cn_a"],
          avl: "Cntot",
        }, beta),
        alphaLines("Xcp", raws, stabilityAlpha, { datcom: "xcp" }, beta),
        alphaLines("NP", raws, stabilityAlpha, { avl: "NP" }, beta),
      ],
    },
    {
      id: "derivatives",
      label: "Derivatives",
      figures: [
        derivLines("CLα", raws, stabilityAlpha, { datcom: "cla", tornado: "CL_a", avl: "CLa", flow5: "CLa" }, beta),
        derivLines("Cmα", raws, stabilityAlpha, { datcom: "cma", tornado: "Cm_a", avl: "Cma", flow5: "Cma" }, beta),
        derivLines("CYβ", raws, stabilityAlpha, { datcom: "cyb", tornado: "CY_b", avl: "CYb" }, beta),
        derivLines("Cnβ", raws, stabilityAlpha, { datcom: "cnb", tornado: "Cn_b", avl: "Cnb" }, beta),
        derivLines("Clβ", raws, stabilityAlpha, { datcom: "clb", tornado: "Cl_b", avl: "Clb" }, beta),
        ...RATE_GROUPS.map((group) =>
          derivLines(group.label, raws, stabilityAlpha, {
            tornado: group.tornado,
            avl: group.avl,
          }, beta),
        ),
        { kind: "bars", title: "p, q, r (per rad)", groups: rateBars(raws) },
      ],
    },
    {
      id: "downwash",
      label: "Downwash",
      figures: [
        alphaLines("ε", raws, stabilityAlpha, { datcom: "epslon" }, beta),
        alphaLines("dε/dα", raws, stabilityAlpha, { datcom: "depsda" }, beta),
        alphaLines("q/q∞", raws, stabilityAlpha, { datcom: "q_qinf" }, beta),
      ],
    },
    { id: "controls", label: "Controls", figures: controlFigures(raws, beta) },
    {
      id: "spanwise",
      label: "Spanwise",
      figures: [
        lineFigure("Spanwise lift", "Cl", "y (ft)", spanwiseSeries(raws, handbook)),
      ],
    },
    { id: "sections", label: "Sections", figures: sectionFigures },
  ];
}
