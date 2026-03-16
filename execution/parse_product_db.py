"""
parse_product_db.py
Livello 3 — Esecuzione

Legge il database prodotti/scatole da Supabase (o fallback XLSX locale).
Esegue il join con la lista prodotti dell'ordine SAP.

Input:  lista prodotti [{cod_prodotto, qta}]
Output: lista prodotti arricchita con info scatola
"""

import os
import re
import json
import argparse
from typing import Optional


# Path fallback al file XLSX locale
XLSX_FALLBACK_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'SLV qtà scatola.xlsx'
)

PALLET_BASE_L = 800   # mm
PALLET_BASE_P = 1200  # mm


def _parse_dimensioni(dim_str: str) -> Optional[tuple]:
    """
    Parsa la stringa dimensioni scatola (es. '500X390X290') in (l, p, a) in mm.
    Ritorna None se non parsabile.
    """
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
        return (l, p, a)
    except ValueError:
        return None


def load_product_db_from_xlsx(xlsx_path: str = None) -> dict:
    """
    Carica il DB prodotti dal file XLSX locale.
    Ritorna un dict {cod_prodotto: {qta_massima, codice_scatola, l_mm, p_mm, a_mm}}
    """
    import openpyxl
    path = xlsx_path or XLSX_FALLBACK_PATH
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File DB prodotti non trovato: {path}")

    wb = openpyxl.load_workbook(path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    db = {}
    skippati = []

    for row in rows[1:]:  # Skip header
        if not row or all(v is None for v in row):
            continue

        cod = str(row[0]).strip() if row[0] is not None else ''
        qta_max_raw = row[1]
        scatola = str(row[2]).strip() if row[2] is not None else ''
        dim_str = str(row[3]).strip() if row[3] is not None else ''

        if not cod:
            continue

        # Gestione "dato mancante"
        if 'mancante' in scatola.lower() or 'mancante' in dim_str.lower():
            skippati.append({'cod': cod, 'motivo': 'dato mancante nel DB'})
            continue

        # Parse quantità massima
        try:
            qta_max = int(float(str(qta_max_raw))) if qta_max_raw else 0
        except (ValueError, TypeError):
            qta_max = 0

        if qta_max <= 0:
            skippati.append({'cod': cod, 'motivo': f'qta_massima non valida: {qta_max_raw}'})
            continue

        # Parse dimensioni
        dims = _parse_dimensioni(dim_str)
        if dims is None:
            skippati.append({'cod': cod, 'motivo': f'dimensioni non parsabili: {dim_str}'})
            continue

        l_mm, p_mm, a_mm = dims

        # Avviso se la scatola supera la base pallet
        if l_mm > PALLET_BASE_L and p_mm > PALLET_BASE_P:
            skippati.append({
                'cod': cod,
                'motivo': f'scatola ({l_mm}x{p_mm}) supera base pallet ({PALLET_BASE_L}x{PALLET_BASE_P})'
            })
            continue

        db[cod] = {
            'qta_massima': qta_max,
            'codice_scatola': scatola,
            'l_mm': l_mm,
            'p_mm': p_mm,
            'a_mm': a_mm
        }

    return {'db': db, 'skippati_db': skippati}


def load_product_db_from_supabase() -> dict:
    """
    Carica il DB prodotti da Supabase.
    Ritorna un dict {cod_prodotto: {...}}
    """
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL o SUPABASE_KEY non configurati in .env")

        client = create_client(url, key)
        response = client.table("product_boxes").select("*").execute()
        rows = response.data

        db = {}
        skippati = []
        for row in rows:
            cod = str(row.get('codice_prodotto', '')).strip()
            if not cod:
                continue
            qta_max = row.get('qta_massima', 0)
            l_mm = row.get('l_mm', 0)
            p_mm = row.get('p_mm', 0)
            a_mm = row.get('a_mm', 0)
            scatola = row.get('codice_scatola', '')

            if not all([qta_max, l_mm, p_mm, a_mm]):
                skippati.append({'cod': cod, 'motivo': 'dati incompleti in Supabase'})
                continue

            db[cod] = {
                'qta_massima': int(qta_max),
                'codice_scatola': scatola,
                'l_mm': int(l_mm),
                'p_mm': int(p_mm),
                'a_mm': int(a_mm)
            }

        return {'db': db, 'skippati_db': skippati}

    except ImportError:
        raise ImportError("Libreria 'supabase' non installata. Usa: pip install supabase")


def join_order_with_db(prodotti_ordine: list, db: dict) -> dict:
    """
    Esegue il join tra lista prodotti ordine e DB prodotti.

    Args:
        prodotti_ordine: [{cod_prodotto, qta}]
        db: {cod_prodotto: {qta_massima, codice_scatola, l_mm, p_mm, a_mm}}

    Returns:
        {
            "prodotti_ok": [{cod_prodotto, qta, qta_massima, codice_scatola, l_mm, p_mm, a_mm}],
            "prodotti_non_trovati": [str]
        }
    """
    prodotti_ok = []
    non_trovati = []

    for p in prodotti_ordine:
        cod = p['cod_prodotto']
        info = db.get(cod)

        if info is None:
            non_trovati.append(cod)
            continue

        prodotti_ok.append({
            'cod_prodotto': cod,
            'qta': p['qta'],
            'qta_massima': info['qta_massima'],
            'codice_scatola': info['codice_scatola'],
            'l_mm': info['l_mm'],
            'p_mm': info['p_mm'],
            'a_mm': info['a_mm']
        })

    return {
        'prodotti_ok': prodotti_ok,
        'prodotti_non_trovati': non_trovati
    }


def load_and_join(prodotti_ordine: list, use_supabase: bool = False,
                  xlsx_path: str = None) -> dict:
    """
    Entry point principale: carica DB e fa il join con l'ordine.
    Tenta Supabase se configurato, altrimenti usa XLSX.
    """
    db_result = None

    if use_supabase:
        try:
            db_result = load_product_db_from_supabase()
            print("OK DB caricato da Supabase")
        except Exception as e:
            print(f"WARN Supabase non disponibile ({e}), uso fallback XLSX")
            db_result = load_product_db_from_xlsx(xlsx_path)
    else:
        db_result = load_product_db_from_xlsx(xlsx_path)
        print(f"OK DB caricato da XLSX ({len(db_result['db'])} prodotti)")

    join_result = join_order_with_db(prodotti_ordine, db_result['db'])

    return {
        **join_result,
        'skippati_db': db_result.get('skippati_db', [])
    }


if __name__ == "__main__":
    # Test rapido con dati di esempio
    test_prodotti = [
        {"cod_prodotto": "4551120610003", "qta": 500},
        {"cod_prodotto": "990951SLV0003", "qta": 25},
        {"cod_prodotto": "CODICE_INESISTENTE", "qta": 10},
    ]
    result = load_and_join(test_prodotti, use_supabase=False)
    print(json.dumps(result, indent=2, ensure_ascii=False))
