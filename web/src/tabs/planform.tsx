import { useStore } from "zustand";
import { NumField } from "../Field";
import { PLANFORM_BREAKS, PLANFORM_RP, unitText } from "../fields";
import store from "../store";
import type { AircraftGroup } from "../aircraft";

export function PlanformFields({
  prefix,
  cmpIndex,
}: {
  prefix: "WG" | "HT" | "VT";
  cmpIndex: number;
}) {
  const aircraft = useStore(store, (s) => s.aircraft);
  const group = (aircraft?.[prefix] ?? {}) as Record<string, unknown>;
  const unit = aircraft?.unit ?? "ft";
  const plotOn = Number(aircraft?.plot_cmp?.[cmpIndex] ?? 1) !== 0;
  return (
    <form className="space-y-1" onSubmit={(e) => e.preventDefault()}>
      {PLANFORM_RP.map(([field, label, kind], i) => (
        <div key={field}>
          <NumField
            label={label}
            value={group[field]}
            unit={unitText(kind, unit)}
            checkbox={
              i === 0 ? (
                <input
                  type="checkbox"
                  checked={plotOn}
                  onChange={(e) => store.getState().setPlotCmp(cmpIndex, e.target.checked)}
                  aria-label={`${prefix} visible`}
                />
              ) : undefined
            }
            onCommit={(v) => store.getState().setGroupField(prefix as AircraftGroup, field, v)}
          />
          {PLANFORM_BREAKS.includes((i + 1) as (typeof PLANFORM_BREAKS)[number]) ? (
            <hr className="my-2 border-slate-300 dark:border-slate-700" />
          ) : null}
        </div>
      ))}
    </form>
  );
}
