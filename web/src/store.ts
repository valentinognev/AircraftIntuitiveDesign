import { createStore as createVanillaStore } from "zustand/vanilla";
import {
  aircraftFromJson,
  emptyAircraft,
  parseJsonc,
  patchArrayItem,
  patchGroup,
  type AircraftDict,
  type AircraftGroup,
} from "./aircraft";
import { fetchModel, fetchStability, postAnalyze, type ValidateResult } from "./api";
import type { HandshakePayload } from "./payload";
import {
  addPart,
  extraTabForPart,
  patchSlotArrayItem,
  patchSlotField,
  type ExtraTabId,
} from "./extras";
import { readRecent, rememberRecent } from "./recent";
import { currentTheme, type Theme } from "./theme";

export type View = "start" | "editor";

export type { ExtraTabId };

export type TabId = "wing" | "ht" | "vt" | "control" | "body" | "aero" | "geometry" | "plus" | ExtraTabId;

export const TABS: { id: TabId; label: string }[] = [
  { id: "wing", label: "Wing" },
  { id: "ht", label: "HT" },
  { id: "vt", label: "VT" },
  { id: "control", label: "Control" },
  { id: "body", label: "Body" },
  { id: "aero", label: "Aero" },
  { id: "geometry", label: "Geometry" },
  { id: "plus", label: "+" },
];

export type ParseErrorInfo = { message: string };

export type AidState = {
  view: View;
  theme: Theme;
  models: string[] | null;
  modelsError: string | null;
  aircraft: AircraftDict | null;
  stem: string | null;
  parseError: ParseErrorInfo | null;
  validateError: ParseErrorInfo | null;
  tab: TabId;
  recent: string[];
  revision: number;
  lastPayload: HandshakePayload | null;
  payloads: Record<string, HandshakePayload>;
  lastStability: Record<string, unknown> | null;
  analyzeError: ParseErrorInfo | null;
  handshakeError: string | null;
  analyzing: boolean;
  setTheme: (theme: Theme) => void;
  setTab: (tab: TabId) => void;
  setModels: (models: string[]) => void;
  setModelsError: (modelsError: string | null) => void;
  applyParseFail: (error: string) => void;
  applyValidateResult: (result: ValidateResult) => void;
  openNew: () => void;
  openAircraft: (raw: unknown, stem: string) => void;
  openJsoncText: (text: string, stem: string) => void;
  openExample: (name: string) => Promise<void>;
  openRecent: (name: string) => Promise<void>;
  goStart: () => void;
  setGroupField: (group: AircraftGroup, key: string, value: unknown) => void;
  setArrayField: (group: AircraftGroup, key: string, index: number, value: unknown) => void;
  setSlotField: (list: "NP" | "NB", slot: number, key: string, value: unknown) => void;
  setSlotArrayField: (
    list: "NP" | "NB",
    slot: number,
    key: string,
    index: number,
    value: unknown,
  ) => void;
  addPart: (component: number) => void;
  setPlotCmp: (index: number, on: boolean) => void;
  setUnit: (unit: string) => void;
  runAnalyze: (solver: string) => Promise<void>;
  loadStability: () => Promise<void>;
};

function initialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  return currentTheme();
}

function initialRecent(): string[] {
  if (typeof localStorage === "undefined") return [];
  try {
    return readRecent(localStorage);
  } catch {
    return [];
  }
}

function recordRecent(name: string): string[] {
  if (typeof localStorage === "undefined") return [];
  try {
    return rememberRecent(name, localStorage);
  } catch {
    return [];
  }
}

