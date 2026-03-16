'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface HistoryItem {
    id: number;
    created_at: string;
    cliente: string;
    nome_cliente: string;
    numero_ordine: string;
    data_ordine: string;
    n_pallet: number;
    n_scatole: number;
}

export default function HistoryPage() {
    const router = useRouter();
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [configured, setConfigured] = useState(true);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/history')
            .then(r => r.json())
            .then(data => {
                setConfigured(data.configured);
                setHistory(data.history || []);
            })
            .catch(() => setConfigured(false))
            .finally(() => setLoading(false));
    }, []);

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0F2447 0%, #1A3C6E 40%, #F0F4FA 40%)',
            fontFamily: 'Inter, sans-serif',
        }}>
            {/* Header */}
            <div style={{ padding: '2rem', maxWidth: 900, margin: '0 auto' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                    <button onClick={() => router.push('/')} style={{
                        background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.25)',
                        color: '#FFFFFF', borderRadius: 8, padding: '0.5rem 1rem', cursor: 'pointer',
                        fontWeight: 600, fontSize: '0.85rem',
                    }}>← Indietro</button>
                    <h1 style={{ color: '#FFFFFF', margin: 0, fontSize: '1.5rem', fontWeight: 800 }}>
                        📋 Storico Palletizzazioni
                    </h1>
                </div>

                <div style={{ background: '#FFFFFF', borderRadius: 16, boxShadow: '0 8px 32px rgba(26,60,110,0.12)', overflow: 'hidden' }}>
                    {loading ? (
                        <div style={{ padding: '3rem', textAlign: 'center', color: '#94A3B8' }}>
                            Caricamento...
                        </div>
                    ) : !configured ? (
                        <div style={{ padding: '3rem', textAlign: 'center' }}>
                            <div style={{ fontSize: 48, marginBottom: '1rem' }}>🔌</div>
                            <h3 style={{ color: '#1A3C6E', marginBottom: '0.5rem' }}>Supabase non configurato</h3>
                            <p style={{ color: '#64748B', fontSize: '0.875rem' }}>
                                Lo storico è disponibile dopo aver configurato Supabase in <code>backend/.env</code>
                            </p>
                        </div>
                    ) : history.length === 0 ? (
                        <div style={{ padding: '3rem', textAlign: 'center' }}>
                            <div style={{ fontSize: 48, marginBottom: '1rem' }}>📭</div>
                            <p style={{ color: '#64748B' }}>Nessuna palletizzazione registrata</p>
                        </div>
                    ) : (
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#F8FAFC' }}>
                                    {['Data', 'Cliente', 'Ordine', 'N. Pallet', 'N. Scatole'].map(h => (
                                        <th key={h} style={{
                                            padding: '0.875rem 1.25rem', textAlign: 'left',
                                            fontSize: '0.75rem', fontWeight: 700, color: '#64748B',
                                            textTransform: 'uppercase', letterSpacing: '0.05em',
                                            borderBottom: '1px solid #E2E8F0',
                                        }}>{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {history.map((item, i) => (
                                    <tr key={item.id} style={{
                                        borderBottom: '1px solid #F1F5F9',
                                        background: i % 2 === 0 ? '#FFFFFF' : '#FAFAFA',
                                    }}>
                                        <td style={{ padding: '0.875rem 1.25rem', fontSize: '0.8rem', color: '#475569' }}>
                                            {new Date(item.created_at).toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                        </td>
                                        <td style={{ padding: '0.875rem 1.25rem', fontSize: '0.85rem', fontWeight: 600, color: '#1E293B' }}>
                                            {item.nome_cliente || item.cliente}
                                        </td>
                                        <td style={{ padding: '0.875rem 1.25rem', fontSize: '0.8rem', color: '#64748B', fontFamily: 'monospace' }}>
                                            {item.numero_ordine}
                                        </td>
                                        <td style={{ padding: '0.875rem 1.25rem' }}>
                                            <span style={{
                                                background: '#EFF6FF', color: '#1D4ED8',
                                                padding: '0.25rem 0.625rem', borderRadius: 6,
                                                fontWeight: 700, fontSize: '0.85rem',
                                            }}>
                                                {item.n_pallet}
                                            </span>
                                        </td>
                                        <td style={{ padding: '0.875rem 1.25rem', fontSize: '0.85rem', color: '#1A3C6E', fontWeight: 600 }}>
                                            {item.n_scatole}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}
