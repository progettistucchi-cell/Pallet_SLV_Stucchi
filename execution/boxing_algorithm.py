"""
boxing_algorithm.py
Livello 3 — Esecuzione

Calcola quante scatole servono per ogni prodotto dell'ordine.
Regole:
 - MAI mischiare prodotti diversi nella stessa scatola
 - Saturare al massimo la capacità (scatole piene + eventuale scatola parziale)
 - Output: lista di Box pronte per la palletizzazione

Input:  lista prodotti con info scatola [{cod_prodotto, qta, qta_massima, ...}]
Output: lista scatole [{id, cod_prodotto, codice_scatola, l_mm, p_mm, a_mm,
                        n_pezzi, is_piena, volume_mm3}]
"""

import json
import argparse
from typing import List, Dict


def calcola_boxing(prodotti: List[Dict]) -> Dict:
    """
    Calcola il boxing per ogni prodotto dell'ordine.

    Args:
        prodotti: lista da parse_product_db.join_order_with_db
                  [{cod_prodotto, qta, qta_massima, codice_scatola,
                    l_mm, p_mm, a_mm}]

    Returns:
        {
            "scatole": [
                {
                    "id": int,                  # ID progressivo scatola
                    "cod_prodotto": str,
                    "codice_scatola": str,
                    "l_mm": int,
                    "p_mm": int,
                    "a_mm": int,
                    "n_pezzi": int,             # pezzi contenuti
                    "capacita_max": int,        # pezzi max per scatola
                    "is_piena": bool,           # True se al 100%
                    "fill_ratio": float,        # n_pezzi / capacita_max
                    "volume_mm3": int           # L×P×A
                }, ...
            ],
            "riepilogo": {
                "n_scatole_totali": int,
                "n_scatole_piene": int,
                "n_scatole_parziali": int,
                "per_prodotto": [{...}]
            }
        }
    """
    scatole = []
    box_id = 1
    riepilogo_per_prodotto = []

    for p in prodotti:
        cod = p['cod_prodotto']
        qta = p['qta']
        qta_max = p['qta_massima']
        codice_scatola = p['codice_scatola']
        l, pp, a = p['l_mm'], p['p_mm'], p['a_mm']
        volume = l * pp * a

        if qta <= 0:
            continue

        n_piene = qta // qta_max
        resto = qta % qta_max

        scatole_prodotto_piene = 0
        scatole_prodotto_parziali = 0

        # Scatole piene
        for _ in range(n_piene):
            scatole.append({
                "id": box_id,
                "cod_prodotto": cod,
                "codice_scatola": codice_scatola,
                "l_mm": l,
                "p_mm": pp,
                "a_mm": a,
                "n_pezzi": qta_max,
                "capacita_max": qta_max,
                "is_piena": True,
                "fill_ratio": 1.0,
                "volume_mm3": volume
            })
            box_id += 1
            scatole_prodotto_piene += 1

        # Scatola parziale (se c'è resto)
        if resto > 0:
            fill = round(resto / qta_max, 4)
            scatole.append({
                "id": box_id,
                "cod_prodotto": cod,
                "codice_scatola": codice_scatola,
                "l_mm": l,
                "p_mm": pp,
                "a_mm": a,
                "n_pezzi": resto,
                "capacita_max": qta_max,
                "is_piena": False,
                "fill_ratio": fill,
                "volume_mm3": volume
            })
            box_id += 1
            scatole_prodotto_parziali += 1

        riepilogo_per_prodotto.append({
            "cod_prodotto": cod,
            "codice_scatola": codice_scatola,
            "qta_totale": qta,
            "capacita_scatola": qta_max,
            "n_scatole_piene": scatole_prodotto_piene,
            "n_scatole_parziali": scatole_prodotto_parziali,
            "n_scatole_totali": scatole_prodotto_piene + scatole_prodotto_parziali
        })

    n_piene_tot = sum(1 for s in scatole if s['is_piena'])
    n_parziali_tot = sum(1 for s in scatole if not s['is_piena'])

    return {
        "scatole": scatole,
        "riepilogo": {
            "n_scatole_totali": len(scatole),
            "n_scatole_piene": n_piene_tot,
            "n_scatole_parziali": n_parziali_tot,
            "per_prodotto": riepilogo_per_prodotto
        }
    }


if __name__ == "__main__":
    # Test con dati di esempio
    test_prodotti = [
        {
            "cod_prodotto": "4551120610003",
            "qta": 500,
            "qta_massima": 220,
            "codice_scatola": "VP8017/0",
            "l_mm": 500, "p_mm": 390, "a_mm": 290
        },
        {
            "cod_prodotto": "990951SLV0003",
            "qta": 25,
            "qta_massima": 10,
            "codice_scatola": "VP4129/0",
            "l_mm": 340, "p_mm": 195, "a_mm": 135
        },
        {
            "cod_prodotto": "999051SLV0003",
            "qta": 50,
            "qta_massima": 50,
            "codice_scatola": "VP4256/0",
            "l_mm": 800, "p_mm": 400, "a_mm": 400
        },
    ]

    result = calcola_boxing(test_prodotti)
    print(json.dumps(result['riepilogo'], indent=2, ensure_ascii=False))
    print(f"\n✅ Totale scatole: {result['riepilogo']['n_scatole_totali']}")
    print(f"   Piene: {result['riepilogo']['n_scatole_piene']}")
    print(f"   Parziali: {result['riepilogo']['n_scatole_parziali']}")
    print("\nPrime 5 scatole:")
    for s in result['scatole'][:5]:
        stato = "PIENA" if s['is_piena'] else f"PARZIALE ({s['fill_ratio']*100:.0f}%)"
        print(f"  [{s['id']}] {s['cod_prodotto']} | {s['codice_scatola']} | "
              f"{s['l_mm']}x{s['p_mm']}x{s['a_mm']}mm | {s['n_pezzi']}pz | {stato}")
