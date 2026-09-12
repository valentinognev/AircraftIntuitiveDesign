export const RECENT_STORAGE_KEY = "aid-recent";
export const RECENT_MAX = 5;

export function readRecent(storage: Pick<Storage, "getItem">): string[] {
  try {
    const raw = storage.getItem(RECENT_STORAGE_KEY);
    if (raw == null || raw === "") return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    const names: string[] = [];
    for (const item of parsed) {
      if (typeof item === "string" && item !== "" && !names.includes(item)) {
        names.push(item);
      }
      if (names.length >= RECENT_MAX) break;
    }
    return names;
  } catch {
    return [];
  }
}

export function rememberRecent(name: string, storage: Pick<Storage, "getItem" | "setItem">): string[] {
  const trimmed = name.trim();
  if (trimmed === "") return readRecent(storage);
  const rest = readRecent(storage).filter((n) => n !== trimmed);
  const out = [trimmed, ...rest].slice(0, RECENT_MAX);
  storage.setItem(RECENT_STORAGE_KEY, JSON.stringify(out));
  return out;
}
