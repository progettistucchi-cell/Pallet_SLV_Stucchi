-- ============================================================
-- SQL da eseguire su Supabase SQL Editor
-- https://supabase.com/dashboard/project/rlfguzlhkbyqnhzeoxsh/sql/new
-- ============================================================

-- Tabella prodotti/scatole SLV
CREATE TABLE IF NOT EXISTS product_boxes (
  id SERIAL PRIMARY KEY,
  codice_prodotto TEXT UNIQUE NOT NULL,
  qta_massima INTEGER NOT NULL,
  codice_scatola TEXT NOT NULL,
  l_mm INTEGER NOT NULL,
  p_mm INTEGER NOT NULL,
  a_mm INTEGER NOT NULL
);

-- Storico palletizzazioni
CREATE TABLE IF NOT EXISTS pallet_history (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  cliente TEXT,
  nome_cliente TEXT,
  numero_ordine TEXT,
  data_ordine TEXT,
  n_pallet INTEGER,
  n_scatole INTEGER,
  result_json JSONB,
  warnings_json JSONB
);
