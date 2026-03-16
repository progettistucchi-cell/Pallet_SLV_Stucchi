'use client';

import { useEffect, useState, useRef, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, Text, Box, Line } from '@react-three/drei';
import * as THREE from 'three';

// ─── Stessa palette colori del 2D ────────────────────────────────────────────
const PALETTE = [
    '#4A90D9', '#E87A3C', '#52B26B', '#9B59B6', '#E74C3C',
    '#1ABC9C', '#F39C12', '#2980B9', '#D35400', '#27AE60',
    '#8E44AD', '#C0392B', '#16A085', '#E67E22', '#2C3E50',
];

function getColorForType(typeKey: string, colorMap: Record<string, string>): string {
    return colorMap[typeKey] || '#AAAAAA';
}

function buildColorMap(boxes: any[]): Record<string, string> {
    const types = [...new Set(boxes.map(b => b.codice_scatola))];
    const map: Record<string, string> = {};
    types.forEach((t, i) => { map[t] = PALETTE[i % PALETTE.length]; });
    return map;
}

// ─── Griglia pavimento ───────────────────────────────────────────────────────
function PalletFloor({ l, p }: { l: number; p: number }) {
    // Scala mm → unità Three.js (dividiamo per 100 per avere valori maneggiabili)
    const lU = l / 100;
    const pU = p / 100;
    return (
        <group position={[lU / 2, 0, pU / 2]}>
            {/* Base */}
            <mesh position={[0, -0.05, 0]}>
                <boxGeometry args={[lU, 0.1, pU]} />
                <meshStandardMaterial color="#A0522D" roughness={0.9} />
            </mesh>
            {/* Griglia di riferimento */}
            <gridHelper
                args={[Math.max(lU, pU) * 1.2, 10, '#999999', '#CCCCCC']}
                position={[0, -0.09, 0]}
            />
        </group>
    );
}

// ─── Singola scatola 3D ──────────────────────────────────────────────────────
function Box3D({ box, color, onSelect, isSelected }: {
    box: any;
    color: string;
    onSelect: (box: any) => void;
    isSelected: boolean;
}) {
    const [hovered, setHovered] = useState(false);
    const S = 100; // scala mm → unità Three.js

    const lU = box.placed_l_mm / S;
    const pU = box.placed_p_mm / S;
    const hU = box.a_mm / S;
    const xU = (box.pos_x_mm + box.placed_l_mm / 2) / S;
    const zU = (box.pos_y_mm + box.placed_p_mm / 2) / S;
    const yU = (box.pos_z_mm + box.a_mm / 2) / S;

    const threeColor = new THREE.Color(color);
    const emissive = hovered || isSelected ? threeColor.clone().multiplyScalar(0.3) : new THREE.Color(0x000000);

    return (
        <group
            position={[xU, yU, zU]}
            onPointerOver={(e) => { e.stopPropagation(); setHovered(true); }}
            onPointerOut={() => setHovered(false)}
            onClick={(e) => { e.stopPropagation(); onSelect(box); }}
        >
            <mesh>
                <boxGeometry args={[lU, hU, pU]} />
                <meshStandardMaterial
                    color={color}
                    emissive={emissive}
                    opacity={box.is_piena ? 0.92 : 0.65}
                    transparent={!box.is_piena}
                    roughness={0.35}
                    metalness={0.05}
                />
            </mesh>
            {/* Bordi sempre visibili */}
            <lineSegments>
                <edgesGeometry args={[new THREE.BoxGeometry(lU, hU, pU)]} />
                <lineBasicMaterial
                    color={isSelected ? '#FFFFFF' : (hovered ? '#FFFFFF' : '#000000')}
                    opacity={isSelected ? 1 : (hovered ? 0.9 : 0.55)}
                    transparent
                />
            </lineSegments>
        </group>
    );
}

// ─── Scena 3D principale ─────────────────────────────────────────────────────
function Scene({ pallet }: { pallet: any }) {
    const colorMap = buildColorMap(pallet.layers.flatMap((l: any) => l.scatole));
    const [selectedBox, setSelectedBox] = useState<any>(null);

    const allBoxes = pallet.layers.flatMap((l: any) => l.scatole);

    return (
        <>
            <ambientLight intensity={0.6} />
            <directionalLight position={[10, 20, 10]} intensity={1.2} castShadow />
            <directionalLight position={[-10, 10, -5]} intensity={0.4} />

            <PalletFloor l={800} p={1200} />

            {allBoxes.map((box: any, i: number) => (
                <Box3D
                    key={`${box.cod_prodotto}-${i}`}
                    box={box}
                    color={getColorForType(box.codice_scatola, colorMap)}
                    onSelect={setSelectedBox}
                    isSelected={selectedBox && selectedBox === box}
                />
            ))}

            <OrbitControls
                makeDefault
                minDistance={2}
                maxDistance={40}
                target={[4, 4, 6]}
                enableDamping
                dampingFactor={0.08}
            />
        </>
    );
}

