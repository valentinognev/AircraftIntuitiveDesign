export type HandshakePayload = {
  source: string;
  solver: string;
  axes: { mach: number[]; alpha: number[]; beta: number[] };
  tables: { cl: number[][]; cd: number[][]; cm: number[][] };
  ref: Record<string, unknown>;
};

export type PlotSeries = {
  solver: string;
  stroke: string;
  alpha: number[];
  cl: number[];
  cd: number[];
  cm: number[];
};

/** DATCOM default; Tornado red; flow5 yellow (AID README). AVL uses DATCOM default. */
export function solverStroke(solver: string): string {
  if (solver === "tornado") return "red";
  if (solver === "flow5") return "yellow";
  return "currentColor";
}

function row(table: number[][] | undefined): number[] {
  const first = table?.[0];
  return Array.isArray(first) ? first.map(Number) : [];
}

export function seriesFromPayload(payload: HandshakePayload): PlotSeries {
  return {
    solver: payload.solver,
    stroke: solverStroke(payload.solver),
    alpha: payload.axes.alpha.map(Number),
    cl: row(payload.tables.cl),
    cd: row(payload.tables.cd),
    cm: row(payload.tables.cm),
  };
}

export function overlaySeries(payloads: HandshakePayload[]): PlotSeries[] {
  return payloads.map(seriesFromPayload);
}

export function stabilityText(st: { summary?: unknown } | null | undefined): string {
  if (st == null || !Array.isArray(st.summary)) return "";
  return st.summary.map(String).join("\n");
}

export type PlotDomain = { xmin: number; xmax: number; ymin: number; ymax: number };

/** DATCOM prints NDM / ND as 99999; Qt overlay drops |y| >= 99998. */
const ND_ABS = 99998;

function usableSample(x: number, y: number): boolean {
  return Number.isFinite(x) && Number.isFinite(y) && Math.abs(y) < ND_ABS;
}

export function plotDomain(
  series: PlotSeries[],
  pick: (s: PlotSeries) => number[],
): PlotDomain | null {
  let xmin = Infinity;
  let xmax = -Infinity;
  let ymin = Infinity;
  let ymax = -Infinity;
  let any = false;
  for (const s of series) {
    const ys = pick(s);
    const n = Math.min(s.alpha.length, ys.length);
    for (let i = 0; i < n; i++) {
      const x = s.alpha[i];
      const y = ys[i];
      if (!usableSample(x, y)) continue;
      any = true;
      if (x < xmin) xmin = x;
      if (x > xmax) xmax = x;
      if (y < ymin) ymin = y;
      if (y > ymax) ymax = y;
    }
  }
  if (!any) return null;
  return { xmin, xmax, ymin, ymax };
}

export type PlotRect = { x: number; y: number; width: number; height: number };

export type ChartLayout = { width: number; height: number; plot: PlotRect };

/** Inner axes box. Left and bottom margins hold tick labels, matching a Qt axes frame. */
export function chartLayout(width = 640, height = 220): ChartLayout {
  const left = 52;
  const right = 12;
  const top = 8;
  const bottom = 54;
  return {
    width,
    height,
    plot: {
      x: left,
      y: top,
      width: width - left - right,
      height: height - top - bottom,
    },
  };
}

export type AxisTick = { value: number; label: string };

function formatTick(value: number): string {
  return String(Number(value.toPrecision(10)));
}

function roundTick(value: number): number {
  return Number(value.toPrecision(12));
}

/** Nice ticks on [min, max], preferring a step that lands on both ends. */
export function axisTicks(min: number, max: number, target = 5): AxisTick[] {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [];
  if (!(max > min)) return [{ value: min, label: formatTick(min) }];
  const span = max - min;
  const exp = Math.floor(Math.log10(span / target));
  const nice = [1, 2, 2.5, 4, 5, 10];
  let best: { score: number; values: number[] } | null = null;
  for (let e = exp - 1; e <= exp + 1; e++) {
    const mag = 10 ** e;
    for (const n of nice) {
      const step = n * mag;
      if (!(step > 0)) continue;
      const start = Math.ceil((min - step * 1e-9) / step) * step;
      const end = Math.floor((max + step * 1e-9) / step) * step;
      if (end + step * 1e-9 < start) continue;
      const count = Math.round((end - start) / step) + 1;
      if (count < 2 || count > 8) continue;
      const values = Array.from({ length: count }, (_, i) => roundTick(start + i * step));
      const lead = (values[0] - min) / span;
      const trail = (max - values[values.length - 1]) / span;
      const score = Math.abs(count - target) + (lead + trail) * 5;
      if (best == null || score < best.score) best = { score, values };
    }
  }
  const values = best?.values ?? [min, max];
  return values.map((value) => ({ value, label: formatTick(value) }));
}

export type GridLine = { x1: number; y1: number; x2: number; y2: number };

export function gridLines(domain: PlotDomain, plot: PlotRect): GridLine[] {
  const lines: GridLine[] = [];
  const dx = domain.xmax - domain.xmin || 1;
  const dy = domain.ymax - domain.ymin || 1;
  for (const tick of axisTicks(domain.xmin, domain.xmax)) {
    const x = plot.x + ((tick.value - domain.xmin) / dx) * plot.width;
    lines.push({ x1: x, y1: plot.y, x2: x, y2: plot.y + plot.height });
  }
  for (const tick of axisTicks(domain.ymin, domain.ymax)) {
    const y = plot.y + plot.height - ((tick.value - domain.ymin) / dy) * plot.height;
    lines.push({ x1: plot.x, y1: y, x2: plot.x + plot.width, y2: y });
  }
  return lines;
}

export function svgPolyline(
  xs: number[],
  ys: number[],
  width: number,
  height: number,
  pad = 8,
  domain?: PlotDomain,
  plot?: PlotRect,
): string {
  if (xs.length === 0 || ys.length === 0) return "";
  const n = Math.min(xs.length, ys.length);
  const kept: { x: number; y: number }[] = [];
  for (let i = 0; i < n; i++) {
    if (usableSample(xs[i], ys[i])) kept.push({ x: xs[i], y: ys[i] });
  }
  if (kept.length === 0) return "";
  const xmin = domain?.xmin ?? Math.min(...kept.map((p) => p.x));
  const xmax = domain?.xmax ?? Math.max(...kept.map((p) => p.x));
  const ymin = domain?.ymin ?? Math.min(...kept.map((p) => p.y));
  const ymax = domain?.ymax ?? Math.max(...kept.map((p) => p.y));
  const dx = xmax - xmin || 1;
  const dy = ymax - ymin || 1;
  const pts: string[] = [];
  for (const p of kept) {
    const px = plot
      ? plot.x + ((p.x - xmin) / dx) * plot.width
      : pad + ((p.x - xmin) / dx) * (width - 2 * pad);
    const py = plot
      ? plot.y + plot.height - ((p.y - ymin) / dy) * plot.height
      : height - pad - ((p.y - ymin) / dy) * (height - 2 * pad);
    pts.push(`${px},${py}`);
  }
  return pts.join(" ");
}
