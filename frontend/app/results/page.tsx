'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';

interface Box {
    id: number;
    cod_prodotto: string;
    codice_scatola: string;
    l_mm: number;
    p_mm: number;
    a_mm: number;
    placed_l_mm: number;
    placed_p_mm: number;
    pos_x_mm: number;
    pos_y_mm: number;
    n_pezzi: number;
    is_piena: boolean;
    fill_ratio: number;
    rotated: boolean;
}

interface Layer {
    layer_n: number;
    tipo: 'PIENA' | 'PARZIALE';
    altezza_mm: number;
    altezza_cumulativa_mm: number;
    n_scatole: number;
    scatole: Box[];
}

interface Pallet {
    pallet_id: number;
    layers: Layer[];
    altezza_totale_mm: number;
    n_scatole: number;
    fill_pct: number;
}

interface PalletResult {
    metadati: { cliente: string; nome_cliente: string; numero_ordine: string; data_ordine: string };
    n_pallet: number;
    pallet_list: Pallet[];
    riepilogo_boxing: { n_scatole_totali: number; n_scatole_piene: number; n_scatole_parziali: number };
    warnings: { prodotti_non_trovati: string[]; skippati_db: any[] };
    pdf_filename: string | null;
    img_filenames: string[];
}

const PALETTE = [
    '#4A90D9', '#E87A3C', '#52B26B', '#9B59B6', '#E74C3C',
    '#1ABC9C', '#F39C12', '#2980B9', '#D35400', '#27AE60',
];

