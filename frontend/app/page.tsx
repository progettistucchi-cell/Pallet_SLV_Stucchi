'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

export default function HomePage() {
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) setFile(e.target.files[0]);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${apiUrl}/api/palletize`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Errore nel server');
      }

      sessionStorage.setItem('palletResult', JSON.stringify(data));
      router.push('/results');
    } catch (err: any) {
      setError(err.message || 'Errore sconosciuto');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#000000',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      fontFamily: 'Inter, sans-serif',
    }}>
      {/* Logo Stucchi */}
      <div style={{ marginBottom: '2.5rem', animation: 'fadeInUp 0.4s ease' }}>
        <Image
          src="/logo-stucchi-white.png"
          alt="Stucchi"
          width={220}
          height={116}
          style={{ objectFit: 'contain' }}
          priority
        />
      </div>

      {/* Titolo app */}
      <div style={{ textAlign: 'center', marginBottom: '2rem', animation: 'fadeInUp 0.5s ease' }}>
        <h1 style={{
          fontSize: '2rem', fontWeight: 700, color: '#FFFFFF',
          margin: 0, letterSpacing: '-0.5px',
        }}>Pallet Optimizer</h1>
        <p style={{ color: '#666666', fontSize: '0.95rem', marginTop: '0.4rem', fontWeight: 400 }}>
          Sistema di Ottimizzazione Palletizzazione
        </p>
      </div>

      {/* Card Upload */}
      <div style={{
        background: '#FFFFFF',
        borderRadius: 20, padding: '2.5rem',
        width: '100%', maxWidth: 540,
        border: '1px solid #E2E8F0',
        boxShadow: '0 32px 80px rgba(0,0,0,0.5)',
      }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#1A3C6E', marginTop: 0, marginBottom: '0.25rem' }}>
          Carica Ordine SAP
        </h2>
        <p style={{ color: '#64748B', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
          Carica il file .XLS esportato da SAP per avviare la palletizzazione automatica
        </p>

        {/* Drop zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onClick={() => document.getElementById('file-input')?.click()}
          style={{
            border: `2px dashed ${isDragging ? '#E87A3C' : file ? '#16A34A' : '#CBD5E1'}`,
            borderRadius: 14,
            padding: '2.5rem',
            textAlign: 'center',
            cursor: 'pointer',
            background: isDragging ? '#FFF7ED' : file ? '#F0FDF4' : '#F8FAFC',
            transition: 'all 0.2s ease',
            marginBottom: '1.5rem',
          }}
        >
          <div style={{ fontSize: 40, marginBottom: '0.75rem' }}>
            {file ? '\u2705' : '\uD83D\uDCC2'}
          </div>
          {file ? (
            <>
              <p style={{ fontWeight: 600, color: '#16A34A', margin: 0, fontSize: '1rem' }}>
                {file.name}
              </p>
              <p style={{ color: '#64748B', margin: '0.25rem 0 0', fontSize: '0.8rem' }}>
                {(file.size / 1024).toFixed(1)} KB &mdash; Clicca per cambiare
              </p>
            </>
          ) : (
            <>
              <p style={{ fontWeight: 600, color: '#1E293B', margin: 0 }}>
                Trascina il file qui
              </p>
              <p style={{ color: '#94A3B8', margin: '0.25rem 0 0', fontSize: '0.8rem' }}>
                oppure clicca per selezionare &mdash; .XLS, .XLSX
              </p>
            </>
          )}
          <input
            id="file-input"
            type="file"
            accept=".xls,.xlsx,.csv"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
        </div>

        {/* Errore */}
        {error && (
          <div style={{
            background: 'rgba(220,38,38,0.08)', border: '1px solid rgba(220,38,38,0.25)',
            borderRadius: 10, padding: '0.875rem 1rem',
            color: '#DC2626', fontSize: '0.875rem', marginBottom: '1rem',
          }}>
            {error}
          </div>
        )}

        {/* CTA */}
        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          style={{
            width: '100%', padding: '1rem',
            background: file && !loading
              ? 'linear-gradient(135deg, #E87A3C, #F59E0B)'
              : '#E2E8F0',
            color: file && !loading ? '#FFFFFF' : '#94A3B8',
            border: 'none', borderRadius: 12,
            fontSize: '1rem', fontWeight: 700,
            cursor: file && !loading ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s ease',
            boxShadow: file && !loading ? '0 4px 20px rgba(232,122,60,0.35)' : 'none',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}
        >
          {loading ? (
            <>
              <span style={{
                width: 18, height: 18, border: '2px solid #FFFFFF',
                borderTop: '2px solid transparent', borderRadius: '50%',
                display: 'inline-block', animation: 'spin 0.8s linear infinite',
              }} />
              Elaborazione in corso...
            </>
          ) : (
            'Avvia Palletizzazione'
          )}
        </button>

        {/* Info pallet */}
        <div style={{
          display: 'flex', gap: '1rem', marginTop: '1.5rem',
          padding: '1rem', background: '#F8FAFC',
          borderRadius: 10, border: '1px solid #E2E8F0',
        }}>
          {[
            { label: 'Euro Pallet', value: '80\u00D7120 cm' },
            { label: 'Altezza Max', value: '160 cm' },
            { label: 'Rotazione', value: 'Ammessa' },
          ].map((item) => (
            <div key={item.label} style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: '0.7rem', color: '#94A3B8', fontWeight: 500, marginBottom: 2 }}>{item.label}</div>
              <div style={{ fontSize: '0.85rem', color: '#1A3C6E', fontWeight: 700 }}>{item.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* History link */}
      <a href="/history" style={{
        marginTop: '2rem', color: '#444444',
        textDecoration: 'none', fontSize: '0.875rem',
        transition: 'color 0.2s',
      }}
        onMouseEnter={(e) => (e.currentTarget.style.color = '#FFFFFF')}
        onMouseLeave={(e) => (e.currentTarget.style.color = '#444444')}
      >
        Storico palletizzazioni &rarr;
      </a>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeInUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
      `}</style>
    </div>
  );
}
