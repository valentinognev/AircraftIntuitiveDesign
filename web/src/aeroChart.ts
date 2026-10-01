import type { ControlBars, HingeBars } from "./aeroFigures";
import type { OverlayPointSeries, SolverRaw, SolverRaws } from "./coeffOverlay";
import { plotDomain, type PlotDomain, type PlotRect, type PlotSeries } from "./payload";

/** DATCOM prints NDM / ND as 99999; drop |y| >= 99998. */
const ND_ABS = 99998;

const SOLVERS = ["datcom", "tornado", "avl", "flow5"] as const;

export type BarSlot = { key: string; value: number | null };
export type BarCategory = { label: string; slots: BarSlot[] };

export type LaidOutBar = {
  key: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
};

export type BarChartGeometry = {
  domain: PlotDomain | null;
  bars: LaidOutBar[];
  labels: { label: string; x: number }[];
};

export function knownSolverRaws(raws: Record<string, unknown>): SolverRaws {
  const out: SolverRaws = {};
  for (const key of SOLVERS) {
    const value = raws[key];
    if (value && typeof value === "object" && !Array.isArray(value)) {
      out[key] = value as SolverRaw;
    }
  }
  return out;
}

export function hasSolverRaw(raws: SolverRaws): boolean {
  return SOLVERS.some((key) => raws[key] != null);
}

export function stabilityAlphaOf(st: { alpha?: unknown } | null | undefined): number | null {
  const alpha = st?.alpha;
  return typeof alpha === "number" && Number.isFinite(alpha) ? alpha : null;
}

export function seriesLegend(series: { name?: string; solver: string }): string {
  return series.name ? series.name : series.solver;
}

function usableY(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && Math.abs(value) < ND_ABS;
}

/** Line samples plus each hline's first y (and its x, when it has any). */
export function lineSeriesDomain(series: OverlayPointSeries[]): PlotDomain | null {
  const lines: PlotSeries[] = series
    .filter((s) => s.kind === "line")
    .map((s) => ({
      solver: s.solver,
      stroke: s.stroke,
      alpha: s.x,
      cl: s.y,
      cd: [],
      cm: [],
    }));
  let domain = plotDomain(lines, (s) => s.cl);
  for (const s of series) {
    if (s.kind !== "hline") continue;
    const y = s.y[0];
    if (!usableY(y)) continue;
    const xs = s.x.filter((v) => Number.isFinite(v));
    if (!domain) {
      const xmin = xs.length ? Math.min(...xs) : 0;
      const xmax = xs.length ? Math.max(...xs) : xmin;
      domain = { xmin, xmax, ymin: y, ymax: y };
      continue;
    }
    if (y < domain.ymin) domain.ymin = y;
    if (y > domain.ymax) domain.ymax = y;
    if (xs.length) {
      const xmin = Math.min(...xs);
      const xmax = Math.max(...xs);
      if (xmin < domain.xmin) domain.xmin = xmin;
      if (xmax > domain.xmax) domain.xmax = xmax;
    }
  }
  return domain;
}

/** Horizontal segment across the axes box at y. */
export function hlineSegment(
  y: number,
  domain: PlotDomain,
  plot: PlotRect,
): { x1: number; y1: number; x2: number; y2: number } | null {
  if (!Number.isFinite(y) || Math.abs(y) >= ND_ABS) return null;
  const dy = domain.ymax - domain.ymin || 1;
  const py = plot.y + plot.height - ((y - domain.ymin) / dy) * plot.height;
  return { x1: plot.x, y1: py, x2: plot.x + plot.width, y2: py };
}

export function lineLegends(series: OverlayPointSeries[]): { label: string; stroke: string }[] {
  const seen = new Set<string>();
  const out: { label: string; stroke: string }[] = [];
  for (const s of series) {
    const label = seriesLegend(s);
    if (seen.has(label)) continue;
    seen.add(label);
    out.push({ label, stroke: s.stroke });
  }
  return out;
}

