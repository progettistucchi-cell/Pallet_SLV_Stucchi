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

    # Lettura UTF-16 con BOM
    with open(file_path, encoding='utf-16') as f:
        content = f.read()

    lines = content.strip().split('\n')
    if len(lines) < 2:
        raise ValueError("File SAP vuoto o non valido.")

    # Prima riga = header → skip
    header = lines[0].split('\t')

    # Variabili da estrarre al volo
    cliente = ""
    nome_cliente = ""
    data_ordine = ""
    numero_ordine = ""
    prodotti = []
    prodotti_skippati = []

    for line in lines[1:]:
        cols = line.split('\t')

        # Pad colonne mancanti
        while len(cols) <= max(COL_CLIENTE, COL_NOME, COL_DT_ORDACQ,
                               COL_COD_MATERIALE_CLIENTE, COL_QTA_ORD):
            cols.append('')

        col_cliente_val = cols[COL_CLIENTE].strip()

        # Skip righe aggregate (es. "*" = totale di gruppo)
        if col_cliente_val.startswith('*'):
            continue

        # Recupera metadati cliente dalla prima riga dati
        if not cliente and col_cliente_val and not col_cliente_val.startswith('*'):
            cliente = col_cliente_val
            nome_cliente = cols[COL_NOME].strip()
            data_ordine = cols[COL_DT_ORDACQ].strip()

        cod_prodotto = cols[COL_COD_MATERIALE_CLIENTE].strip()
        qta_str = cols[COL_QTA_ORD].strip()

        # Skip righe senza codice prodotto
        if not cod_prodotto:
            # Controlla se è la riga con numero ordine (col [6] = Materiale)
            if len(cols) > 6 and cols[6].strip() and not cols[6].strip().startswith('*'):
                numero_ordine = cols[6].strip()
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
