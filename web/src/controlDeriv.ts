const COEFFS = ["CL", "CD", "Cm", "CY", "Cl", "Cn"] as const;

export type ControlCoeff = (typeof COEFFS)[number];

export type ControlDerivRow = {
  surface: string;
  delta_deg: number;
  available: boolean;
  reason?: string;
} & Record<ControlCoeff, number | null>;

export type ControlDerivPayload = {
  solver: string;
  deltas_deg: number[];
  rows: ControlDerivRow[];
};

export type ControlChartSeries = {
  id: string;
  xs: number[];
  ys: number[];
  /**
   * The name the legend shows, set when the numbers were computed at zero sideslip
   * under a non-zero one. `id` is a stable key and is never rewritten for display --
   * `Results.tsx` writes it to `data-series`, so the two must stay distinct.
   */
  label?: string;
};

/**
 * The solvers whose control curves really are at the flight condition's sideslip.
 *
 * Mirrors `BETA_CAPABLE_CONTROL_SOLVERS` in `aid/solver_overlay.py`: Tornado reads it
 * through `tornado_io`'s `betha` and flow5 through the deck's polar beta, while
 * DATCOM, AVL and the handbook have no sideslip capability at all. This is the same
 * list as `aid_web.analyze.BETA_CAPABLE_SOLVERS`, which answers the same question for
 * the handshake payloads.
 */
const BETA_CAPABLE_SOLVERS = new Set(["tornado", "flow5"]);

/**
 * Finite coefficients grouped by surface and name. Null and unavailable rows are omitted.
 *
 * `beta` is the flight condition's sideslip in degrees. README.md:44 is the rule:
 * "any series that was not computed at that sideslip gets ` (beta=0)` appended, and at
 * `BETA == 0` every label is byte-identical to the pre-feature text" -- so a solver
 * outside :data:`BETA_CAPABLE_SOLVERS` gets the mark and nothing else changes.
 */
export function chartRows(payload: ControlDerivPayload, beta = 0): ControlChartSeries[] {
  const mark = beta !== 0 && !BETA_CAPABLE_SOLVERS.has(payload.solver);
  const grouped = new Map<string, ControlChartSeries>();
  for (const row of payload.rows) {
    if (row.available === false) continue;
    for (const name of COEFFS) {
      const value = row[name];
      if (value == null || !Number.isFinite(value)) continue;
      const id = `${payload.solver}-${row.surface}-${name}`;
      let series = grouped.get(id);
      if (series == null) {
        series = { id, xs: [], ys: [], ...(mark ? { label: `${id} (beta=0)` } : {}) };
        grouped.set(id, series);
      }
      series.xs.push(row.delta_deg);
      series.ys.push(value);
    }
  }
  return [...grouped.values()];
}

/** What a control-chart legend entry reads: the mark when there is one, else the id. */
export function controlLegendText(series: ControlChartSeries): string {
  return series.label ?? series.id;
}