function PalletCard({ pallet, imgFilenames }: { pallet: Pallet; imgFilenames?: string[] }) {
    const router = useRouter();
    const [expanded, setExpanded] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const touchStartX = useRef<number | null>(null);

    const heightPct = Math.round((pallet.altezza_totale_mm / 1600) * 100);
    const numSteps = imgFilenames?.length || 0;

    const handleTouchStart = (e: React.TouchEvent) => {
        touchStartX.current = e.touches[0].clientX;
    };

    const handleTouchEnd = (e: React.TouchEvent) => {
        if (touchStartX.current === null) return;
        const touchEndX = e.changedTouches[0].clientX;
        const diff = touchStartX.current - touchEndX;

        // Swipe left (next)
        if (diff > 50 && currentStep < numSteps - 1) {
            setCurrentStep(prev => prev + 1);
        }
        // Swipe right (prev)
        if (diff < -50 && currentStep > 0) {
            setCurrentStep(prev => prev - 1);
        }
        touchStartX.current = null;
    };

    return (
        <div style={{
            background: '#FFFFFF', borderRadius: 16,
            border: '1px solid #E2E8F0', overflow: 'hidden',
            boxShadow: '0 4px 16px rgba(26,60,110,0.08)',
            transition: 'box-shadow 0.2s ease',
        }}>
            {/* Header Pallet */}
            <div style={{
                background: 'linear-gradient(135deg, #1A3C6E, #2563EB)',
                padding: '1.25rem 1.5rem',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
                <div>
                    <h3 style={{ color: '#FFFFFF', margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>
                        📦 Pallet {pallet.pallet_id}
                    </h3>
                    <p style={{ color: '#93C5FD', margin: '0.2rem 0 0', fontSize: '0.8rem' }}>
                        {pallet.n_scatole} scatole • {pallet.layers.length} layer
                    </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    {/* Bottone 3D */}
                    <button
                        onClick={() => router.push(`/pallet-3d?pallet=${pallet.pallet_id}`)}
                        style={{
                            padding: '0.45rem 0.9rem', borderRadius: 10, cursor: 'pointer',
                            background: 'linear-gradient(135deg, rgba(139,92,246,0.9), rgba(79,70,229,0.9))',
                            color: '#FFFFFF', border: '1px solid rgba(255,255,255,0.25)',
                            fontWeight: 700, fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: 5,
                            boxShadow: '0 2px 8px rgba(139,92,246,0.4)',
                        }}
                    >
                        🧊 3D
                    </button>
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ color: '#FFFFFF', fontWeight: 800, fontSize: '1.5rem' }}>
                            {pallet.fill_pct}%
                        </div>
                        <div style={{ color: '#93C5FD', fontSize: '0.7rem' }}>riempimento</div>
                    </div>
                </div>
            </div>

            {/* Stats bar */}
            <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #F1F5F9' }}>
                <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '0.75rem' }}>
                    {[
                        { label: 'Altezza', value: `${pallet.altezza_totale_mm} mm`, icon: '📏' },
                        { label: 'Layer', value: `${pallet.layers.length}`, icon: '⬜' },
                        { label: 'Scatole', value: `${pallet.n_scatole}`, icon: '🗃️' },
                    ].map(s => (
                        <div key={s.label} style={{ flex: 1, textAlign: 'center' }}>
                            <div style={{ fontSize: 18 }}>{s.icon}</div>
                            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#1A3C6E' }}>{s.value}</div>
                            <div style={{ fontSize: '0.7rem', color: '#94A3B8' }}>{s.label}</div>
                        </div>
                    ))}
                </div>

                {/* Barra altezza */}
                <div style={{ background: '#F1F5F9', borderRadius: 6, height: 8, overflow: 'hidden' }}>
                    <div style={{
                        height: '100%', borderRadius: 6,
                        width: `${heightPct}%`,
                        background: heightPct > 90 ? '#DC2626' : heightPct > 70 ? '#D97706' : '#16A34A',
                        transition: 'width 0.5s ease',
                    }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                    <span style={{ fontSize: '0.7rem', color: '#94A3B8' }}>0 mm</span>
                    <span style={{ fontSize: '0.7rem', color: '#94A3B8' }}>{pallet.altezza_totale_mm} / 1600 mm</span>
                </div>
            </div>

            {/* Immagine layer - CAROUSEL */}
            {numSteps > 0 && imgFilenames && (
                <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #F1F5F9' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <p style={{ fontSize: '0.8rem', color: '#64748B', margin: 0, fontWeight: 600 }}>
                            Sequenza di Montaggio
                        </p>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1A3C6E', background: '#F1F5F9', padding: '2px 8px', borderRadius: 12 }}>
                            Step {currentStep + 1} di {numSteps}
                        </span>
                    </div>

                    <div 
                        style={{ position: 'relative', background: '#F8FAFC', borderRadius: 8, border: '1px solid #E2E8F0', padding: '0.5rem', overflow: 'hidden', touchAction: 'pan-y' }}
                        onTouchStart={handleTouchStart}
                        onTouchEnd={handleTouchEnd}
                    >
                        <div style={{
                            display: 'flex',
                            transition: 'transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)',
                            transform: `translateX(-${currentStep * 100}%)`,
                            width: '100%',
                        }}>
                            {imgFilenames.map((filename, i) => (
                                /* eslint-disable-next-line @next/next/no-img-element */
                                <img
                                    key={filename}
                                    src={`${process.env.NEXT_PUBLIC_API_URL || ''}/api/images/${filename}`}
                                    alt={`Pallet ${pallet.pallet_id} step ${i + 1}`}
                                    style={{ flex: '0 0 100%', width: '100%', borderRadius: 4, display: 'block', pointerEvents: 'none', objectFit: 'contain' }}
                                />
                            ))}
                        </div>
                        
                        {/* Controlli slider */}
                        {numSteps > 1 && (
                            <>
                                <button 
                                    onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
                                    disabled={currentStep === 0}
                                    style={{
                                        position: 'absolute', top: '50%', left: '0.5rem', transform: 'translateY(-50%)',
                                        width: 32, height: 32, borderRadius: '50%', background: 'white', border: '1px solid #CBD5E1',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)', cursor: currentStep === 0 ? 'default' : 'pointer',
                                        opacity: currentStep === 0 ? 0.5 : 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: '1rem', color: '#1E293B', padding: 0, paddingRight: 2
                                    }}
                                >
                                    ◀
                                </button>
                                <button 
                                    onClick={() => setCurrentStep(prev => Math.min(numSteps - 1, prev + 1))}
                                    disabled={currentStep === numSteps - 1}
                                    style={{
                                        position: 'absolute', top: '50%', right: '0.5rem', transform: 'translateY(-50%)',
                                        width: 32, height: 32, borderRadius: '50%', background: 'white', border: '1px solid #CBD5E1',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)', cursor: currentStep === numSteps - 1 ? 'default' : 'pointer',
                                        opacity: currentStep === numSteps - 1 ? 0.5 : 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: '1rem', color: '#1E293B', padding: 0, paddingLeft: 2
                                    }}
                                >
                                    ▶
                                </button>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* Layer accordion */}
            <div style={{ padding: '1rem 1.5rem' }}>
                <button
                    onClick={() => setExpanded(!expanded)}
                    style={{
                        width: '100%', padding: '0.6rem', background: '#F8FAFC',
                        border: '1px solid #E2E8F0', borderRadius: 8, cursor: 'pointer',
                        color: '#1A3C6E', fontWeight: 600, fontSize: '0.85rem',
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    }}
                >
                    <span>📋 Dettaglio Layer</span>
                    <span>{expanded ? '▲' : '▼'}</span>
                </button>

                {expanded && (
                    <div style={{ marginTop: '0.75rem' }}>
                        {pallet.layers.map((layer) => (
                            <div key={layer.layer_n} style={{
                                marginBottom: '0.75rem', borderRadius: 10,
                                border: `1px solid ${layer.tipo === 'PIENA' ? '#BBF7D0' : '#FED7AA'}`,
                                overflow: 'hidden',
                            }}>
                                <div style={{
                                    padding: '0.6rem 1rem',
                                    background: layer.tipo === 'PIENA' ? '#F0FDF4' : '#FFF7ED',
                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                }}>
                                    <span style={{
                                        fontWeight: 700, fontSize: '0.85rem',
                                        color: layer.tipo === 'PIENA' ? '#16A34A' : '#D97706',
                                    }}>
                                        Layer {layer.layer_n} — {layer.tipo}
                                    </span>
                                    <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                                        H: {layer.altezza_mm}mm | Cum: {layer.altezza_cumulativa_mm}mm | {layer.n_scatole} scatole
                                    </span>
                                </div>
                                <div style={{ padding: '0.5rem 0' }}>
                                    {layer.scatole.map((box, i) => (
                                        <div key={`${box.id}-${i}`} style={{
                                            padding: '0.35rem 1rem',
                                            borderBottom: i < layer.scatole.length - 1 ? '1px solid #F1F5F9' : 'none',
                                            display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap',
                                        }}>
                                            <span style={{
                                                width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                                                background: box.is_piena ? '#16A34A' : '#D97706',
                                                display: 'inline-block',
                                            }} />
                                            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#1E293B', minWidth: 140 }}>
                                                {box.cod_prodotto}
                                            </span>
                                            <span style={{ fontSize: '0.72rem', color: '#64748B' }}>
                                                {box.codice_scatola}
                                            </span>
                                            <span style={{ fontSize: '0.72rem', color: '#475569' }}>
                                                {box.placed_l_mm}×{box.placed_p_mm}×{box.a_mm}mm
                                            </span>
                                            <span style={{ fontSize: '0.72rem', color: '#94A3B8' }}>
                                                pos ({box.pos_x_mm},{box.pos_y_mm})
                                            </span>
                                            {box.rotated && <span style={{ fontSize: '0.65rem', color: '#2563EB', background: '#EFF6FF', padding: '1px 5px', borderRadius: 4 }}>↺ 90°</span>}
                                            <span style={{
                                                fontSize: '0.68rem', fontWeight: 600,
                                                color: box.is_piena ? '#16A34A' : '#D97706',
                                                background: box.is_piena ? '#F0FDF4' : '#FFF7ED',
                                                padding: '1px 6px', borderRadius: 4,
                                            }}>
                                                {box.is_piena ? 'PIENA' : `PARZ. ${Math.round(box.fill_ratio * 100)}%`}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default function ResultsPage() {
    const router = useRouter();
    const [result, setResult] = useState<PalletResult | null>(null);

    useEffect(() => {
        const stored = sessionStorage.getItem('palletResult');
        if (!stored) { router.push('/'); return; }
        setResult(JSON.parse(stored));
    }, [router]);

    if (!result) {
        return (
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F0F4FA' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 48, marginBottom: '1rem' }}>⏳</div>
                    <p style={{ color: '#64748B' }}>Caricamento risultati...</p>
                </div>
            </div>
        );
    }

    const hasWarnings = result.warnings.prodotti_non_trovati?.length > 0 || result.warnings.skippati_db?.length > 0;

    return (
        <div style={{ minHeight: '100vh', background: '#F0F4FA', fontFamily: 'Inter, sans-serif' }}>
            {/* Top bar */}
            <div style={{
                background: 'linear-gradient(135deg, #0F2447, #1A3C6E)',
                padding: '1rem 2rem',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ fontSize: 24 }}>📦</span>
                    <div>
                        <h1 style={{ color: '#FFFFFF', margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>
                            Pallet Optimizer
                        </h1>
                        <p style={{ color: '#93C5FD', margin: 0, fontSize: '0.75rem' }}>
                            {result.metadati.nome_cliente} — Ordine {result.metadati.numero_ordine}
                        </p>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                    {result.pdf_filename && (
                        <a
                            href={`${process.env.NEXT_PUBLIC_API_URL || ''}/api/download-pdf/${result.pdf_filename}`}
                            download
                            style={{
                                padding: '0.6rem 1.25rem',
                                background: 'linear-gradient(135deg, #E87A3C, #F59E0B)',
                                color: '#FFFFFF', borderRadius: 10, textDecoration: 'none',
                                fontWeight: 700, fontSize: '0.875rem',
                                boxShadow: '0 4px 14px rgba(232,122,60,0.4)',
                                display: 'flex', alignItems: 'center', gap: 6,
                            }}
                        >
                            ⬇️ Scarica PDF
                        </a>
                    )}
                    <button
                        onClick={() => router.push('/')}
                        style={{
                            padding: '0.6rem 1rem', background: 'rgba(255,255,255,0.12)',
                            color: '#FFFFFF', border: '1px solid rgba(255,255,255,0.2)',
                            borderRadius: 10, cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
                        }}
                    >
                        ← Nuovo Ordine
                    </button>
                </div>
            </div>

            {/* Content */}
            <div style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem' }}>

                {/* Stats overview */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
                    {[
                        { icon: '🚛', label: 'Pallet Totali', value: result.n_pallet, color: '#1A3C6E' },
                        { icon: '📦', label: 'Scatole Totali', value: result.riepilogo_boxing.n_scatole_totali, color: '#2563EB' },
                        { icon: '✅', label: 'Scatole Piene', value: result.riepilogo_boxing.n_scatole_piene, color: '#16A34A' },
                        { icon: '🔶', label: 'Scatole Parziali', value: result.riepilogo_boxing.n_scatole_parziali, color: '#D97706' },
                    ].map(s => (
                        <div key={s.label} style={{
                            background: '#FFFFFF', borderRadius: 14, padding: '1.25rem',
                            boxShadow: '0 2px 8px rgba(26,60,110,0.06)',
                            border: '1px solid #E2E8F0', textAlign: 'center',
                        }}>
                            <div style={{ fontSize: 28, marginBottom: 4 }}>{s.icon}</div>
                            <div style={{ fontSize: '2rem', fontWeight: 800, color: s.color }}>{s.value}</div>
                            <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: 2 }}>{s.label}</div>
                        </div>
                    ))}
                </div>

                {/* Warnings */}
                {hasWarnings && (
                    <div style={{
                        background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 12,
                        padding: '1rem 1.5rem', marginBottom: '1.5rem',
                    }}>
                        <h3 style={{ color: '#92400E', margin: '0 0 0.5rem', fontSize: '0.9rem', fontWeight: 700 }}>
                            ⚠️ Prodotti non palletizzati
                        </h3>
                        {result.warnings.prodotti_non_trovati?.map(cod => (
                            <div key={cod} style={{ fontSize: '0.8rem', color: '#78350F' }}>• {cod} — non trovato nel DB prodotti</div>
                        ))}
                        {result.warnings.skippati_db?.map((item: any, i) => (
                            <div key={i} style={{ fontSize: '0.8rem', color: '#78350F' }}>
                                • {typeof item === 'object' ? `${item.cod} — ${item.motivo}` : item}
                            </div>
                        ))}
                    </div>
                )}

                {/* Grid pallet */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem' }}>
                    {result.pallet_list.map((pallet) => {
                        const imgFilenames = result.img_filenames
                            .filter(f => f.includes(`pallet_${String(pallet.pallet_id).padStart(2, '0')}`))
                            .sort(); // sort per avere step_01, step_02... ecc in ordine

                        return (
                            <PalletCard
                                key={pallet.pallet_id}
                                pallet={pallet}
                                imgFilenames={imgFilenames}
                            />
                        );
                    })}
                </div>

                {/* Report testuale collassabile */}
                <details style={{
                    marginTop: '2rem', background: '#FFFFFF', borderRadius: 12,
                    border: '1px solid #E2E8F0', padding: '1rem 1.5rem',
                }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 600, color: '#1A3C6E', fontSize: '0.9rem' }}>
                        📄 Report Testuale Completo
                    </summary>
                    <pre style={{
                        marginTop: '1rem', fontSize: '0.75rem', color: '#334155',
                        background: '#F8FAFC', padding: '1rem', borderRadius: 8,
                        overflow: 'auto', maxHeight: 400, lineHeight: 1.6,
                    }}>
                        {(result as any).report_testo}
                    </pre>
                </details>
            </div>
        </div>
    );
}
