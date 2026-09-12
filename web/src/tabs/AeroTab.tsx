import { useStore } from "zustand";
import { NumField, StringField, TextField } from "../Field";
import { AERO_BREAKS, AERO_FIELDS, AERO_NACA_FIELDS, unitText } from "../fields";
import store from "../store";
import type { AircraftGroup } from "../aircraft";

function nacaValue(aircraft: Record<string, Record<string, unknown>> | null, key: string): unknown {
  if (aircraft == null) return null;
  const indexed = /^([A-Za-z]+)\.([A-Za-z]+)\[(\d+)\]$/.exec(key);
  if (indexed) {
    const group = indexed[1] as AircraftGroup;
    const field = indexed[2];
    const idx = Number(indexed[3]);
    const raw = aircraft[group]?.[field];
    return Array.isArray(raw) ? raw[idx] : null;
  }
  const dotted = /^([A-Za-z]+)\.([A-Za-z]+)$/.exec(key);
  if (dotted) {
    const group = dotted[1] as AircraftGroup;
    return aircraft[group]?.[dotted[2]];
  }
  return null;
}

function commitNaca(key: string, value: unknown): void {
  const indexed = /^([A-Za-z]+)\.([A-Za-z]+)\[(\d+)\]$/.exec(key);
  if (indexed) {
    store.getState().setArrayField(indexed[1] as AircraftGroup, indexed[2], Number(indexed[3]), value);
    return;
  }
  const dotted = /^([A-Za-z]+)\.([A-Za-z]+)$/.exec(key);
  if (dotted) {
    store.getState().setGroupField(dotted[1] as AircraftGroup, dotted[2], value);
  }
}

export function AeroTab() {
  const aircraft = useStore(store, (s) => s.aircraft);
  const aero = (aircraft?.AERO ?? {}) as Record<string, unknown>;
  const unit = aircraft?.unit ?? "ft";
  const groups = aircraft as unknown as Record<string, Record<string, unknown>> | null;
  return (
    <form className="space-y-1" onSubmit={(e) => e.preventDefault()}>
      {AERO_FIELDS.map(([field, label, kind], i) => (
        <div key={field}>
          {field === "ALSCHD" ? (
            <TextField
              label={label}
              value={aero[field]}
              unit={unitText(kind, unit)}
              onCommit={(v) => store.getState().setGroupField("AERO", field, v)}
            />
          ) : (
            <NumField
              label={label}
              value={aero[field]}
              unit={unitText(kind, unit)}
              onCommit={(v) => store.getState().setGroupField("AERO", field, v)}
            />
          )}
          {AERO_BREAKS.includes((i + 1) as (typeof AERO_BREAKS)[number]) ? (
            <hr className="my-2 border-slate-300 dark:border-slate-700" />
          ) : null}
        </div>
      ))}
      {AERO_NACA_FIELDS.map(([key, label], i) => (
        <div key={key}>
          <StringField
            label={label}
            value={nacaValue(groups, key)}
            unit={unitText("naca", unit)}
            onCommit={(v) => commitNaca(key, v)}
          />
          {AERO_BREAKS.includes((AERO_FIELDS.length + i + 1) as (typeof AERO_BREAKS)[number]) ? (
            <hr className="my-2 border-slate-300 dark:border-slate-700" />
          ) : null}
        </div>
      ))}
    </form>
  );
}
