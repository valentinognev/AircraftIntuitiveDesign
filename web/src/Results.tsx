import { useEffect, useState, useSyncExternalStore } from "react";
import { aircraftForRequest } from "./api";
import { chartRows, type ControlChartSeries, type ControlDerivPayload } from "./controlDeriv";
import {
  barFill,
  barLegend,
  controlBarCategories,
  groupedBarCategories,
  hasSolverRaw,
  hingeBarCategories,
  hlineSegment,
  knownSolverRaws,
  layoutBars,
  lineLegends,
  lineSeriesDomain,
  stabilityAlphaOf,
  type BarCategory,
} from "./aeroChart";
import { aeroTabs, type AeroFigure, type BarFigure, type ControlBars, type HingeBars, type LineFigure, type TableFigure } from "./aeroFigures";
import {
  axisTicks,
  chartLayout,
  gridLines,
  overlaySeries,
  plotDomain,
  stabilityText,
  svgPolyline,
  type HandshakePayload,
  type PlotSeries,
} from "./payload";
import store, { type AidState } from "./store";

function useAid<T>(selector: (state: AidState) => T): T {
  return useSyncExternalStore(
    store.subscribe,
    () => selector(store.getState()),
    () => selector(store.getState()),
  );
}

const LAYOUT = chartLayout();

function swatch(color: string): string {
  return color === "currentColor" ? "currentColor" : color;
}

const CONTROL_STROKES = [
  "currentColor",
  "red",
  "#2563eb",
  "#16a34a",
  "#ca8a04",
  "#9333ea",
  "#0891b2",
  "#db2777",
];

function controlStroke(index: number): string {
  return CONTROL_STROKES[index % CONTROL_STROKES.length];
}

function controlDomain(series: ControlChartSeries[]) {
  return plotDomain(
    series.map((s) => ({
      solver: s.id,
      stroke: "currentColor",
      alpha: s.xs,
      cl: s.ys,
      cd: [],
      cm: [],
    })),
    (s) => s.cl,
  );
}

function ControlDerivChart({ series }: { series: ControlChartSeries[] }) {
  const domain = controlDomain(series);
  const { width, height, plot } = LAYOUT;
  return (
    <figure className="min-w-0">
      <figcaption className="text-xs font-medium text-slate-600 dark:text-slate-300">
        dC/dδ
      </figcaption>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="h-44 w-full text-slate-700 dark:text-slate-200"
        role="img"
        aria-label="dC/dδ versus probe angle"
      >
        <Axes domain={domain} xlabel="δ (deg)" />
        {domain
          ? series.map((s, i) => {
              const pts = svgPolyline(s.xs, s.ys, width, height, 0, domain, plot);
              if (!pts) return null;
              return (
                <polyline
                  key={s.id}
                  points={pts}
                  fill="none"
                  stroke={controlStroke(i)}
                  strokeWidth={1.75}
                  data-series={s.id}
                />
              );
            })
          : null}
      </svg>
      <ul className="flex flex-wrap gap-3 text-xs">
        {series.map((s, i) => (
          <li key={s.id} className="flex items-center gap-1">
            <span
              className="inline-block h-0.5 w-4"
              style={{ background: swatch(controlStroke(i)) }}
            />
            {s.id}
          </li>
        ))}
      </ul>
    </figure>
  );
}

function Chart({
  title,
  ylabel,
  series,
  pick,
}: {
  title: string;
  ylabel: string;
  series: PlotSeries[];
  pick: (s: PlotSeries) => number[];
}) {
  const domain = plotDomain(series, pick);
  const { width, height, plot } = LAYOUT;
  const xTicks = domain ? axisTicks(domain.xmin, domain.xmax) : [];
  const yTicks = domain ? axisTicks(domain.ymin, domain.ymax) : [];
  const dx = domain ? domain.xmax - domain.xmin || 1 : 1;
  const dy = domain ? domain.ymax - domain.ymin || 1 : 1;
  const yOf = (value: number) => plot.y + plot.height - ((value - (domain?.ymin ?? 0)) / dy) * plot.height;
  const xOf = (value: number) => plot.x + ((value - (domain?.xmin ?? 0)) / dx) * plot.width;
  return (
    <figure className="min-w-0">
      <figcaption className="text-xs font-medium text-slate-600 dark:text-slate-300">
        {title}
      </figcaption>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="h-44 w-full text-slate-700 dark:text-slate-200"
        role="img"
        aria-label={`${title} (${ylabel})`}
      >
        {domain
          ? gridLines(domain, plot).map((line, i) => (
              <line
                key={i}
                x1={line.x1}
                y1={line.y1}
                x2={line.x2}
                y2={line.y2}
                stroke="currentColor"
                strokeOpacity={0.22}
              />
            ))
          : null}
        <rect
          x={plot.x}
          y={plot.y}
          width={plot.width}
          height={plot.height}
          fill="none"
          stroke="currentColor"
          strokeOpacity={0.7}
        />
        {yTicks.map((tick) => (
          <text
            key={`y-${tick.label}`}
            x={plot.x - 6}
            y={yOf(tick.value)}
            fill="currentColor"
            fontSize={12}
            textAnchor="end"
            dominantBaseline="middle"
          >
            {tick.label}
          </text>
        ))}
        {xTicks.map((tick) => (
          <text
            key={`x-${tick.label}`}
            x={xOf(tick.value)}
            y={plot.y + plot.height + 18}
            fill="currentColor"
            fontSize={12}
            textAnchor="middle"
          >
            {tick.label}
          </text>
        ))}
        <text
          x={plot.x + plot.width / 2}
          y={height - 8}
          fill="currentColor"
          fontSize={12}
          textAnchor="middle"
        >
          α (deg)
        </text>
        {domain
          ? series.map((s) => {
              const pts = svgPolyline(s.alpha, pick(s), width, height, 0, domain, plot);
              if (!pts) return null;
              return (
                <polyline
                  key={s.solver}
                  points={pts}
                  fill="none"
                  stroke={s.stroke}
                  strokeWidth={1.75}
                />
              );
            })
          : null}
      </svg>
    </figure>
  );
}