export function createStore() {
  let analyzeGen = 0;
  return createVanillaStore<AidState>((set, get) => ({
    view: "start",
    theme: initialTheme(),
    models: null,
    modelsError: null,
    aircraft: null,
    stem: null,
    parseError: null,
    validateError: null,
    tab: "wing",
    recent: initialRecent(),
    revision: 0,
    lastPayload: null,
    payloads: {},
    lastStability: null,
    analyzeError: null,
    handshakeError: null,
    analyzing: false,
    setTheme: (theme) => set({ theme }),
    setTab: (tab) => set({ tab }),
    setModels: (models) => set({ models, modelsError: null }),
    setModelsError: (modelsError) => set({ modelsError }),
    applyParseFail: (error) => set({ parseError: { message: error } }),
    applyValidateResult: (result) =>
      set({
        validateError: result.ok ? null : { message: result.error },
      }),
    openNew: () =>
      set((s) => {
        analyzeGen += 1;
        return {
          view: "editor",
          aircraft: emptyAircraft(),
          stem: "untitled",
          parseError: null,
          validateError: null,
          tab: "wing",
          lastPayload: null,
          payloads: {},
          lastStability: null,
          analyzeError: null,
          handshakeError: null,
          analyzing: false,
          revision: s.revision + 1,
        };
      }),
    openAircraft: (raw, stem) => {
      try {
        const aircraft = aircraftFromJson(raw);
        set((s) => {
          analyzeGen += 1;
          return {
            view: "editor",
            aircraft,
            stem,
            parseError: null,
            validateError: null,
            tab: "wing",
            recent: recordRecent(stem),
            lastPayload: null,
            payloads: {},
            lastStability: null,
            analyzeError: null,
            handshakeError: null,
            analyzing: false,
            revision: s.revision + 1,
          };
        });
        void get().loadStability();
      } catch (err) {
        set({ parseError: { message: err instanceof Error ? err.message : String(err) } });
      }
    },
    openJsoncText: (text, stem) => {
      try {
        get().openAircraft(parseJsonc(text), stem);
      } catch (err) {
        set({ parseError: { message: err instanceof Error ? err.message : String(err) } });
      }
    },
    openExample: async (name) => {
      set({ parseError: null });
      try {
        const raw = await fetchModel(name);
        get().openAircraft(raw, name);
      } catch (err) {
        set({ parseError: { message: err instanceof Error ? err.message : String(err) } });
      }
    },
    openRecent: async (name) => {
      const models = get().models;
      if (models != null && models.includes(name)) {
        await get().openExample(name);
      }
    },
    goStart: () => set({ view: "start", parseError: null, validateError: null }),
    setGroupField: (group, key, value) => {
      const ac = get().aircraft;
      if (ac == null) return;
      set((s) => ({
        aircraft: patchGroup(ac, group, key, value),
        parseError: null,
        revision: s.revision + 1,
      }));
    },
    setArrayField: (group, key, index, value) => {
      const ac = get().aircraft;
      if (ac == null) return;
      set((s) => ({
        aircraft: patchArrayItem(ac, group, key, index, value),
        parseError: null,
        revision: s.revision + 1,
      }));
    },
    setSlotField: (list, slot, key, value) => {
      const ac = get().aircraft;
      if (ac == null) return;
      set((s) => ({
        aircraft: patchSlotField(ac, list, slot, key, value),
        parseError: null,
        revision: s.revision + 1,
      }));
    },
    setSlotArrayField: (list, slot, key, index, value) => {
      const ac = get().aircraft;
      if (ac == null) return;
      set((s) => ({
        aircraft: patchSlotArrayItem(ac, list, slot, key, index, value),
        parseError: null,
        revision: s.revision + 1,
      }));
    },
    addPart: (component) => {
      const ac = get().aircraft;
      if (ac == null) return;
      const aircraft = addPart(ac, component);
      const extra = extraTabForPart(aircraft, component);
      set((s) => ({
        aircraft,
        tab: extra ?? s.tab,
        parseError: null,
        revision: s.revision + 1,
      }));
    },
    setPlotCmp: (index, on) => {
      const ac = get().aircraft;
      if (ac == null) return;
      const flags = [...ac.plot_cmp];
      while (flags.length <= index) flags.push(1);
      flags[index] = on ? 1 : 0;
      set((s) => ({ aircraft: { ...ac, plot_cmp: flags }, revision: s.revision + 1 }));
    },
    setUnit: (unit) => {
      const ac = get().aircraft;
      if (ac == null) return;
      set((s) => ({ aircraft: { ...ac, unit }, revision: s.revision + 1 }));
    },
    runAnalyze: async (solver) => {
      const ac = get().aircraft;
      if (ac == null) return;
      const gen = ++analyzeGen;
      set({ analyzing: true, analyzeError: null, handshakeError: null });
      const revision = get().revision;
      try {
        const result = await postAnalyze(ac, solver);
        if (analyzeGen !== gen) return;
        if (result.ok) {
          if (get().revision !== revision) return;
          set((s) => ({
            lastPayload: result.payload,
            payloads: { ...s.payloads, [result.payload.solver]: result.payload },
            analyzeError: null,
            handshakeError: result.handshakeError,
            tab: "aero",
          }));
        } else {
          set({ analyzeError: { message: result.error } });
        }
      } catch (err) {
        if (analyzeGen !== gen) return;
        set({
          analyzeError: { message: err instanceof Error ? err.message : String(err) },
        });
      } finally {
        if (analyzeGen === gen) set({ analyzing: false });
      }
    },
    loadStability: async () => {
      const ac = get().aircraft;
      if (ac == null) return;
      const revision = get().revision;
      const st = await fetchStability(ac);
      if (get().revision !== revision) return;
      set({ lastStability: st });
    },
  }));
}

const store = createStore();
export default store;