// ─── Legenda colori ──────────────────────────────────────────────────────────
function Legend({ pallet }: { pallet: any }) {
    const allBoxes = pallet.layers.flatMap((l: any) => l.scatole);
    const colorMap = buildColorMap(allBoxes);
    const entries = Object.entries(colorMap);

    return (
        <div style={{
            position: 'absolute', bottom: 16, left: 16, background: 'rgba(15,36,71,0.85)',
            borderRadius: 10, padding: '0.75rem 1rem', backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255,255,255,0.1)', maxWidth: 220,
        }}>
            <p style={{ color: '#93C5FD', fontSize: '0.7rem', fontWeight: 700, margin: '0 0 0.5rem', textTransform: 'uppercase', letterSpacing: 1 }}>
                Tipo Scatola
            </p>
            {entries.map(([tipo, col]) => (
                <div key={tipo} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <div style={{ width: 12, height: 12, borderRadius: 3, background: col, flexShrink: 0 }} />
                    <span style={{ color: '#E2E8F0', fontSize: '0.72rem', fontFamily: 'monospace' }}>{tipo}</span>
                </div>
            ))}
        </div>
    );
}

// ─── Info box scatola selezionata ─────────────────────────────────────────────
function InfoPanel({ box, onClose }: { box: any; onClose: () => void }) {
    if (!box) return null;
    return (
        <div style={{
            position: 'absolute', top: 16, right: 16,
            background: 'rgba(15,36,71,0.9)', borderRadius: 12, padding: '1rem 1.2rem',
            border: '1px solid rgba(255,255,255,0.15)', backdropFilter: 'blur(10px)',
            maxWidth: 260, color: '#FFFFFF',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#93C5FD' }}>📦 Scatola Selezionata</span>
                <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', fontSize: '1rem' }}>✕</button>
            </div>
            {[
                ['Prodotto', box.cod_prodotto],
                ['Scatola', box.codice_scatola],
                ['Dimensioni', `${box.placed_l_mm}×${box.placed_p_mm}×${box.a_mm} mm`],
                ['Posizione X/Y', `${box.pos_x_mm} / ${box.pos_y_mm} mm`],
                ['Quota Z', `${box.pos_z_mm} mm`],
                ['Pezzi', box.n_pezzi],
                ['Stato', box.is_piena ? '✅ PIENA' : `⚠️ PARZ. ${Math.round(box.fill_ratio * 100)}%`],
            ].map(([label, val]) => (
                <div key={label as string} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.73rem', color: '#94A3B8' }}>{label}</span>
                    <span style={{ fontSize: '0.73rem', fontWeight: 600, color: '#E2E8F0', textAlign: 'right', maxWidth: 140 }}>{val as string}</span>
                </div>
            ))}
        </div>
    );
}

// ─── Pagina principale ───────────────────────────────────────────────────────
function PalletContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const palletId = Number(searchParams.get('pallet') || '1');

    const [pallet, setPallet] = useState<any>(null);
    const [totalPallets, setTotalPallets] = useState(0);
    const [ordine, setOrdine] = useState<any>(null);
    const [selectedBox, setSelectedBox] = useState<any>(null);

    useEffect(() => {
        const stored = sessionStorage.getItem('palletResult');
        if (!stored) { router.push('/'); return; }
        const result = JSON.parse(stored);
        const found = result.pallet_list.find((p: any) => p.pallet_id === palletId);
        setOrdine(result.metadati);
        setTotalPallets(result.pallet_list.length);
        setPallet(found || result.pallet_list[0]);
    }, [palletId, router]);

    if (!pallet) {
        return (
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0F2447', color: '#93C5FD', fontFamily: 'Inter, sans-serif' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 48, marginBottom: 16 }}>⏳</div>
                    <p>Caricamento visualizzazione 3D...</p>
                </div>
            </div>
        );
    }

    const allBoxes = pallet.layers.flatMap((l: any) => l.scatole);
    const colorMap = buildColorMap(allBoxes);

    return (
        <div style={{ minHeight: '100vh', background: '#0F2447', display: 'flex', flexDirection: 'column', fontFamily: 'Inter, sans-serif' }}>
            {/* Top bar */}
            <div style={{
                background: 'rgba(10,20,45,0.95)', padding: '0.75rem 1.5rem',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                borderBottom: '1px solid rgba(255,255,255,0.08)', backdropFilter: 'blur(8px)',
                position: 'sticky', top: 0, zIndex: 10,
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ fontSize: 22 }}>📦</span>
                    <div>
                        <h1 style={{ color: '#FFFFFF', margin: 0, fontSize: '1rem', fontWeight: 700 }}>
                            Visualizzatore 3D — Pallet {pallet.pallet_id}
                        </h1>
                        <p style={{ color: '#93C5FD', margin: 0, fontSize: '0.72rem' }}>
                            {ordine?.nome_cliente} — Ordine {ordine?.numero_ordine} — {allBoxes.length} scatole
                        </p>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    {/* Selettore pallet */}
                    <div style={{ display: 'flex', gap: 6 }}>
                        {Array.from({ length: totalPallets }, (_, i) => i + 1).map(id => (
                            <button
                                key={id}
                                onClick={() => router.push(`/pallet-3d?pallet=${id}`)}
                                style={{
                                    padding: '0.4rem 0.75rem', borderRadius: 8, cursor: 'pointer', fontSize: '0.8rem', fontWeight: 700,
                                    background: id === pallet.pallet_id ? 'linear-gradient(135deg, #2563EB, #1A3C6E)' : 'rgba(255,255,255,0.08)',
                                    color: '#FFFFFF', border: `1px solid ${id === pallet.pallet_id ? '#60A5FA' : 'rgba(255,255,255,0.15)'}`,
                                }}
                            >
                                P{id}
                            </button>
                        ))}
                    </div>

                    <button
                        onClick={() => router.back()}
                        style={{
                            padding: '0.5rem 1rem', background: 'rgba(255,255,255,0.1)',
                            color: '#FFFFFF', border: '1px solid rgba(255,255,255,0.2)',
                            borderRadius: 8, cursor: 'pointer', fontWeight: 600, fontSize: '0.8rem',
                        }}
                    >
                        ← Risultati 2D
                    </button>
                </div>
            </div>

            {/* Stats strip */}
            <div style={{
                display: 'flex', gap: 24, padding: '0.6rem 1.5rem',
                background: 'rgba(10,20,45,0.7)', borderBottom: '1px solid rgba(255,255,255,0.05)',
            }}>
                {[
                    { label: 'Altezza picco', value: `${pallet.altezza_totale_mm} mm` },
                    { label: 'Riempimento', value: `${pallet.fill_pct}%` },
                    { label: 'Scatole', value: allBoxes.length },
                    { label: 'Step Z', value: pallet.layers.length },
                ].map(s => (
                    <div key={s.label} style={{ textAlign: 'center' }}>
                        <div style={{ color: '#FFFFFF', fontWeight: 700, fontSize: '1rem' }}>{s.value}</div>
                        <div style={{ color: '#94A3B8', fontSize: '0.68rem' }}>{s.label}</div>
                    </div>
                ))}
                <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ color: '#64748B', fontSize: '0.72rem' }}>🖱️ Drag per ruotare · Scroll per zoom · Click per dettagli</span>
                </div>
            </div>

            {/* Canvas 3D */}
            <div style={{ position: 'relative', width: '100%', height: 'calc(100vh - 130px)' }}>
                {pallet && (
                    <Canvas
                        shadows
                        camera={{
                            position: [
                                14,
                                Math.max((pallet.altezza_totale_mm / 100) * 0.5, 5),
                                18
                            ],
                            fov: 50,
                            near: 0.1,
                            far: 500
                        }}
                        style={{ background: '#0F2447' }}
                    >
                        <Suspense fallback={null}>
                            <SceneWithPanel pallet={pallet} colorMap={colorMap} onSelectBox={setSelectedBox} selectedBox={selectedBox} />
                        </Suspense>
                    </Canvas>
                )}

                <Legend pallet={pallet} />

                {selectedBox && (
                    <InfoPanel box={selectedBox} onClose={() => setSelectedBox(null)} />
                )}
            </div>
        </div>
    );
}