function Axes({
  domain,
  xlabel,
  showXTicks = true,
}: {
  domain: ReturnType<typeof lineSeriesDomain>;
  xlabel: string;
  showXTicks?: boolean;
}) {
  const { height, plot } = LAYOUT;
  const xTicks = domain ? axisTicks(domain.xmin, domain.xmax) : [];
  const yTicks = domain ? axisTicks(domain.ymin, domain.ymax) : [];
  const dx = domain ? domain.xmax - domain.xmin || 1 : 1;
  const dy = domain ? domain.ymax - domain.ymin || 1 : 1;
  const yOf = (value: number) => plot.y + plot.height - ((value - (domain?.ymin ?? 0)) / dy) * plot.height;
  const xOf = (value: number) => plot.x + ((value - (domain?.xmin ?? 0)) / dx) * plot.width;
  return (
    <>
      {domain
        ? gridLines(domain, plot).map((line, i) => (
            <line
              key={i}
              x1={line.x1}
              y1={line.y1}
              x2={line.x2}
              y2={line.y2}
              stroke="currentColor"
              strokeOpacity={0.22}
            />
          ))
        : null}
      <rect
        x={plot.x}
        y={plot.y}
        width={plot.width}
        height={plot.height}
        fill="none"
        stroke="currentColor"
        strokeOpacity={0.7}
      />
      {yTicks.map((tick) => (
        <text
          key={`y-${tick.label}`}
          x={plot.x - 6}
          y={yOf(tick.value)}
          fill="currentColor"
          fontSize={12}
          textAnchor="end"
          dominantBaseline="middle"
        >
          {tick.label}
        </text>
      ))}
      {showXTicks
        ? xTicks.map((tick) => (
            <text
              key={`x-${tick.label}`}
              x={xOf(tick.value)}
              y={plot.y + plot.height + 18}
              fill="currentColor"
              fontSize={12}
              textAnchor="middle"
            >
              {tick.label}
            </text>
          ))
        : null}
      {xlabel ? (
        <text
          x={plot.x + plot.width / 2}
          y={height - 8}
          fill="currentColor"
          fontSize={12}
          textAnchor="middle"
        >
          {xlabel}
        </text>
      ) : null}
    </>
  );
}

function LineFigureView({ figure }: { figure: LineFigure }) {
  const domain = lineSeriesDomain(figure.series);
  const { width, height, plot } = LAYOUT;
  const legends = lineLegends(figure.series);
  return (
    <figure className="min-w-0">
      <figcaption className="text-xs font-medium text-slate-600 dark:text-slate-300">
        {figure.title}
      </figcaption>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className="h-44 w-full text-slate-700 dark:text-slate-200"
        role="img"
        aria-label={`${figure.title} (${figure.ylabel})`}
      >
        <Axes domain={domain} xlabel={figure.xlabel} />
        {domain
          ? figure.series.map((s, i) => {
              if (s.kind === "hline") {
                const seg = hlineSegment(s.y[0], domain, plot);
                if (!seg) return null;
                return (
                  <line
                    key={`${s.solver}-h-${i}`}
                    x1={seg.x1}
                    y1={seg.y1}
                    x2={seg.x2}
                    y2={seg.y2}
                    stroke={s.stroke}
                    strokeWidth={1.75}
                  />
                );
              }
              const pts = svgPolyline(s.x, s.y, width, height, 0, domain, plot);
              if (!pts) return null;
              if (!pts.includes(" ")) {
                return (
                  <circle
                    key={`${s.solver}-${i}`}
                    cx={Number(pts.split(",")[0])}
                    cy={Number(pts.split(",")[1])}
                    r={3.5}
                    fill={s.stroke}
                  />
                );
              }
              return (
                <polyline
                  key={`${s.solver}-${i}`}
                  points={pts}
                  fill="none"
                  stroke={s.stroke}
                  strokeWidth={1.75}
                />
              );
            })
          : null}
      </svg>
      {legends.length > 0 ? (
        <ul className="flex flex-wrap gap-3 text-xs">
          {legends.map((item) => (
            <li key={item.label} className="flex items-center gap-1">
              <span className="inline-block h-0.5 w-4" style={{ background: swatch(item.stroke) }} />
              {item.label}
            </li>
          ))}
        </ul>
      ) : null}
    </figure>
  );
}

