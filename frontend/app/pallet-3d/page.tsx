'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

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

function PalletFloor({ l, p }: { l: number; p: number }) {
    const lU = l / 100;
    const pU = p / 100;
    return (
        <group position={[lU / 2, 0, pU / 2]}>
            <mesh position={[0, -0.05, 0]}>
                <boxGeometry args={[lU, 0.1, pU]} />
                <meshStandardMaterial color="#A0522D" roughness={0.9} />
            </mesh>
            <gridHelper
                args={[Math.max(lU, pU) * 1.2, 10, '#999999', '#CCCCCC']}
                position={[0, -0.09, 0]}
            />
        </group>
    );
}

function Box3D({ box, color, onSelect, isSelected }: {
    box: any;
    color: string;
    onSelect: (box: any) => void;
    isSelected: boolean;
}) {
    const [hovered, setHovered] = useState(false);
    const S = 100;

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
            {/* Bordi sempre visibili per distinguere le scatole */}
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

function Legend({ pallet }: { pallet: any }) {
    const allBoxes = pallet.layers.flatMap((l: any) => l.scatole);
    const colorMap = buildColorMap(allBoxes);
    const entries = Object.entries(colorMap);

    return (
        <div style={{
            position: 'absolute', bottom: 16, left: 16, background: 'rgba(0,0,0,0.88)',
            borderRadius: 10, padding: '0.75rem 1rem', backdropFilter: 'blur(8px)',
            border: '1px solid #2a2a2a', maxWidth: 220,
        }}>
            <p style={{ color: '#888888', fontSize: '0.7rem', fontWeight: 700, margin: '0 0 0.5rem', textTransform: 'uppercase', letterSpacing: 1 }}>
                Tipo Scatola
            </p>
            {entries.map(([tipo, col]) => (
                <div key={tipo} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <div style={{ width: 12, height: 12, borderRadius: 3, background: col, flexShrink: 0 }} />
                    <span style={{ color: '#CCCCCC', fontSize: '0.72rem', fontFamily: 'monospace' }}>{tipo}</span>
                </div>
            ))}
        </div>
    );
}

function InfoPanel({ box, onClose }: { box: any; onClose: () => void }) {
    if (!box) return null;
    return (
        <div style={{
            position: 'absolute', top: 16, right: 16,
            background: 'rgba(0,0,0,0.92)', borderRadius: 12, padding: '1rem 1.2rem',
            border: '1px solid #2a2a2a', backdropFilter: 'blur(10px)',
            maxWidth: 260, color: '#FFFFFF',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#E87A3C' }}>Scatola Selezionata</span>
                <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#555555', cursor: 'pointer', fontSize: '1rem' }}>&times;</button>
            </div>
            {[
                ['Prodotto', box.cod_prodotto],
                ['Scatola', box.codice_scatola],
                ['Dimensioni', `${box.placed_l_mm}\u00D7${box.placed_p_mm}\u00D7${box.a_mm} mm`],
                ['Posizione X/Y', `${box.pos_x_mm} / ${box.pos_y_mm} mm`],
                ['Quota Z', `${box.pos_z_mm} mm`],
                ['Pezzi', box.n_pezzi],
                ['Stato', box.is_piena ? 'PIENA' : `PARZ. ${Math.round(box.fill_ratio * 100)}%`],
            ].map(([label, val]) => (
                <div key={label as string} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: '0.73rem', color: '#555555' }}>{label}</span>
                    <span style={{ fontSize: '0.73rem', fontWeight: 600, color: '#CCCCCC', textAlign: 'right', maxWidth: 140 }}>{val as string}</span>
                </div>
            ))}
        </div>
    );
}

function SceneWithPanel({ pallet, colorMap, onSelectBox, selectedBox }: {
    pallet: any;
    colorMap: Record<string, string>;
    onSelectBox: (box: any) => void;
    selectedBox: any;
}) {
    const allBoxes = pallet.layers.flatMap((l: any) => l.scatole);
    const hU = pallet.altezza_totale_mm / 100;
    const targetY = hU / 2;

    return (
        <>
            <ambientLight intensity={0.6} />
            <directionalLight position={[10, 20, 10]} intensity={1.2} castShadow />
            <directionalLight position={[-10, 10, -5]} intensity={0.4} />
            <fog attach="fog" args={['#0c1a2e', 40, 100]} />

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
                minDistance={2}
                maxDistance={60}
                target={[4, targetY, 6]}
                enableDamping
                dampingFactor={0.08}
            />
        </>
    );
}

function Pallet3DInner() {
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
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000000', color: '#888888', fontFamily: 'Inter, sans-serif' }}>
                <p>Caricamento visualizzazione 3D...</p>
            </div>
        );
    }

    const allBoxes = pallet.layers.flatMap((l: any) => l.scatole);
    const colorMap = buildColorMap(allBoxes);

    return (
        <div style={{ height: '100vh', background: '#0a0a0a', display: 'flex', flexDirection: 'column', fontFamily: 'Inter, sans-serif', overflow: 'hidden' }}>
            {/* Top bar */}
            <div style={{
                background: '#000000', padding: '0.75rem 1.5rem',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                borderBottom: '1px solid #1e1e1e',
                position: 'sticky', top: 0, zIndex: 10,
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <Image
                        src="/logo-stucchi-white.png"
                        alt="Stucchi"
                        width={100}
                        height={52}
                        style={{ objectFit: 'contain' }}
                    />
                    <div style={{ width: 1, height: 28, background: '#2a2a2a' }} />
                    <div>
                        <div style={{ color: '#FFFFFF', fontWeight: 600, fontSize: '0.9rem' }}>
                            Visualizzatore 3D &mdash; Pallet {pallet.pallet_id}
                        </div>
                        <div style={{ color: '#555555', fontSize: '0.72rem' }}>
                            {ordine?.nome_cliente} &mdash; Ordine {ordine?.numero_ordine} &mdash; {allBoxes.length} scatole
                        </div>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <div style={{ display: 'flex', gap: 6 }}>
                        {Array.from({ length: totalPallets }, (_, i) => i + 1).map(id => (
                            <button
                                key={id}
                                onClick={() => router.push(`/pallet-3d?pallet=${id}`)}
                                style={{
                                    padding: '0.4rem 0.75rem', borderRadius: 8, cursor: 'pointer', fontSize: '0.8rem', fontWeight: 700,
                                    background: id === pallet.pallet_id ? '#E87A3C' : '#141414',
                                    color: '#FFFFFF', border: `1px solid ${id === pallet.pallet_id ? '#E87A3C' : '#2a2a2a'}`,
                                }}
                            >
                                P{id}
                            </button>
                        ))}
                    </div>

                    <button
                        onClick={() => router.back()}
                        style={{
                            padding: '0.5rem 1rem', background: '#141414',
                            color: '#CCCCCC', border: '1px solid #2a2a2a',
                            borderRadius: 8, cursor: 'pointer', fontWeight: 600, fontSize: '0.8rem',
                        }}
                    >
                        &larr; Risultati 2D
                    </button>
                </div>
            </div>

            {/* Stats strip */}
            <div style={{
                display: 'flex', gap: 24, padding: '0.6rem 1.5rem',
                background: '#0f0f0f', borderBottom: '1px solid #1a1a1a',
            }}>
                {[
                    { label: 'Altezza picco', value: `${pallet.altezza_totale_mm} mm`, accent: false },
                    { label: 'Riempimento', value: `${pallet.fill_pct}%`, accent: true },
                    { label: 'Scatole', value: allBoxes.length, accent: false },
                    { label: 'Step Z', value: pallet.layers.length, accent: false },
                ].map(s => (
                    <div key={s.label} style={{ textAlign: 'center' }}>
                        <div style={{ color: s.accent ? '#E87A3C' : '#FFFFFF', fontWeight: 700, fontSize: '1rem' }}>{s.value}</div>
                        <div style={{ color: '#444444', fontSize: '0.68rem' }}>{s.label}</div>
                    </div>
                ))}
                <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
                    <span style={{ color: '#333333', fontSize: '0.72rem' }}>Drag per ruotare &middot; Scroll per zoom &middot; Click per dettagli</span>
                </div>
            </div>

            {/* Canvas 3D */}
            <div style={{ flex: 1, position: 'relative', minHeight: 0, overflow: 'hidden' }}>
                {pallet && (
                    <Canvas
                        shadows
                        camera={{ position: [14, (pallet.altezza_totale_mm / 100) + 8, 22], fov: 45, near: 0.1, far: 500 }}
                        style={{ display: 'block', width: '100%', height: '100%', background: 'linear-gradient(180deg, #1e3a5f 0%, #0c1a2e 100%)' }}
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

export default function Pallet3DPage() {
    return (
        <Suspense fallback={
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000000', color: '#888888', fontFamily: 'Inter, sans-serif' }}>
                <p>Caricamento...</p>
            </div>
        }>
            <Pallet3DInner />
        </Suspense>
    );
}
