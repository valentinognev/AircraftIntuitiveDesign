import { solverStroke } from "./payload";

export type SolverRaw = Record<string, unknown>;
export type SolverRaws = {
  datcom?: SolverRaw;
  tornado?: SolverRaw;
  avl?: SolverRaw;
  flow5?: SolverRaw;
};
export type OverlayPointSeries = {
  solver: "datcom" | "tornado" | "avl" | "flow5";
  stroke: string;
  x: number[];
  y: number[];
  kind: "line" | "hline";
  /** Display override, set when the solver could not fly the condition it is plotted in. */
  label?: string;
  /** Spanwise curves name the handbook and Tornado wings. Other series omit it. */
  name?: string;
};

/** DATCOM prints NDM / ND as 99999; drop |y| >= 99998. */
const ND_ABS = 99998;

type SolverName = OverlayPointSeries["solver"];

/**
 * Solvers whose numbers cannot be the requested sideslip, so they need the
 * `(beta=0)` suffix when the flight is not upright.
 *
 * DATCOM's `$FLTCON` and AVL's run-case menu have no sideslip at all, so both stay
 * at beta = 0 whatever is asked of them. flow5's force channels *do* follow the
 * requested sideslip (`setBetaSpec`), but its twelve stability derivatives do not:
 * `computeStabilityDerivatives` builds its axes from `objects::windDirection(alpha, 0.0)`
 * (FLOW5/flow5-lib/analysis3d/panelanalysis.cpp:614, its WindDirection at :660), so every derivative is identical
 * at beta = 0, +5 and -5. Only Tornado's `state["betha"]` really flies the sideslip.
 */
const NO_SIDESLIP: ReadonlySet<SolverName> = new Set<SolverName>(["datcom", "avl"]);
const NO_SIDESLIP_DERIVATIVES: ReadonlySet<SolverName> = new Set<SolverName>([
  "datcom",
  "avl",
  "flow5",
]);

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/** A scalar, or the only entry of a one-element list. Longer lists are not one sample. */
function oneSample(value: unknown): number | null {
  if (Array.isArray(value)) return value.length === 1 ? finiteNumber(value[0]) : null;
  return finiteNumber(value);
}

/** Scalar coeff, or the first finite entry when Analyze stored a one-element list. */
function firstFinite(value: unknown): number | null {
  if (Array.isArray(value)) {
    for (const item of value) {
      const n = finiteNumber(item);
      if (n != null) return n;
    }
    return null;
  }
  return finiteNumber(value);
}

function has(raw: SolverRaw, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(raw, key);
}

function pairedSamples(
  xRaw: unknown,
  yRaw: unknown,
  stripNd: boolean,
): { x: number[]; y: number[] } {
  const xs = Array.isArray(xRaw) ? xRaw : [xRaw];
  const ys = Array.isArray(yRaw) ? yRaw : [yRaw];
  const n = Math.min(xs.length, ys.length);
  const x: number[] = [];
  const y: number[] = [];
  for (let i = 0; i < n; i++) {
    const xv = finiteNumber(xs[i]);
    const yv = finiteNumber(ys[i]);
    if (xv == null || yv == null) continue;
    if (stripNd && Math.abs(yv) >= ND_ABS) continue;
    x.push(xv);
    y.push(yv);
  }
  return { x, y };
}

function linspace(start: number, stop: number, count: number): number[] {
  if (count <= 0) return [];
  if (count === 1) return [start];
  const step = (stop - start) / (count - 1);
  const out = new Array<number>(count);
  for (let i = 0; i < count; i++) out[i] = start + step * i;
  out[0] = start;
  out[count - 1] = stop;
  return out;
}

function finiteAlpha(raw: SolverRaw | undefined): number[] {
  if (!raw || !has(raw, "alpha")) return [];
  const items = Array.isArray(raw.alpha) ? raw.alpha : [raw.alpha];
  const out: number[] = [];
  for (const item of items) {
    const n = finiteNumber(item);
    if (n != null) out.push(n);
  }
  return out;
}

export function alphaGrid(raws: SolverRaws, stabilityAlpha: number | null): number[] {
  const alpha = finiteAlpha(raws.datcom);
  if (alpha.length > 0) {
    let min = alpha[0];
    let max = alpha[0];
    for (const value of alpha) {
      if (value < min) min = value;
      if (value > max) max = value;
    }
    return linspace(min, max, 80);
  }
  if (typeof stabilityAlpha === "number" && Number.isFinite(stabilityAlpha)) {
    return linspace(Math.min(-10, stabilityAlpha), Math.max(20, stabilityAlpha), 100);
  }
  return [];
}

function series(
  solver: SolverName,
  x: number[],
  y: number[],
  kind: "line" | "hline",
  label?: string,
): OverlayPointSeries {
  return {
    solver,
    stroke: solverStroke(solver),
    x,
    y,
    kind,
    ...(label != null ? { label } : {}),
  };
}

