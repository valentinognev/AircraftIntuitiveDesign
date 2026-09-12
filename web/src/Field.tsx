import { useState, type KeyboardEvent, type ReactNode } from "react";

export const inputClass =
  "w-full rounded border border-slate-300 bg-white px-2 py-1 text-sm disabled:bg-slate-100 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:disabled:bg-slate-800/60";

export function FieldRow({
  label,
  unit,
  checkbox,
  children,
}: {
  label: string;
  unit?: string;
  checkbox?: ReactNode;
  children: ReactNode;
}) {
  return (
    <label className="grid grid-cols-[minmax(9rem,1fr)_12rem_4rem] items-center gap-2 text-sm">
      <span className="flex items-center justify-end gap-2 text-right">
        {checkbox}
        {label}
      </span>
      {children}
      <span className="text-xs text-slate-500 dark:text-slate-400">{unit ?? ""}</span>
    </label>
  );
}

function enterBlurs(e: KeyboardEvent<HTMLInputElement>) {
  if (e.key === "Enter") {
    e.preventDefault();
    e.currentTarget.blur();
  }
}

function displayValue(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

export function commitNumber(text: string): number | null | undefined {
  const trimmed = text.trim();
  if (trimmed === "") return null;
  const num = Number(trimmed);
  if (Number.isFinite(num)) return num;
  return undefined;
}

export function commitString(text: string): string | null {
  const trimmed = text.trim();
  if (trimmed === "") return null;
  return trimmed;
}

export function commitFlexible(text: string): unknown | undefined {
  const trimmed = text.trim();
  if (trimmed === "") return null;
  if (trimmed.startsWith("[")) {
    try {
      return JSON.parse(trimmed) as unknown;
    } catch {
      return undefined;
    }
  }
  if (trimmed.includes(",")) {
    const parts = trimmed.split(",").map((p) => p.trim()).filter((p) => p !== "");
    const nums = parts.map((p) => Number(p));
    if (nums.every((n) => Number.isFinite(n))) return nums;
    return undefined;
  }
  const num = Number(trimmed);
  if (Number.isFinite(num)) return num;
  return trimmed;
}

export function NumInput({
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

export function NumField({
  label,
  value,
  unit,
  checkbox,
  onCommit,
}: {
  label: string;
  value: unknown;
  unit?: string;
  checkbox?: ReactNode;
  onCommit: (v: number | null) => void;
}) {
  return (
    <FieldRow label={label} unit={unit} checkbox={checkbox}>
      <NumInput value={value} ariaLabel={label} onCommit={onCommit} />
    </FieldRow>
  );
}

export function StringField({
  label,
  value,
  unit,
  onCommit,
}: {
  label: string;
  value: unknown;
  unit?: string;
  onCommit: (v: string | null) => void;
}) {
  const idle = displayValue(value);
  const [focused, setFocused] = useState(false);
  const [draft, setDraft] = useState(idle);
  return (
    <FieldRow label={label} unit={unit}>
      <input
        className={inputClass}
        type="text"
        value={focused ? draft : idle}
        onFocus={() => {
          setDraft(idle);
          setFocused(true);
        }}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => {
          onCommit(commitString(draft));
          setFocused(false);
        }}
        onKeyDown={enterBlurs}
      />
    </FieldRow>
  );
}

export function TextField({
  label,
  value,
  unit,
  onCommit,
}: {
  label: string;
  value: unknown;
  unit?: string;
  onCommit: (v: unknown) => void;
}) {
  const idle = displayValue(value);
  const [focused, setFocused] = useState(false);
  const [draft, setDraft] = useState(idle);
  return (
    <FieldRow label={label} unit={unit}>
      <input
        className={inputClass}
        type="text"
        value={focused ? draft : idle}
        onFocus={() => {
          setDraft(idle);
          setFocused(true);
        }}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => {
          const next = commitFlexible(draft);
          if (next !== undefined) onCommit(next);
          setFocused(false);
        }}
        onKeyDown={enterBlurs}
      />
    </FieldRow>
  );
}