// ─── Scena wrapper con state lifting ─────────────────────────────────────────
function SceneWithPanel({ pallet, colorMap, onSelectBox, selectedBox }: {
    pallet: any;
    colorMap: Record<string, string>;
    onSelectBox: (box: any) => void;
    selectedBox: any;
}) {
    const allBoxes = pallet.layers.flatMap((l: any) => l.scatole);
    const hU = pallet.altezza_totale_mm / 100; // Altezza reale in unità Three.js
    const targetY = hU / 2; // Centro verticale

    return (
        <>
            <ambientLight intensity={0.7} />
            <directionalLight position={[10, 20, 10]} intensity={1.2} castShadow />
            <directionalLight position={[-10, 10, -5]} intensity={0.5} />
            <directionalLight position={[0, 5, 15]} intensity={0.3} />

            <PalletFloor l={800} p={1200} />

            {allBoxes.map((box: any, i: number) => (
                <Box3D
                    key={`${box.cod_prodotto}-${i}`}
                    box={box}
                    color={getColorForType(box.codice_scatola, colorMap)}
                    onSelect={onSelectBox}
                    isSelected={selectedBox === box}
                />
            ))}

            <OrbitControls
                makeDefault
                minDistance={5}
                maxDistance={50}
                target={[4, targetY, 6]}
                enableDamping
                dampingFactor={0.08}
            />
        </>
    );
}

export default function Pallet3DPage() {
    return (
        <Suspense fallback={
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0F2447', color: '#93C5FD' }}>
                <div style={{ textAlign: 'center', fontSize: 24 }}>Caricamento 3D...</div>
            </div>
        }>
            <PalletContent />
        </Suspense>
    );
}