/** `(beta=0)` for a solver that could not fly the requested sideslip, else nothing. */
function pinnedLabel(
  solver: SolverName,
  beta: number,
  pinned: ReadonlySet<SolverName>,
): string | undefined {
  if (beta === 0 || !pinned.has(solver)) return undefined;
  return `${solver} (beta=0)`;
}

/**
 * Alpha is degrees on the web raw. Slopes are per radian.
 * y = value + slope * deg2rad(gridDeg - a0Deg).
 */
function slopeLine(value: number, slope: number, a0Deg: number, gridDeg: number[]): number[] {
  const deg2rad = Math.PI / 180;
  return gridDeg.map((alpha) => value + slope * (alpha - a0Deg) * deg2rad);
}

export function seriesVsAlpha(
  raws: SolverRaws,
  stabilityAlpha: number | null,
  spec: {
    datcom?: string;
    tornado?: [string, string | null];
    avl?: string;
    flow5?: string;
  },
  beta = 0,
): OverlayPointSeries[] {
  const grid = alphaGrid(raws, stabilityAlpha);
  const out: OverlayPointSeries[] = [];

  const datcom = raws.datcom;
  if (
    spec.datcom &&
    datcom &&
    has(datcom, spec.datcom) &&
    has(datcom, "alpha")
  ) {
    const samples = pairedSamples(datcom.alpha, datcom[spec.datcom], true);
    out.push(series("datcom", samples.x, samples.y, "line", pinnedLabel("datcom", beta, NO_SIDESLIP)));
  }

  const tornado = raws.tornado;
  if (spec.tornado && tornado) {
    const [valKey, slopeKey] = spec.tornado;
    const value = firstFinite(tornado[valKey]);
    const slope = slopeKey ? firstFinite(tornado[slopeKey]) : null;
    if (value != null && slope != null) {
      const a0 = firstFinite(tornado.alpha) ?? 0;
      out.push(series("tornado", grid, slopeLine(value, slope, a0, grid), "line"));
    }
  }

  const avl = raws.avl;
  if (spec.avl && avl && has(avl, spec.avl) && has(avl, "alpha")) {
    const samples = pairedSamples(avl.alpha, avl[spec.avl], false);
    if (samples.x.length > 0) {
      out.push(series("avl", samples.x, samples.y, "line", pinnedLabel("avl", beta, NO_SIDESLIP)));
    }
  }

  const flow5 = raws.flow5;
  if (spec.flow5 && flow5 && has(flow5, spec.flow5) && has(flow5, "alpha")) {
    const samples = pairedSamples(flow5.alpha, flow5[spec.flow5], false);
    out.push(series("flow5", samples.x, samples.y, "line"));
  }

  return out;
}

export function seriesDerivative(
  raws: SolverRaws,
  stabilityAlpha: number | null,
  spec: { datcom?: string; tornado?: string; avl?: string; flow5?: string },
  beta = 0,
): OverlayPointSeries[] {
  const grid = alphaGrid(raws, stabilityAlpha);
  const out: OverlayPointSeries[] = [];

  const datcom = raws.datcom;
  if (
    spec.datcom &&
    datcom &&
    has(datcom, spec.datcom) &&
    has(datcom, "alpha")
  ) {
    const samples = pairedSamples(datcom.alpha, datcom[spec.datcom], true);
    out.push(
      series("datcom", samples.x, samples.y, "line", pinnedLabel("datcom", beta, NO_SIDESLIP_DERIVATIVES)),
    );
  }

  const horizontal = (
    solver: "tornado" | "flow5",
    key: string | undefined,
    raw: SolverRaw | undefined,
  ) => {
    if (!key || !raw || !has(raw, key)) return;
    const value = firstFinite(raw[key]);
    if (value == null) return;
    const perDeg = (value * Math.PI) / 180;
    out.push(
      series(
        solver,
        grid,
        grid.map(() => perDeg),
        "hline",
        pinnedLabel(solver, beta, NO_SIDESLIP_DERIVATIVES),
      ),
    );
  };

  horizontal("tornado", spec.tornado, raws.tornado);

  const avl = raws.avl;
  const avlLabel = pinnedLabel("avl", beta, NO_SIDESLIP_DERIVATIVES);
  if (spec.avl && avl && has(avl, spec.avl) && has(avl, "alpha")) {
    const alpha = avl.alpha;
    const value = avl[spec.avl];
    if (Array.isArray(alpha) && Array.isArray(value)) {
      if (alpha.length === value.length) {
        const samples = pairedSamples(alpha, value, false);
        if (samples.x.length > 0) {
          out.push(
            series(
              "avl",
              samples.x,
              samples.y.map((item) => (item * Math.PI) / 180),
              "line",
              avlLabel,
            ),
          );
        }
      }
    } else {
      const a0 = oneSample(alpha);
      const v = oneSample(value);
      if (a0 != null && v != null) {
        out.push(series("avl", [a0], [(v * Math.PI) / 180], "line", avlLabel));
      }
    }
  }

  horizontal("flow5", spec.flow5, raws.flow5);
  return out;
}
