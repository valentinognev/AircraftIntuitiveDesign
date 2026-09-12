import { expect, it } from "vitest";
import { aircraftFromJson, emptyAircraft } from "./aircraft";
import { CONTROL_BLOCKS, CONTROL_GRID_HEADERS } from "./fields";
import { addPart, extraTabs, PLUS_PARTS } from "./extras";
import { createStore } from "./store";

it("adding Wing 2 sets NP slot 0", () => {
  const store = createStore();
  store.getState().openNew();
  store.getState().addPart(3);
  const ac = store.getState().aircraft;
  expect(ac).not.toBeNull();
  expect(ac!.NP).toHaveLength(4);
  expect(ac!.NP[0]).toEqual(expect.objectContaining({ CHRDR: expect.any(Number) }));
  expect((ac!.NP[0] as { CHRDR: number }).CHRDR).toBeGreaterThan(0);
  expect(ac!.NP[1]).toBeNull();
  expect(ac!.NP[2]).toBeNull();
  expect(ac!.NP[3]).toBeNull();
  expect(store.getState().tab).toBe("wing2");
});

it("ensureNpNb pads NP to 1x4 and NB to 1x2", () => {
  const ac = aircraftFromJson({
    ...emptyAircraft(),
    NP: [null],
    NB: [],
  });
  expect(ac.NP).toEqual([null, null, null, null]);
  expect(ac.NB).toEqual([null, null]);
});

it("Body 2 fills NB[0] and Body 3 fills NB[1]", () => {
  const store = createStore();
  store.getState().openNew();
  store.getState().addPart(1);
  expect(store.getState().aircraft!.NB).toHaveLength(2);
  expect(store.getState().aircraft!.NB[0]).toEqual(expect.objectContaining({ NX: 7 }));
  expect(store.getState().aircraft!.NB[1]).toBeNull();
  expect(store.getState().tab).toBe("body2");
  store.getState().addPart(1);
  expect(store.getState().aircraft!.NB[1]).toEqual(expect.objectContaining({ NX: 7 }));
  expect(store.getState().tab).toBe("body3");
});

it("Prop Wing 2 HT 2 VT 2 fill NP slots 3 0 1 2", () => {
  const store = createStore();
  store.getState().openNew();
  store.getState().addPart(2);
  store.getState().addPart(3);
  store.getState().addPart(4);
  store.getState().addPart(5);
  const np = store.getState().aircraft!.NP;
  expect(np).toHaveLength(4);
  expect(np[3]).toEqual(expect.objectContaining({ CHRDR: expect.any(Number) }));
  expect(np[0]).toEqual(expect.objectContaining({ CHRDR: expect.any(Number) }));
  expect(np[1]).toEqual(expect.objectContaining({ CHRDR: expect.any(Number) }));
  expect(np[2]).toEqual(expect.objectContaining({ CHRDR: expect.any(Number) }));
  expect((np[3] as { CHRDR: number }).CHRDR).toBeGreaterThan(0);
});

it("PLUS_PARTS match PySide plus-tab labels", () => {
  expect(PLUS_PARTS).toEqual(["New Body", "Propeller", "New Wing", "New HT", "New VT"]);
});

it("loaded NP[0] and NP[3] become Wing 2 and Prop tabs", () => {
  const ac = addPart(addPart(emptyAircraft(), 3), 2);
  const labels = extraTabs(ac).map((t) => t.label);
  expect(labels).toEqual(["Prop", "Wing 2"]);
});

it("setSlotField writes NP[0].CHRDR", () => {
  const store = createStore();
  store.getState().openNew();
  store.getState().addPart(3);
  store.getState().setSlotField("NP", 0, "CHRDR", 0.55);
  expect((store.getState().aircraft!.NP[0] as { CHRDR: number }).CHRDR).toBe(0.55);
});

it("Control grids use CONTROL_BLOCKS inboard|outboard keys", () => {
  expect(CONTROL_GRID_HEADERS).toEqual(["Inboard", "Outboard"]);
  expect(CONTROL_BLOCKS.map(([prefix]) => prefix)).toEqual(["F", "A", "E", "R"]);
  expect(CONTROL_BLOCKS[0][1]).toBe("Flaps:");
  expect(CONTROL_BLOCKS[1][1]).toBe("Ailerons:");
  expect(CONTROL_BLOCKS[2][1]).toBe("Elevator:");
  expect(CONTROL_BLOCKS[3][1]).toBe("Rudder:");
  for (const [, , , specs] of CONTROL_BLOCKS) {
    expect(specs[0]).toEqual(["SPANFI", "SPANFO", "Span", "len"]);
    expect(specs[1]).toEqual(["CHRDFI", "CHRDFO", "Chord", "len"]);
  }
  expect(CONTROL_BLOCKS[0][3][2]).toEqual(["DELTA", null, "Deflection", "deg"]);
  expect(CONTROL_BLOCKS[1][3][2]).toEqual(["DELTAL", "DELTAR", "Deflection", "deg"]);
  expect(CONTROL_BLOCKS[2][3][2]).toEqual(["DELTA", null, "Deflection", "deg"]);
  expect(CONTROL_BLOCKS[3][3][2]).toEqual(["DELTA", null, "Deflection", "deg"]);
});
