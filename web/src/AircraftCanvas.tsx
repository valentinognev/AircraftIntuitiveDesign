import { OrbitControls } from "@react-three/drei";
import { Canvas, useThree } from "@react-three/fiber";
import { useLayoutEffect, useMemo, useRef } from "react";
import { BufferAttribute, BufferGeometry, DoubleSide } from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { useStore } from "zustand";
import {
  keepLastGood,
  sceneFromConfig,
  type Polyline,
  type Scene,
  type Vec3,
} from "./geom";
import store from "./store";

function toThree(p: { x: number; y: number; z: number }): [number, number, number] {
  return [p.x, p.z, p.y];
}

function FuselageMesh({ rings }: { rings: Polyline[] }) {
  const geometry = useMemo(() => {
    const geo = new BufferGeometry();
    const usable = rings.filter((ring) => ring.length >= 3);
    if (usable.length < 2) return geo;
    const count = usable[0].length;
    if (usable.some((ring) => ring.length !== count)) return geo;
    const positions = new Float32Array(usable.length * count * 3);
    let p = 0;
    for (const ring of usable) {
      for (const point of ring) {
        const [x, y, z] = toThree(point);
        positions[p++] = x;
        positions[p++] = y;
        positions[p++] = z;
      }
    }
    const indices: number[] = [];
    for (let i = 0; i < usable.length - 1; i++) {
      for (let j = 0; j < count; j++) {
        const j2 = (j + 1) % count;
        const a = i * count + j;
        const b = i * count + j2;
        const c = (i + 1) * count + j;
        const d = (i + 1) * count + j2;
        indices.push(a, c, d, a, d, b);
      }
    }
    geo.setAttribute("position", new BufferAttribute(positions, 3));
    geo.setIndex(indices);
    geo.computeVertexNormals();
    return geo;
  }, [rings]);
  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color="#7dd3fc" roughness={0.45} metalness={0.1} side={DoubleSide} />
    </mesh>
  );
}

function GridMesh({ rows }: { rows: Vec3[][] }) {
  const geometry = useMemo(() => {
    const geo = new BufferGeometry();
    const spanCount = rows.length;
    const chordCount = rows[0]?.length ?? 0;
    if (spanCount < 2 || chordCount < 2 || rows.some((row) => row.length !== chordCount)) return geo;
    const positions = new Float32Array(spanCount * chordCount * 3);
    let p = 0;
    for (const row of rows) {
      for (const point of row) {
        const [x, y, z] = toThree(point);
        positions[p++] = x;
        positions[p++] = y;
        positions[p++] = z;
      }
    }
    const indices: number[] = [];
    for (let j = 0; j < spanCount - 1; j++) {
      for (let i = 0; i < chordCount - 1; i++) {
        const a = j * chordCount + i;
        const b = j * chordCount + i + 1;
        const c = (j + 1) * chordCount + i;
        const d = (j + 1) * chordCount + i + 1;
        indices.push(a, c, d, a, d, b);
      }
    }
    geo.setAttribute("position", new BufferAttribute(positions, 3));
    geo.setIndex(indices);
    geo.computeVertexNormals();
    return geo;
  }, [rows]);
  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color="#7dd3fc" roughness={0.45} metalness={0.1} side={DoubleSide} />
    </mesh>
  );
}

function FrameAircraft({ scene, frameKey }: { scene: Scene; frameKey: string }) {
  const camera = useThree((s) => s.camera);
  const controls = useRef<OrbitControlsImpl>(null);
  const sceneRef = useRef(scene);
  sceneRef.current = scene;
  useLayoutEffect(() => {
    const current = sceneRef.current;
    let minX = Infinity;
    let minY = Infinity;
    let minZ = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    let maxZ = -Infinity;
    const consider = (point: Vec3) => {
      const [x, y, z] = toThree(point);
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      minZ = Math.min(minZ, z);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
      maxZ = Math.max(maxZ, z);
    };
    for (const ring of current.fuselage) for (const point of ring) consider(point);
    for (const wing of current.wings) for (const row of wing.rows) for (const point of row) consider(point);
    if (!Number.isFinite(minX)) return;
    const center = [(minX + maxX) / 2, (minY + maxY) / 2, (minZ + maxZ) / 2];
    const radius = 0.5 * Math.hypot(maxX - minX, maxY - minY, maxZ - minZ);
    const az = (-37.5 * Math.PI) / 180;
    const el = (30 * Math.PI) / 180;
    const dx = Math.cos(el) * Math.sin(az);
    const dy = -Math.cos(el) * Math.cos(az);
    const dz = Math.sin(el);
    const dist = (radius / Math.sin((45 * Math.PI) / 360)) * 1.05;
    camera.position.set(center[0] + dx * dist, center[1] + dz * dist, center[2] + dy * dist);
    camera.up.set(0, 1, 0);
    camera.lookAt(center[0], center[1], center[2]);
    camera.updateProjectionMatrix();
    const orbit = controls.current;
    if (orbit) {
      orbit.target.set(center[0], center[1], center[2]);
      orbit.update();
    }
  }, [frameKey, camera]);
  return <OrbitControls ref={controls} />;
}

export function AircraftCanvas() {
  const aircraft = useStore(store, (s) => s.aircraft);
  const stem = useStore(store, (s) => s.stem);
  const lastScene = useRef<Scene | null>(null);
  const result =
    aircraft == null ? ({ ok: false, message: "no aircraft" } as const) : sceneFromConfig(aircraft);
  const { scene, warning } = keepLastGood(result, lastScene.current);
  if (result.ok) lastScene.current = result.scene;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center gap-2 border-b border-slate-200 px-2 py-1 dark:border-slate-800">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Geometry
        </span>
      </div>
      {warning ? (
        <div
          className="bg-amber-100 px-2 py-1 text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-200"
          role="alert"
        >
          {warning}
        </div>
      ) : null}
      <div className="min-h-0 flex-1 bg-slate-50 dark:bg-slate-950">
        <Canvas camera={{ position: [16, 8, 14], fov: 45 }} gl={{ alpha: true }} style={{ background: "transparent" }}>
          <ambientLight intensity={0.55} />
          <directionalLight position={[12, 18, 10]} intensity={0.9} />
          {scene ? <FuselageMesh rings={scene.fuselage} /> : null}
          {scene
            ? scene.wings.map((wing, i) => <GridMesh key={i} rows={wing.rows} />)
            : null}
          {scene ? <FrameAircraft scene={scene} frameKey={stem ?? "aircraft"} /> : <OrbitControls />}
        </Canvas>
      </div>
    </div>
  );
}
