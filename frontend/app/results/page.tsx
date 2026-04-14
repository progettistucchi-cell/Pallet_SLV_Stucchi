'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

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
        if (diff > 50 && currentStep < numSteps - 1) setCurrentStep(prev => prev + 1);
        if (diff < -50 && currentStep > 0) setCurrentStep(prev => prev - 1);
        touchStartX.current = null;
    };

    return (
        <div style={{
            background: '#FFFFFF', borderRadius: 16,
            border: '1px solid #E2E8F0', overflow: 'hidden',
            boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
            transition: 'box-shadow 0.2s ease',
        }}>
            {/* Header Pallet */}
            <div style={{
                background: '#000000',
                borderBottom: '1px solid #1a1a1a',
                padding: '1.25rem 1.5rem',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
                <div>
                    <h3 style={{ color: '#FFFFFF', margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>
                        Pallet {pallet.pallet_id}
                    </h3>
                    <p style={{ color: '#666666', margin: '0.2rem 0 0', fontSize: '0.8rem' }}>
                        {pallet.n_scatole} scatole &bull; {pallet.layers.length} layer
                    </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button
                        onClick={() => router.push(`/pallet-3d?pallet=${pallet.pallet_id}`)}
                        style={{
                            padding: '0.45rem 0.9rem', borderRadius: 8, cursor: 'pointer',
                            background: 'rgba(232,122,60,0.15)',
                            color: '#E87A3C', border: '1px solid rgba(232,122,60,0.35)',
                            fontWeight: 700, fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: 5,
                        }}
                    >
                        Vista 3D
                    </button>
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ color: '#FFFFFF', fontWeight: 800, fontSize: '1.5rem' }}>
                            {pallet.fill_pct}%
                        </div>
                        <div style={{ color: '#555555', fontSize: '0.7rem' }}>riempimento</div>
                    </div>
                </div>
            </div>

            {/* Stats */}
            <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #F1F5F9' }}>
                <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '0.75rem' }}>
                    {[
                        { label: 'Altezza', value: `${pallet.altezza_totale_mm} mm` },
                        { label: 'Layer', value: `${pallet.layers.length}` },
                        { label: 'Scatole', value: `${pallet.n_scatole}` },
                    ].map(s => (
                        <div key={s.label} style={{ flex: 1, textAlign: 'center' }}>
                            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#1E293B' }}>{s.value}</div>
                            <div style={{ fontSize: '0.7rem', color: '#94A3B8' }}>{s.label}</div>
                        </div>
                    ))}
                </div>
                <div style={{ background: '#F1F5F9', borderRadius: 6, height: 6, overflow: 'hidden' }}>
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

            {/* Carousel immagini */}
            {numSteps > 0 && imgFilenames && (
                <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #F1F5F9' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <p style={{ fontSize: '0.8rem', color: '#64748B', margin: 0, fontWeight: 600 }}>
                            Sequenza di Montaggio
                        </p>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#E87A3C', background: 'rgba(232,122,60,0.08)', padding: '2px 8px', borderRadius: 12, border: '1px solid rgba(232,122,60,0.2)' }}>
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
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                    key={filename}
                                    src={`${process.env.NEXT_PUBLIC_API_URL || ''}/api/images/${filename}`}
                                    alt={`Pallet ${pallet.pallet_id} step ${i + 1}`}
                                    style={{ flex: '0 0 100%', width: '100%', borderRadius: 4, display: 'block', pointerEvents: 'none', objectFit: 'contain' }}
                                />
                            ))}
                        </div>

                        {numSteps > 1 && (
                            <>
                                <button
                                    onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
                                    disabled={currentStep === 0}
                                    style={{
                                        position: 'absolute', top: '50%', left: '0.5rem', transform: 'translateY(-50%)',
                                        width: 32, height: 32, borderRadius: '50%', background: 'rgba(0,0,0,0.5)', border: 'none',
                                        cursor: currentStep === 0 ? 'default' : 'pointer',
                                        opacity: currentStep === 0 ? 0.3 : 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: '1rem', color: '#FFFFFF', padding: 0,
                                    }}
                                >&lsaquo;</button>
                                <button
                                    onClick={() => setCurrentStep(prev => Math.min(numSteps - 1, prev + 1))}
                                    disabled={currentStep === numSteps - 1}
                                    style={{
                                        position: 'absolute', top: '50%', right: '0.5rem', transform: 'translateY(-50%)',
                                        width: 32, height: 32, borderRadius: '50%', background: 'rgba(0,0,0,0.5)', border: 'none',
                                        cursor: currentStep === numSteps - 1 ? 'default' : 'pointer',
                                        opacity: currentStep === numSteps - 1 ? 0.3 : 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: '1rem', color: '#FFFFFF', padding: 0,
                                    }}
                                >&rsaquo;</button>
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
                        color: '#64748B', fontWeight: 600, fontSize: '0.85rem',
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    }}
                >
                    <span>Dettaglio Layer</span>
                    <span>{expanded ? '\u25B2' : '\u25BC'}</span>
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
                                    <span style={{ fontWeight: 700, fontSize: '0.85rem', color: layer.tipo === 'PIENA' ? '#16A34A' : '#D97706' }}>
                                        Layer {layer.layer_n} &mdash; {layer.tipo}
                                    </span>
                                    <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                                        H: {layer.altezza_mm}mm | Cum: {layer.altezza_cumulativa_mm}mm | {layer.n_scatole} sc.
                                    </span>
                                </div>
                                <div style={{ padding: '0.5rem 0' }}>
                                    {layer.scatole.map((box, i) => (
                                        <div key={`${box.id}-${i}`} style={{
                                            padding: '0.35rem 1rem',
                                            borderBottom: i < layer.scatole.length - 1 ? '1px solid #F1F5F9' : 'none',
                                            display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap',
                                        }}>
                                            <span style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0, background: box.is_piena ? '#16A34A' : '#D97706', display: 'inline-block' }} />
                                            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#1E293B', minWidth: 140 }}>{box.cod_prodotto}</span>
                                            <span style={{ fontSize: '0.72rem', color: '#64748B' }}>{box.codice_scatola}</span>
                                            <span style={{ fontSize: '0.72rem', color: '#475569' }}>{box.placed_l_mm}&times;{box.placed_p_mm}&times;{box.a_mm}mm</span>
                                            {box.rotated && <span style={{ fontSize: '0.65rem', color: '#E87A3C', background: 'rgba(232,122,60,0.1)', padding: '1px 5px', borderRadius: 4 }}>90&deg;</span>}
                                            <span style={{ fontSize: '0.68rem', fontWeight: 600, color: box.is_piena ? '#16A34A' : '#D97706', background: box.is_piena ? '#F0FDF4' : '#FFF7ED', padding: '1px 6px', borderRadius: 4 }}>
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
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000000' }}>
                <div style={{ textAlign: 'center' }}>
                    <p style={{ color: '#555555' }}>Caricamento risultati...</p>
                </div>
            </div>
        );
    }

    const hasWarnings = result.warnings.prodotti_non_trovati?.length > 0 || result.warnings.skippati_db?.length > 0;

    return (
        <div style={{ minHeight: '100vh', background: '#0a0a0a', fontFamily: 'Inter, sans-serif' }}>
            {/* Top bar */}
            <div style={{
                background: '#000000',
                padding: '0.85rem 2rem',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                borderBottom: '1px solid #1e1e1e',
                position: 'sticky', top: 0, zIndex: 50,
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <Image
                        src="/logo-stucchi-white.png"
                        alt="Stucchi"
                        width={110}
                        height={58}
                        style={{ objectFit: 'contain' }}
                    />
                    <div style={{ width: 1, height: 32, background: '#2a2a2a' }} />
                    <div>
                        <div style={{ color: '#FFFFFF', fontWeight: 600, fontSize: '0.9rem' }}>
                            Pallet Optimizer
                        </div>
                        <div style={{ color: '#555555', fontSize: '0.72rem' }}>
                            {result.metadati.nome_cliente} &mdash; Ordine {result.metadati.numero_ordine}
                        </div>
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
                                boxShadow: '0 4px 14px rgba(232,122,60,0.35)',
                                display: 'flex', alignItems: 'center', gap: 6,
                            }}
                        >
                            Scarica PDF
                        </a>
                    )}
                    <button
                        onClick={() => router.push('/')}
                        style={{
                            padding: '0.6rem 1rem', background: '#141414',
                            color: '#CCCCCC', border: '1px solid #2a2a2a',
                            borderRadius: 10, cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
                        }}
                    >
                        &larr; Nuovo Ordine
                    </button>
                </div>
            </div>

            {/* Content */}
            <div style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem' }}>

                {/* Stats overview */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
                    {[
                        { label: 'Pallet Totali', value: result.n_pallet, color: '#1A3C6E' },
                        { label: 'Scatole Totali', value: result.riepilogo_boxing.n_scatole_totali, color: '#1A3C6E' },
                        { label: 'Scatole Piene', value: result.riepilogo_boxing.n_scatole_piene, color: '#16A34A' },
                        { label: 'Scatole Parziali', value: result.riepilogo_boxing.n_scatole_parziali, color: '#D97706' },
                    ].map(s => (
                        <div key={s.label} style={{
                            background: '#FFFFFF', borderRadius: 14, padding: '1.25rem',
                            border: '1px solid #E2E8F0',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.06)', textAlign: 'center',
                        }}>
                            <div style={{ fontSize: '2rem', fontWeight: 800, color: s.color }}>{s.value}</div>
                            <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: 2 }}>{s.label}</div>
                        </div>
                    ))}
                </div>

                {/* Warnings */}
                {hasWarnings && (
                    <div style={{
                        background: 'rgba(217,119,6,0.08)', border: '1px solid rgba(217,119,6,0.25)', borderRadius: 12,
                        padding: '1rem 1.5rem', marginBottom: '1.5rem',
                    }}>
                        <h3 style={{ color: '#D97706', margin: '0 0 0.5rem', fontSize: '0.9rem', fontWeight: 700 }}>
                            Prodotti non palletizzati
                        </h3>
                        {result.warnings.prodotti_non_trovati?.map(cod => (
                            <div key={cod} style={{ fontSize: '0.8rem', color: '#888888' }}>&bull; {cod} &mdash; non trovato nel DB prodotti</div>
                        ))}
                        {result.warnings.skippati_db?.map((item: any, i) => (
                            <div key={i} style={{ fontSize: '0.8rem', color: '#888888' }}>
                                &bull; {typeof item === 'object' ? `${item.cod} \u2014 ${item.motivo}` : item}
                            </div>
                        ))}
                    </div>
                )}

                {/* Grid pallet */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem' }}>
                    {result.pallet_list.map((pallet) => {
                        const imgFilenames = result.img_filenames
                            .filter(f => f.includes(`pallet_${String(pallet.pallet_id).padStart(2, '0')}`))
                            .sort();
                        return (
                            <PalletCard key={pallet.pallet_id} pallet={pallet} imgFilenames={imgFilenames} />
                        );
                    })}
                </div>

                {/* Report testuale */}
                <details style={{
                    marginTop: '2rem', background: '#FFFFFF', borderRadius: 12,
                    border: '1px solid #E2E8F0', padding: '1rem 1.5rem',
                }}>
                    <summary style={{ cursor: 'pointer', fontWeight: 600, color: '#64748B', fontSize: '0.9rem' }}>
                        Report Testuale Completo
                    </summary>
                    <pre style={{
                        marginTop: '1rem', fontSize: '0.75rem', color: '#475569',
                        background: '#F8FAFC', padding: '1rem', borderRadius: 8,
                        overflow: 'auto', maxHeight: 400, lineHeight: 1.6,
                        border: '1px solid #E2E8F0',
                    }}>
                        {(result as any).report_testo}
                    </pre>
                </details>
            </div>
        </div>
    );
}
