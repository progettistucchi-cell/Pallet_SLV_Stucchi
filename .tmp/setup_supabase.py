"""
Crea le tabelle Supabase e migra i prodotti da XLSX.
Usa l'API REST di Supabase per eseguire SQL tramite la funzione pg_execute.
"""
import os, sys, json, requests

sys.path.insert(0, r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\backend')
from dotenv import load_dotenv
load_dotenv(r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\backend\.env')

URL = os.environ['SUPABASE_URL']
KEY = os.environ['SUPABASE_KEY']
HEADERS = {'apikey': KEY, 'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json', 'Prefer': 'return=representation'}

def sql_via_rest(sql: str) -> dict:
    """Esegue SQL tramite l'endpoint /rest/v1/rpc/exec oppure diretto."""
    # Supabase supporta POST su /rest/v1/ con header specifici per la maggior parte delle operazioni
    # Ma per DDL (CREATE TABLE) usiamo l'endpoint management API non disponibile con anon key.
    # Alternativa: usiamo psycopg2 con la connection string Supabase.
    pass

# ─── Approccio diretto: usa supabase-py per fare i controlli ─────────────────
from supabase import create_client
client = create_client(URL, KEY)

# ─── Test se le tabelle esistono già ─────────────────────────────────────────
def table_exists(name: str) -> bool:
    try:
        client.table(name).select('id').limit(1).execute()
        return True
    except Exception as e:
        return 'does not exist' not in str(e).lower() and '42P01' not in str(e)

print("Verifico tabelle...")
pb_exists = table_exists('product_boxes')
ph_exists = table_exists('pallet_history')
print(f"  product_boxes: {'✅ esiste' if pb_exists else '❌ mancante'}")
print(f"  pallet_history: {'✅ esiste' if ph_exists else '❌ mancante'}")

if not pb_exists or not ph_exists:
    print("\n⚠️  Le tabelle devono essere create manualmente su Supabase.")
    print("   Vai su: https://supabase.com/dashboard/project/rlfguzlhkbyqnhzeoxsh/sql/new")
    print("   Ed esegui il seguente SQL:\n")
    sql_create = """
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
"""
    print(sql_create)
    with open(r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\.tmp\create_tables.sql', 'w') as f:
        f.write(sql_create)
    print("SQL salvato anche in: .tmp\\create_tables.sql")
    print("\nDopo aver creato le tabelle, riesegui questo script per migrare i prodotti.")
    sys.exit(0)

# ─── Migrazione prodotti ──────────────────────────────────────────────────────
print("\nTabelle OK. Migrazione prodotti da XLSX...")
sys.path.insert(0, r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\execution')
from migrate_db_to_supabase import load_xlsx_products

XLSX = None
import os as _os
base = r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi'
for f in _os.listdir(base):
    if 'SLV' in f and f.endswith('.xlsx'):
        XLSX = _os.path.join(base, f)
        break

prodotti, skippati = load_xlsx_products(XLSX)
print(f"  Prodotti validi: {len(prodotti)} | Skippati: {len(skippati)}")

# Upsert
ok = 0
errors = []
for i in range(0, len(prodotti), 50):
    chunk = prodotti[i:i+50]
    try:
        client.table('product_boxes').upsert(chunk, on_conflict='codice_prodotto').execute()
        ok += len(chunk)
        print(f"  ✅ Batch {i//50+1}: {len(chunk)} prodotti")
    except Exception as e:
        errors.append(str(e))
        print(f"  ❌ Errore batch {i//50+1}: {e}")

print(f"\n✅ Migrazione completata: {ok} prodotti su Supabase")
if skippati:
    print(f"⚠️  {len(skippati)} prodotti skippati (dati mancanti — aggiungili manualmente in Supabase):")
    for s in skippati:
        print(f"   • {s['cod']}: {s['motivo']}")
if errors:
    print("❌ Errori:", errors)