function categoriesFor(figure: BarFigure | ControlBars | HingeBars): BarCategory[] {
  if (figure.kind === "bars") return groupedBarCategories(figure.groups);
  if (figure.kind === "control-bars") return controlBarCategories(figure);
  return hingeBarCategories(figure);
}

function BarFigureView({
  figure,
  beta,
}: {
  figure: BarFigure | ControlBars | HingeBars;
  beta: number;
}) {
  const categories = categoriesFor(figure);
  const { width, plot } = LAYOUT;
  const laid = layoutBars(categories, plot);
  const legend = barLegend(categories, beta);
  const domain = laid.domain;
  return (
    <figure className="min-w-0">
      <figcaption className="text-xs font-medium text-slate-600 dark:text-slate-300">
        {figure.title}
      </figcaption>
      <svg
        viewBox={`0 0 ${width} ${plot.y + plot.height + 12}`}
        preserveAspectRatio="none"
        className="h-44 w-full text-slate-700 dark:text-slate-200"
        role="img"
        aria-label={figure.title}
      >
        <Axes domain={domain} xlabel="" showXTicks={false} />
        {laid.bars.map((bar, i) => (
          <rect
            key={`${bar.label}-${bar.key}-${i}`}
            x={bar.x}
            y={bar.y}
            width={bar.width}
            height={bar.height}
            fill={barFill(bar.key)}
          />
        ))}
      </svg>
      {laid.labels.length > 0 ? (
        <div
          className="flex text-[10px] leading-tight text-slate-600 dark:text-slate-300"
          style={{
            marginLeft: `${(plot.x / width) * 100}%`,
            width: `${(plot.width / width) * 100}%`,
          }}
        >
          {laid.labels.map((label, i) => (
            <span
              key={`${label.label}-${i}`}
              className="min-w-0 flex-1 break-words px-0.5 text-center"
              title={label.label}
            >
              {label.label}
            </span>
          ))}
        </div>
      ) : null}
      {legend.length > 0 ? (
        <ul className="mt-1 flex flex-wrap gap-3 text-xs">
          {legend.map((item) => (
            <li key={item.key} className="flex items-center gap-1">
              <span className="inline-block h-2 w-3" style={{ background: swatch(barFill(item.key)) }} />
              {item.label}
            </li>
          ))}
        </ul>
      ) : null}
    </figure>
  );
}

