"""
parse_sap_order.py
Livello 3 — Esecuzione

Legge un file .XLS esportato da SAP (formato UTF-16 TSV).
Estrae i prodotti con le relative quantità ordinate.

Input:  path al file .XLS SAP
Output: dict con metadati ordine + lista prodotti [{cod_prodotto, qta, ...}]
"""

import os
import re
import argparse
import json
from typing import Optional


# Indici colonne nel file SAP UTF-16 TSV (0-based)
COL_CLIENTE = 0
COL_NOME = 1
COL_DT_ORDACQ = 2
COL_COD_MATERIALE_CLIENTE = 7   # Codice prodotto (coincide con DB SLV)
COL_QTA_ORD = 9                 # Quantità ordinata


def _parse_qta(val: str) -> int:
    """Converte una stringa quantità SAP (es. '1.200' o '120') in intero."""
    if not val or not val.strip():
        return 0
    # Rimuove separatori migliaia (punto o virgola) e spazi
    cleaned = re.sub(r'[\s.]', '', val.strip())
    cleaned = cleaned.replace(',', '.')
    try:
        return int(float(cleaned))
    except ValueError:
        return 0


def parse_sap_order(file_path: str) -> dict:
    """
    Legge il file ordine SAP e restituisce un dizionario strutturato.

    Args:
        file_path: percorso al file .XLS (UTF-16 TSV)

    Returns:
        {
            "cliente": str,
            "nome_cliente": str,
            "data_ordine": str,
            "numero_ordine": str,
            "prodotti": [
                {
                    "cod_prodotto": str,
                    "qta": int
                }, ...
            ],
            "prodotti_skippati": [str]   # codici senza quantità o vuoti
        }

    Raises:
        FileNotFoundError: se il file non esiste
        ValueError: se il file non contiene dati validi
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File SAP non trovato: {file_path}")

    # Tentativo 1: Lettura UTF-16 TSV (Formato SAP nativo finto Excel)
    rows = []
    try:
        with open(file_path, encoding='utf-16') as f:
            content = f.read()
            
        if not content.strip():
            raise ValueError("File vuoto")
            
        for line in content.strip().split('\n'):
            rows.append(line.split('\t'))
            
    except (UnicodeError, ValueError):
        # Tentativo 2: Lettura vero file Excel Binario (.xlsx)
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active
            for row in sheet.iter_rows(values_only=True):
                rows.append([str(c).strip() if c is not None else "" for c in row])
        except Exception as e:
            raise ValueError(f"Formato file non riconosciuto. Non è né un TSV UTF-16 né un vero Excel .xlsx: {str(e)}")

    if len(rows) < 2:
        raise ValueError("File SAP vuoto o non valido.")

    # Mappatura dinamica delle colonne
    header = [str(x).strip().lower() for x in rows[0]]
    
    # Indici di default fallback (per file senza header corretti)
    col_cliente = COL_CLIENTE
    col_nome = COL_NOME
    col_dt = COL_DT_ORDACQ
    col_mat = COL_COD_MATERIALE_CLIENTE
    col_qta = COL_QTA_ORD

    for i, h in enumerate(header):
        if h == "cliente" or "codice cliente" in h:
            col_cliente = i
        elif h == "nome 1" or h == "nome cliente" or h == "nome":
            col_nome = i
        elif "data" in h and "ordine" in h:
            col_dt = i
        elif h == "materiale" or "cod. materiale" in h or "codice materiale" in h:
            col_mat = i
        elif "qta" in h or "qtà" in h or "quantità" in h or "q.tà" in h:
            col_qta = i

    # Variabili da estrarre al volo
    cliente = ""
    nome_cliente = ""
    data_ordine = ""
    numero_ordine = ""
    prodotti = []
    prodotti_skippati = []

    # Indice max necessario per il padding
    max_idx = max(col_cliente, col_nome, col_dt, col_mat, col_qta)

    for cols in rows[1:]:
        # Pad colonne mancanti
        while len(cols) <= max_idx:
            cols.append('')

        col_cliente_val = cols[col_cliente].strip()

        # Skip righe aggregate (es. "*" = totale di gruppo)
        if col_cliente_val.startswith('*'):
            continue

        # Recupera metadati cliente dalla prima riga dati
        if not cliente and col_cliente_val and not col_cliente_val.startswith('*'):
            cliente = col_cliente_val
            nome_cliente = cols[col_nome].strip()
            data_ordine = cols[col_dt].strip()

        cod_prodotto = cols[col_mat].strip()
        qta_str = cols[col_qta].strip()

        # Skip righe senza codice prodotto
        if not cod_prodotto:
            # Controlla se è la riga con numero ordine (col [6] = Materiale nel vecchio layout, cerchiamo doc. vendita o consegna)
            for i, h in enumerate(header):
                if h == "doc. vendita" and cols[i].strip():
                    numero_ordine = cols[i].strip()
            continue

        # Skip righe con codice che inizia per "*" (subtotali)
        if cod_prodotto.startswith('*'):
            continue

        qta = _parse_qta(qta_str)

        if qta <= 0:
            prodotti_skippati.append(cod_prodotto)
            continue

        prodotti.append({
            "cod_prodotto": cod_prodotto,
            "qta": qta
        })

    if not prodotti:
        raise ValueError(
            "Nessun prodotto valido trovato nel file SAP. "
            f"Prodotti skippati: {prodotti_skippati}"
        )

    return {
        "cliente": cliente,
        "nome_cliente": nome_cliente,
        "data_ordine": data_ordine,
        "numero_ordine": numero_ordine,
        "prodotti": prodotti,
        "prodotti_skippati": prodotti_skippati
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parser file ordine SAP")
    parser.add_argument("--file", required=True, help="Percorso al file .XLS SAP")
    args = parser.parse_args()

    result = parse_sap_order(args.file)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n✅ Trovati {len(result['prodotti'])} prodotti")
    if result['prodotti_skippati']:
        print(f"⚠️  Skippati (qta=0 o vuoti): {result['prodotti_skippati']}")
