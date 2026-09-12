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
      if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
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

export function svgPolyline(
  xs: number[],
  ys: number[],
  width: number,
  height: number,
  pad = 8,
  domain?: PlotDomain,
): string {
  if (xs.length === 0 || ys.length === 0) return "";
  const n = Math.min(xs.length, ys.length);
  const xmin = domain?.xmin ?? Math.min(...xs.slice(0, n));
  const xmax = domain?.xmax ?? Math.max(...xs.slice(0, n));
  const ymin = domain?.ymin ?? Math.min(...ys.slice(0, n));
  const ymax = domain?.ymax ?? Math.max(...ys.slice(0, n));
  const dx = xmax - xmin || 1;
  const dy = ymax - ymin || 1;
  const pts: string[] = [];
  for (let i = 0; i < n; i++) {
    const px = pad + ((xs[i] - xmin) / dx) * (width - 2 * pad);
    const py = height - pad - ((ys[i] - ymin) / dy) * (height - 2 * pad);
    pts.push(`${px},${py}`);
  }
  return pts.join(" ");
}