export function groupedBarCategories(
  groups: { label: string; tornado: number | null; avl: number | null }[],
): BarCategory[] {
  return groups.map((group) => ({
    label: group.label,
    slots: [
      { key: "tornado", value: group.tornado },
      { key: "avl", value: group.avl },
    ],
  }));
}

export function controlBarCategories(figure: ControlBars): BarCategory[] {
  const categories: BarCategory[] = figure.groups.map((group) => ({
    label: group.label,
    slots: [
      { key: "dcl", value: group.dcl },
      { key: "dcm", value: group.dcm },
    ],
  }));
  for (const sample of figure.tornado) {
    for (const value of sample.values) {
      categories.push({
        label: sample.key,
        slots: [{ key: sample.key, value }],
      });
    }
  }
  return categories;
}

export function hingeBarCategories(figure: HingeBars): BarCategory[] {
  return figure.groups.map((group) => ({
    label: group.label,
    slots: [
      { key: "cha", value: group.cha },
      { key: "chd", value: group.chd },
      { key: "dclMax", value: group.dclMax },
    ],
  }));
}

export function layoutBars(categories: BarCategory[], plot: PlotRect): BarChartGeometry {
  const n = categories.length;
  const labels = categories.map((cat, i) => ({
    label: cat.label,
    x: plot.x + ((i + 0.5) * plot.width) / Math.max(n, 1),
  }));
  const finite: number[] = [];
  for (const cat of categories) {
    for (const slot of cat.slots) {
      if (usableY(slot.value)) finite.push(slot.value);
    }
  }
  if (n === 0 || finite.length === 0) return { domain: null, bars: [], labels };

  const ymin = Math.min(0, ...finite);
  const ymax = Math.max(0, ...finite);
  const domain: PlotDomain = { xmin: -0.5, xmax: n - 0.5, ymin, ymax };
  const dy = ymax - ymin || 1;
  const yOf = (value: number) => plot.y + plot.height - ((value - ymin) / dy) * plot.height;
  const baseline = yOf(0);
  const bars: LaidOutBar[] = [];
  const groupWidth = plot.width / n;
  categories.forEach((cat, i) => {
    const center = plot.x + (i + 0.5) * groupWidth;
    const slots = cat.slots.length || 1;
    const inner = groupWidth * 0.8;
    const barWidth = inner / slots;
    cat.slots.forEach((slot, s) => {
      if (!usableY(slot.value)) return;
      const yVal = yOf(slot.value);
      const top = Math.min(baseline, yVal);
      const height = Math.abs(yVal - baseline);
      if (!(height > 0)) return;
      const pad = barWidth * 0.08;
      bars.push({
        key: slot.key,
        label: cat.label,
        x: center - inner / 2 + s * barWidth + pad,
        y: top,
        width: Math.max(barWidth - 2 * pad, 0),
        height,
      });
    });
  });
  return { domain, bars, labels };
}

const BAR_LEGEND: Record<string, string> = {
  tornado: "Tornado",
  avl: "AVL",
  dcl: "dcl",
  dcm: "dcm",
  cha: "cha",
  chd: "chd",
  dclMax: "dclMax",
};

export function barLegend(categories: BarCategory[]): { key: string; label: string }[] {
  const seen = new Set<string>();
  const out: { key: string; label: string }[] = [];
  for (const cat of categories) {
    for (const slot of cat.slots) {
      if (!usableY(slot.value) || seen.has(slot.key)) continue;
      seen.add(slot.key);
      out.push({ key: slot.key, label: BAR_LEGEND[slot.key] ?? slot.key });
    }
  }
  return out;
}

/** Tornado red; the second DATCOM bar in a group is blue so the pair stays distinct. */
export function barFill(key: string): string {
  if (key === "tornado" || key.endsWith("_d")) return "red";
  if (key === "dcm" || key === "chd") return "#1d4ed8";
  if (key === "dclMax") return "#64748b";
  return "currentColor";
}
