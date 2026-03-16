"""
migrate_db_to_supabase.py
Livello 3 — Esecuzione

Importa il DB prodotti da 'SLV qtà scatola.xlsx' su Supabase (tabella product_boxes).
Da eseguire UNA SOLA VOLTA dopo aver configurato backend/.env con le credenziali Supabase.

Usage:
    python3 execution/migrate_db_to_supabase.py

Comportamento:
  - Legge il file XLSX nella root del progetto
  - Skippa prodotti con "dato mancante" o dimensioni non parsabili (li stampa come warning)
  - Per ogni prodotto valido: fa UPSERT su Supabase (non duplica se già esiste)
  - Stampa un riepilogo finale
"""

import os
import re
import sys

# Aggiunta path per .env backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _parse_dimensioni(dim_str: str):
    if not dim_str or 'mancante' in dim_str.lower() or 'sacc' in dim_str.lower():
        return None
    parts = re.split(r'[xX×]', dim_str.strip())
    parts = [re.sub(r'[^\d]', '', p) for p in parts]
    parts = [p for p in parts if p]
    if len(parts) != 3:
        return None
    try:
        l, p, a = int(parts[0]), int(parts[1]), int(parts[2])
        if l <= 0 or p <= 0 or a <= 0:
            return None
        return l, p, a
    except ValueError:
        return None


def load_xlsx_products(xlsx_path: str) -> tuple[list, list]:
    """Legge il file XLSX e ritorna (prodotti_validi, prodotti_skippati)."""
    import openpyxl
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    prodotti = []
    skippati = []

    for row in rows[1:]:
        if not row or all(v is None for v in row):
            continue
        cod = str(row[0]).strip() if row[0] is not None else ''
        qta_max_raw = row[1]
        scatola = str(row[2]).strip() if row[2] is not None else ''
        dim_str = str(row[3]).strip() if row[3] is not None else ''

        if not cod:
            continue

        if 'mancante' in scatola.lower() or 'mancante' in dim_str.lower():
            skippati.append({'cod': cod, 'motivo': 'dato mancante nel DB'})
            continue

        try:
            qta_max = int(float(str(qta_max_raw))) if qta_max_raw else 0
        except (ValueError, TypeError):
            qta_max = 0

        if qta_max <= 0:
            skippati.append({'cod': cod, 'motivo': f'qta_massima non valida: {qta_max_raw}'})
            continue

        dims = _parse_dimensioni(dim_str)
        if dims is None:
            skippati.append({'cod': cod, 'motivo': f'dimensioni non parsabili: {dim_str}'})
            continue

        l_mm, p_mm, a_mm = dims
        prodotti.append({
            'codice_prodotto': cod,
            'qta_massima': qta_max,
            'codice_scatola': scatola,
            'l_mm': l_mm,
            'p_mm': p_mm,
            'a_mm': a_mm
        })

    return prodotti, skippati


def migrate_to_supabase(prodotti: list) -> dict:
    """Fa UPSERT dei prodotti su Supabase. Ritorna {ok, errors}."""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, 'backend', '.env'))

    url = os.environ.get('SUPABASE_URL', '')
    key = os.environ.get('SUPABASE_KEY', '')

    if not url or not key or 'YOUR_PROJECT_ID' in url:
        raise ValueError(
            "❌ Credenziali Supabase mancanti in backend/.env\n"
            "   Aggiungi SUPABASE_URL e SUPABASE_KEY e riprova."
        )

    from supabase import create_client
    client = create_client(url, key)

    ok = 0
    errors = []

    # Batch upsert (chunk da 50 per sicurezza)
    chunk_size = 50
    for i in range(0, len(prodotti), chunk_size):
        chunk = prodotti[i:i + chunk_size]
        try:
            response = (client.table('product_boxes')
                        .upsert(chunk, on_conflict='codice_prodotto')
                        .execute())
            ok += len(chunk)
            print(f"  ✅ Batch {i // chunk_size + 1}: {len(chunk)} prodotti importati")
        except Exception as e:
            errors.append(str(e))
            print(f"  ❌ Batch {i // chunk_size + 1} errore: {e}")

    return {'ok': ok, 'errors': errors}


def main():
    print("=" * 60)
    print("  MIGRAZIONE DB PRODOTTI → SUPABASE")
    print("=" * 60)

    # Trova file XLSX
    xlsx_path = None
    for f in os.listdir(BASE_DIR):
        if 'SLV' in f and f.lower().endswith('.xlsx'):
            xlsx_path = os.path.join(BASE_DIR, f)
            break

    if not xlsx_path:
        print("❌ File 'SLV qtà scatola.xlsx' non trovato nella root del progetto")
        sys.exit(1)

    print(f"\n📂 File: {xlsx_path}")
    print("\n[1/2] Lettura prodotti dal file XLSX...")
    prodotti, skippati = load_xlsx_products(xlsx_path)
    print(f"  ✅ Prodotti validi: {len(prodotti)}")
    print(f"  ⚠️  Prodotti skippati: {len(skippati)}")

    if skippati:
        print("\n  Prodotti skippati:")
        for s in skippati:
            print(f"    • {s['cod']}: {s['motivo']}")

    print(f"\n[2/2] Migrazione su Supabase ({len(prodotti)} prodotti)...")
    try:
        result = migrate_to_supabase(prodotti)
        print(f"\n✅ Migrazione completata: {result['ok']} prodotti importati")
        if result['errors']:
            print(f"❌ Errori: {result['errors']}")
    except ValueError as e:
        print(f"\n{e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Ora puoi aggiungere i prodotti mancanti direttamente")
    print("  dalla Supabase Table Editor (tabella product_boxes)")
    print("=" * 60)


if __name__ == "__main__":
    main()
