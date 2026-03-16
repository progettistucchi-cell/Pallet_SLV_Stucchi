"""
run_pipeline.py
Livello 3 — Entry point

Esegue la pipeline completa di palletizzazione end-to-end:
  1. parse_sap_order     → legge file SAP
  2. parse_product_db    → join con DB prodotti (Supabase o XLSX)
  3. boxing_algorithm    → calcola scatole
  4. pallet_algorithm    → calcola pallet e layer
  5. generate_pallet_image → immagini 2D PNG
  6. generate_pdf        → PDF finale

Input:  path file SAP, path xlsx DB (opzionale), use_supabase flag
Output: dict con pallet_list, pdf_path, img_paths, warnings, report_testo
"""

import os
import sys
import json
import argparse
import traceback

# Fix encoding Windows: forza UTF-8 su stdout/stderr per evitare
# crash con emoji/caratteri Unicode su sistemi con encoding CP1252
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Aggiunge la directory execution al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parse_sap_order import parse_sap_order
from parse_product_db import load_and_join
from boxing_algorithm import calcola_boxing
from pallet_algorithm_3d import palletizza_3d, genera_report_testuale_3d
from generate_pallet_image_3d import genera_tutte_immagini_3d
from generate_pdf import genera_pdf


def run_pipeline(sap_file_path: str, xlsx_db_path: str = None, use_supabase: bool = True, output_dir: str = None) -> dict:
    """
    Pipeline completa di palletizzazione.

    Args:
        sap_file_path:  Path al file .XLS SAP (UTF-16 TSV)
        xlsx_db_path:   Path al file XLSX DB prodotti (fallback se no Supabase)
        use_supabase:   Se True, legge il DB da Supabase
        output_dir:     Cartella output per PDF e immagini (default: .tmp/)

    Returns:
        {
            "success": bool,
            "pallet_list": [...],
            "n_pallet": int,
            "report_testo": str,
            "pdf_path": str,
            "img_paths": [str],
            "warnings": {prodotti_non_trovati, skippati_db, prodotti_skippati_sap},
            "riepilogo_boxing": {...},
            "metadati": {...},
            "error": str | None
        }
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.tmp')
    output_dir = os.path.abspath(output_dir)
    img_dir = os.path.join(output_dir, 'images')

    # Resolve XLSX path se non specificato
    if xlsx_db_path is None:
        # Cerca il file SLV nella directory padre
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [f for f in os.listdir(base) if 'SLV' in f and f.endswith('.xlsx')]
        if candidates:
            xlsx_db_path = os.path.join(base, candidates[0])

    print("=" * 60)
    print("  PIPELINE PALLETIZZAZIONE SLV STUCCHI")
    print("=" * 60)

    # ─── Step 1: Parsing ordine SAP ────────────────────────────────
    print("\n[1/6] Parsing file ordine SAP...")
    try:
        ordine = parse_sap_order(sap_file_path)
        print(f"  OK Cliente: {ordine['nome_cliente']} | "
              f"Ordine: {ordine['numero_ordine']} | "
              f"Prodotti: {len(ordine['prodotti'])}")
    except Exception as e:
        return {"success": False, "error": f"Errore parsing SAP: {e}", "pallet_list": []}

    # ─── Step 2: Join con DB prodotti ──────────────────────────────
    print("\n[2/6] Caricamento DB prodotti e join con ordine...")
    try:
        join_result = load_and_join(
            ordine['prodotti'],
            use_supabase=use_supabase,
            xlsx_path=xlsx_db_path
        )
        prodotti_ok = join_result['prodotti_ok']
        non_trovati = join_result['prodotti_non_trovati']
        skippati_db = join_result.get('skippati_db', [])

        print(f"  OK Prodotti trovati nel DB: {len(prodotti_ok)}")
        if non_trovati:
            print(f"  WARN Non trovati nel DB: {non_trovati}")
        if skippati_db:
            print(f"  WARN Skippati DB (dati mancanti): {len(skippati_db)}")

        if not prodotti_ok:
            return {
                "success": False,
                "error": "Nessun prodotto dell'ordine trovato nel DB. Pipeline interrotta.",
                "pallet_list": []
            }
    except Exception as e:
        return {"success": False, "error": f"Errore caricamento DB: {e}", "pallet_list": []}

    # ─── Step 3: Boxing ────────────────────────────────────────────
    print("\n[3/6] Calcolo boxing...")
    try:
        boxing = calcola_boxing(prodotti_ok)
        scatole = boxing['scatole']
        rib = boxing['riepilogo']
        print(f"  OK Scatole totali: {rib['n_scatole_totali']} "
              f"(Piene: {rib['n_scatole_piene']}, Parziali: {rib['n_scatole_parziali']})")
    except Exception as e:
        return {"success": False, "error": f"Errore boxing: {e}", "pallet_list": []}

    # ─── Step 4: Palletizzazione 3D Z-Buffer ───────────────────────
    print("\n[4/6] Algoritmo 3D Z-Buffer...")
    try:
        pallet_list = palletizza_3d(scatole)
        report_testo = genera_report_testuale_3d(pallet_list)
        print(f"  OK Pallet necessari: {len(pallet_list)}")
    except Exception as e:
        return {"success": False, "error": f"Errore palletizzazione: {e}", "pallet_list": []}

    # ─── Step 5: Generazione immagini 3D Step-by-Step ─────────────
    print("\n[5/6] Generazione manuali 3D...")
    try:
        img_paths = genera_tutte_immagini_3d(pallet_list, output_dir=img_dir)
        print(f"  OK {len(img_paths)} immagini generate")
    except Exception as e:
        print(f"  WARN Errore generazione immagini: {e}")
        img_paths = []

    # ─── Step 6: Generazione PDF ──────────────────────────────────
    print("\n[6/6] Generazione PDF report...")
    warnings = {
        "prodotti_non_trovati": non_trovati,
        "skippati_db": skippati_db,
        "prodotti_skippati_sap": ordine.get('prodotti_skippati', [])
    }
    try:
        pdf_path = genera_pdf(
            metadati=ordine,
            pallet_list=pallet_list,
            img_paths=img_paths,
            warnings=warnings,
            output_dir=output_dir
        )
        print(f"  OK PDF: {pdf_path}")
    except Exception as e:
        print(f"  WARN Errore generazione PDF: {e}")
        traceback.print_exc()
        pdf_path = None

    print("\n" + "=" * 60)
    print(f"  COMPLETATO — {len(pallet_list)} pallet")
    print("=" * 60)
    if non_trovati:
        print(f"\nATTENZIONE: {len(non_trovati)} prodotti NON palletizzati: {non_trovati}")

    return {
        "success": True,
        "pallet_list": pallet_list,
        "n_pallet": len(pallet_list),
        "report_testo": report_testo,
        "pdf_path": pdf_path,
        "img_paths": img_paths,
        "warnings": warnings,
        "riepilogo_boxing": boxing['riepilogo'],
        "metadati": ordine,
        "error": None
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline palletizzazione SLV Stucchi"
    )
    parser.add_argument("--sap-file", required=True,
                        help="Percorso al file .XLS SAP (es: 1018628.XLS)")
    parser.add_argument("--db-xlsx", default=None,
                        help="Percorso al file XLSX DB prodotti (opzionale)")
    parser.add_argument("--supabase", action="store_true",
                        help="Usa Supabase come DB (richiede .env configurato)")
    parser.add_argument("--output-dir", default=None,
                        help="Cartella output per PDF e immagini")
    parser.add_argument("--json", action="store_true",
                        help="Stampa output come JSON")

    args = parser.parse_args()

    result = run_pipeline(
        sap_file_path=args.sap_file,
        xlsx_db_path=args.db_xlsx,
        use_supabase=args.supabase,
        output_dir=args.output_dir
    )

    if args.json:
        # Serializza rimuovendo pallet_list completo (troppo verboso)
        out = {k: v for k, v in result.items() if k != 'pallet_list'}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        if result.get('report_testo'):
            print("\n" + result['report_testo'])