function TableFigureView({ figure }: { figure: TableFigure }) {
  return (
    <figure className="min-w-0">
      <figcaption className="mb-1 text-xs font-medium text-slate-600 dark:text-slate-300">
        {figure.title}
      </figcaption>
      <table className="w-full border-collapse text-xs text-slate-700 dark:text-slate-200">
        <thead>
          <tr className="border-b border-slate-200 font-medium dark:border-slate-700">
            {figure.columns.map((col, i) => (
              <th key={`${col}-${i}`} className={`px-1 py-1 ${i === 0 ? "text-left" : "text-right"}`}>
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {figure.rows.map((row, r) => (
            <tr key={r} className={row.header ? "font-medium" : undefined}>
              {row.cells.map((cell, c) => (
                <td
                  key={c}
                  className={`px-1 py-0.5 ${row.header || c === 0 ? "text-left" : "text-right"}`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}

function FigureView({ figure, beta }: { figure: AeroFigure; beta: number }) {
  if (figure.kind === "lines") return <LineFigureView figure={figure} />;
  if (figure.kind === "table") return <TableFigureView figure={figure} />;
  return <BarFigureView figure={figure} beta={beta} />;
}

/**
 * The sideslip this block of results was **run at**, in degrees.
 *
 * Taken from the run's own payload, never from the aircraft in the editor. Every
 * curve on this page is drawn from `s.raws`, i.e. from the last run, so labelling
 * it from a Beta field that has been edited since would claim the data was flown
 * at a condition it was not — a false provenance claim, and the one this whole
 * labelling rule exists to prevent.
 *
 * `analyze.py`'s `_analyze_result` fills `axes.beta` from `_flown_beta`, which
 * reports the real sideslip for the two solvers that can fly one (`tornado`,
 * `flow5`) and 0 for the ones that cannot (`datcom`, `avl`). So "some payload in
 * this block reporting non-zero" is exactly the condition the block was flown at,
 * and a block flown at β = 0 reports zero throughout — the right answer, since no
 * series needs a `(beta=0)` mark then.
 */
export function flownBeta(payloads: readonly HandshakePayload[]): number {
  for (const payload of payloads) {
    const beta = payload?.axes?.beta?.[0];
    if (typeof beta === "number" && Number.isFinite(beta) && beta !== 0) return beta;
  }
  return 0;
}

export function Results({ initialTab = "forces" }: { initialTab?: string }) {
  const lastPayload = useAid((s) => s.lastPayload);
  const payloads = useAid((s) => s.payloads);
  const lastStability = useAid((s) => s.lastStability);
  const rawRecord = useAid((s) => s.raws);
  const handbook = useAid((s) => s.handbook);
  const [tabId, setTabId] = useState(initialTab);
  const [controlSeries, setControlSeries] = useState<ControlChartSeries[]>([]);
  const [controlError, setControlError] = useState<string | null>(null);
  const runPayloads = lastPayload == null
    ? []
    : Object.values(payloads).length ? Object.values(payloads) : [lastPayload];
  const series = overlaySeries(runPayloads);
  const summary = stabilityText(lastStability);
  const solverRaws = knownSolverRaws(rawRecord);
  const showTabs = hasSolverRaw(solverRaws);
  const beta = flownBeta(runPayloads);
  const tabs = showTabs
    ? aeroTabs(solverRaws, stabilityAlphaOf(lastStability), handbook, beta)
    : [];
  const selected = tabs.find((tab) => tab.id === tabId) ?? tabs[0];

  useEffect(() => {
    if (lastPayload == null) {
      setControlSeries([]);
      setControlError(null);
      return;
    }
    const aircraft = store.getState().aircraft;
    if (aircraft == null) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/control-derivatives", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            aircraft: aircraftForRequest(aircraft),
            solver: "handbook",
            deltas_deg: [0, 5],
          }),
        });
        if (!res.ok) throw new Error(`control-derivatives HTTP ${res.status}`);
        const body = (await res.json()) as ControlDerivPayload;
        if (cancelled) return;
        setControlSeries(chartRows(body));
        setControlError(null);
      } catch (err) {
        if (cancelled) return;
        setControlSeries([]);
        setControlError(err instanceof Error ? err.message : String(err));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [lastPayload]);

  const controlChart =
    controlSeries.length > 0 ? <ControlDerivChart series={controlSeries} /> : null;

  return (
    <div className="flex h-full min-h-0 flex-col overflow-y-auto bg-white p-3 dark:bg-slate-900">
      <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
        Aerodynamics
      </div>
      {summary ? (
        <p className="mb-3 whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">{summary}</p>
      ) : (
        <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">Load an aircraft for CG / static margin.</p>
      )}
      {controlError ? (
        <p className="mb-2 truncate text-xs text-red-600 dark:text-red-400" title={controlError}>
          {controlError}
        </p>
      ) : null}
      {showTabs && selected ? (
        <div>
          <div className="mb-2 flex flex-wrap gap-1" role="tablist" aria-label="Aerodynamic coefficients">
            {tabs.map((tab) => {
              const active = tab.id === selected.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  className={`rounded px-2 py-1 text-xs ${
                    active
                      ? "bg-slate-800 text-white dark:bg-slate-100 dark:text-slate-900"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`}
                  onClick={() => setTabId(tab.id)}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
          <div className="space-y-2">
            {selected.figures.map((figure, i) => (
              <FigureView
                key={`${figure.kind}-${figure.title}-${i}`}
                figure={figure}
                beta={beta}
              />
            ))}
            {controlChart}
          </div>
        </div>
      ) : series.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Analyze to plot CL, CD, Cm vs α.</p>
      ) : (
        <div className="space-y-2">
          <Chart title="CL vs α" ylabel="CL" series={series} pick={(s) => s.cl} />
          <Chart title="CD vs α" ylabel="CD" series={series} pick={(s) => s.cd} />
          <Chart title="Cm vs α" ylabel="Cm" series={series} pick={(s) => s.cm} />
          {controlChart}
          <ul className="flex flex-wrap gap-3 text-xs">
            {series.map((s) => (
              <li key={s.solver} className="flex items-center gap-1">
                <span className="inline-block h-0.5 w-4" style={{ background: swatch(s.stroke) }} />
                {s.solver}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
