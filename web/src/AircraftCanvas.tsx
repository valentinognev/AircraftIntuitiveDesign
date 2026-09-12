import { Line, OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import { BufferAttribute, BufferGeometry, DoubleSide } from "three";
import { useStore } from "zustand";
import {
  keepLastGood,
  sceneFromConfig,
  type Polyline,
  type Scene,
  type WingOutline,
} from "./geom";
import store from "./store";

function toThree(p: { x: number; y: number; z: number }): [number, number, number] {
  return [p.x, p.z, p.y];
}

function FuselageLines({ polylines }: { polylines: Polyline[] }) {
  return (
    <>
      {polylines.map((poly, i) =>
        poly.length < 2 ? null : (
          <Line key={i} points={poly.map(toThree)} color="#64748b" lineWidth={1} />
        ),
      )}
    </>
  );
}

function WingMesh({ wing }: { wing: WingOutline }) {
  const geometry = useMemo(() => {
    const geo = new BufferGeometry();
    if (wing.le.length < 1 || wing.te.length < 1) return geo;
    const le0 = wing.le[0];
    const le1 = wing.le[wing.le.length - 1];
    const te0 = wing.te[0];
    const te1 = wing.te[wing.te.length - 1];
    const pos = new Float32Array([...toThree(le0), ...toThree(te0), ...toThree(te1), ...toThree(le1)]);
    geo.setAttribute("position", new BufferAttribute(pos, 3));
    geo.setIndex([0, 1, 2, 0, 2, 3]);
    geo.computeVertexNormals();
    return geo;
  }, [wing]);
  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial color="#7dd3fc" roughness={0.45} metalness={0.1} side={DoubleSide} />
    </mesh>
  );
}

export function AircraftCanvas() {
  const aircraft = useStore(store, (s) => s.aircraft);
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
          {scene ? <FuselageLines polylines={scene.fuselage} /> : null}
          {scene
            ? scene.wings.map((wing, i) => <WingMesh key={i} wing={wing} />)
            : null}
          <OrbitControls />
        </Canvas>
      </div>
    </div>
  );
}
