import { useState, type KeyboardEvent } from "react";
import { useStore } from "zustand";
import { commitNumber, inputClass } from "../Field";
import { BODY_STATION_KEYS, BODY_STATION_ROWS, unitText } from "../fields";
import store from "../store";

function enterBlurs(e: KeyboardEvent<HTMLInputElement>) {
  if (e.key === "Enter") {
    e.preventDefault();
    e.currentTarget.blur();
  }
}

function StationInput({
  value,
  ariaLabel,
  onCommit,
}: {
  value: unknown;
  ariaLabel: string;
  onCommit: (v: number | null) => void;
}) {
  const idle = value == null || value === "" ? "" : String(value);
  const [focused, setFocused] = useState(false);
  const [draft, setDraft] = useState(idle);
  return (
    <input
      className={inputClass}
      type="text"
      inputMode="decimal"
      aria-label={ariaLabel}
      value={focused ? draft : idle}
      onFocus={() => {
        setDraft(idle);
        setFocused(true);
      }}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={() => {
        const next = commitNumber(draft);
        if (next !== undefined) onCommit(next);
        setFocused(false);
      }}
      onKeyDown={enterBlurs}
    />
  );
}

export function BodyTab() {
  const aircraft = useStore(store, (s) => s.aircraft);
  const bd = (aircraft?.BD ?? {}) as Record<string, unknown>;
  const unit = aircraft?.unit ?? "ft";
  const plotOn = Number(aircraft?.plot_cmp?.[3] ?? 1) !== 0;
  const arrays: Record<(typeof BODY_STATION_KEYS)[number], unknown[]> = {
    N: Array.isArray(bd.N) ? bd.N : [],
    X: Array.isArray(bd.X) ? bd.X : [],
    P: Array.isArray(bd.P) ? bd.P : [],
  };
  return (
    <form className="space-y-2" onSubmit={(e) => e.preventDefault()}>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={plotOn}
          onChange={(e) => store.getState().setPlotCmp(3, e.target.checked)}
          aria-label="BD visible"
        />
        Body
      </label>
      <div className="grid grid-cols-3 gap-2 text-center text-xs font-semibold text-slate-500 dark:text-slate-400">
        <span>Station</span>
        <span>{unitText("pos_hdr", unit)}</span>
        <span>Shape</span>
      </div>
      {Array.from({ length: BODY_STATION_ROWS }, (_, i) => (
        <div key={i} className="grid grid-cols-3 gap-2">
          {BODY_STATION_KEYS.map((key) => (
            <StationInput
              key={key}
              value={arrays[key][i]}
              ariaLabel={`BD.${key}[${i}]`}
              onCommit={(v) => store.getState().setArrayField("BD", key, i, v)}
            />
          ))}
        </div>
      ))}
    </form>
  );
}
