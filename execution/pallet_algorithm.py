"""
pallet_algorithm.py
Livello 3 — Esecuzione

Algoritmo di palletizzazione 3D layer-based.
Gestisce il posizionamento delle scatole su Euro pallet (800x1200mm, altezza max 1600mm).

Strategia:
  1. Scatole PIENE → layer inferiori (dal basso)
  2. Scatole PARZIALI → layer superiori
  3. Ogni layer usa rect bin packing 2D con rotazione 90° ammessa
  4. Altezza layer = altezza massima delle scatole nel layer
  5. Minimizza il numero di pallet (massimizza riempimento)

Input:  lista scatole da boxing_algorithm.calcola_boxing
Output: lista pallet [{id, layers, altezza_totale_mm, stats}]
"""

import json
from typing import List, Dict, Tuple, Optional
from copy import deepcopy


# ─── Costanti Pallet ────────────────────────────────────────────────────────
PALLET_L = 800    # mm lunghezza base
PALLET_P = 1200   # mm profondità base
PALLET_H = 1600   # mm altezza massima carico


# ─── Rect Bin Packing 2D (Guillotine / Shelf First Fit) ─────────────────────

class Shelf:
    """Un 'ripiano' orizzontale nel layer: una striscia rettangolare libera."""
    def __init__(self, y: int, width: int, depth: int):
        self.y = y            # offset dalla parte anteriore del pallet
        self.x_cursor = 0    # cursore in larghezza
        self.width = width   # larghezza disponibile (PALLET_L)
        self.depth = depth   # profondità già occupata dallo shelf
        self.boxes: List[Dict] = []

    def can_fit(self, bl: int, bp: int) -> bool:
        """Verifica se una scatola bl×bp entra nello shelf corrente."""
        return (self.x_cursor + bl <= self.width) and (bp <= self.depth)

    def place(self, box: Dict, bl: int, bp: int, rotated: bool) -> Dict:
        """Posiziona la scatola nello shelf e aggiorna il cursore."""
        placed = {
            **box,
            "pos_x_mm": self.x_cursor,
            "pos_y_mm": self.y,
            "placed_l_mm": bl,
            "placed_p_mm": bp,
            "rotated": rotated
        }
        self.boxes.append(placed)
        self.x_cursor += bl
        return placed


def pack_layer_2d(boxes_to_pack: List[Dict],
                  pallet_l: int = PALLET_L,
                  pallet_p: int = PALLET_P) -> Tuple[List[Dict], List[Dict]]:
    """
    Distribuisce scatole su un layer 800x1200mm usando Shelf First Fit.
    Prova entrambe le orientazioni (L×P e P×L) per ogni scatola.

    Returns:
        (placed: List[Dict], unplaced: List[Dict])
        placed include pos_x_mm, pos_y_mm, placed_l_mm, placed_p_mm, rotated
    """
    placed = []
    unplaced = []
    shelves: List[Shelf] = []
    y_cursor = 0  # profondità già occupata

    def try_orientations(box: Dict):
        """Ritorna (bl, bp, rotated) della migliore orientazione, o None."""
        l, p = box['l_mm'], box['p_mm']
        orientations = [(l, p, False)]
        if l != p:
            orientations.append((p, l, True))

        # Prova a mettere in uno shelf esistente
        for bl, bp, rot in orientations:
            for shelf in shelves:
                if shelf.can_fit(bl, bp):
                    return shelf, bl, bp, rot

        # Nessuno shelf adatto → apri nuovo shelf
        for bl, bp, rot in orientations:
            if bl <= pallet_l and bp <= (pallet_p - y_cursor):
                return None, bl, bp, rot  # None = nuovo shelf

        return None, None, None, None  # non entra

    for box in boxes_to_pack:
        shelf_target, bl, bp, rot = try_orientations(box)

        if bl is None:
            unplaced.append(box)
            continue

        if shelf_target is None:
            # Apri nuovo shelf
            new_shelf = Shelf(y=y_cursor, width=pallet_l, depth=bp)
            shelves.append(new_shelf)
            y_cursor += bp
            placed.append(new_shelf.place(box, bl, bp, rot))
        else:
            placed.append(shelf_target.place(box, bl, bp, rot))

    return placed, unplaced


def build_layer(boxes_subset: List[Dict]) -> Optional[Dict]:
    """
    Costruisce un singolo layer dal subset di scatole dato.
    Ritorna il layer con le scatole piazzate e quelle non piazzate.
    """
    if not boxes_subset:
        return None

    placed, unplaced = pack_layer_2d(boxes_subset)

    if not placed:
        return None

    altezza_layer = max(b['a_mm'] for b in placed)

    return {
        "placed": placed,
        "unplaced": unplaced,
        "altezza_mm": altezza_layer
    }


def palletizza(scatole: List[Dict]) -> List[Dict]:
    """
    Algoritmo principale di palletizzazione.

    Args:
        scatole: lista da boxing_algorithm (con is_piena, l_mm, p_mm, a_mm, ...)

    Returns:
        Lista di pallet:
        [{
            "pallet_id": int,
            "layers": [{
                "layer_n": int,
                "altezza_mm": int,
                "altezza_cumulativa_mm": int,
                "tipo": "PIENA" | "PARZIALE",
                "scatole": [{...pos_x, pos_y, placed_l, placed_p, rotated, ...}]
            }],
            "altezza_totale_mm": int,
            "n_scatole": int,
            "volume_usato_mm3": int,
            "volume_pallet_mm3": int,
            "fill_pct": float
        }]
    """
    if not scatole:
        return []

    # Separa piene e parziali; ordina per volume decrescente (grandi prima = meglio riempie)
    piene = sorted([s for s in scatole if s['is_piena']],
                   key=lambda x: x['volume_mm3'], reverse=True)
    parziali = sorted([s for s in scatole if not s['is_piena']],
                      key=lambda x: x['volume_mm3'], reverse=True)

    pallet_list = []
    pallet_id = 1

    def new_pallet():
        return {
            "pallet_id": pallet_id,
            "layers": [],
            "altezza_totale_mm": 0,
            "n_scatole": 0
        }

    current_pallet = new_pallet()
    layer_n = 1

    def add_layer_to_pallet(pallet, boxes_batch, tipo):
        """Tenta di aggiungere un layer al pallet corrente.
        Ritorna (scatole_non_piazzate, layer_aggiunto: bool)."""
        nonlocal layer_n

        layer = build_layer(boxes_batch)
        if layer is None or not layer['placed']:
            return boxes_batch, False

        altezza_layer = layer['altezza_mm']
        nuova_altezza = pallet['altezza_totale_mm'] + altezza_layer

        if nuova_altezza > PALLET_H:
            return boxes_batch, False  # Non entra → chiudi pallet

        pallet['layers'].append({
            "layer_n": layer_n,
            "tipo": tipo,
            "altezza_mm": altezza_layer,
            "altezza_cumulativa_mm": nuova_altezza,
            "scatole": layer['placed']
        })
        layer_n += 1
        pallet['altezza_totale_mm'] = nuova_altezza
        pallet['n_scatole'] += len(layer['placed'])

        return layer['unplaced'], True

    # ── Fase 1: Piazza le scatole PIENE ──────────────────────────────────────
    rimanenti_piene = list(piene)
    while rimanenti_piene:
        unplaced_after, added = add_layer_to_pallet(
            current_pallet, rimanenti_piene, "PIENA"
        )

        if not added:
            # Il pallet corrente è pieno → salva e apri nuovo pallet
            if current_pallet['layers']:
                pallet_list.append(_finalize_pallet(current_pallet))
            pallet_id += 1
            current_pallet = new_pallet()
            layer_n = 1
            # Riprova con tutte le rimanenti sul nuovo pallet
            continue

        if len(unplaced_after) == len(rimanenti_piene):
            # Nessuna scatola piazzata in questo layer (tutte troppo grandi?)
            # → forza chiusura pallet per evitare loop infinito
            if current_pallet['layers']:
                pallet_list.append(_finalize_pallet(current_pallet))
                pallet_id += 1
                current_pallet = new_pallet()
                layer_n = 1
            break

        rimanenti_piene = unplaced_after

    # ── Fase 2: Aggiunge le scatole PARZIALI (layer superiori) ───────────────
    rimanenti_parziali = list(parziali)
    while rimanenti_parziali:
        unplaced_after, added = add_layer_to_pallet(
            current_pallet, rimanenti_parziali, "PARZIALE"
        )

        if not added:
            # Pallet corrente pieno → salva e apri nuovo
            if current_pallet['layers']:
                pallet_list.append(_finalize_pallet(current_pallet))
            pallet_id += 1
            current_pallet = new_pallet()
            layer_n = 1
            continue

        if len(unplaced_after) == len(rimanenti_parziali):
            if current_pallet['layers']:
                pallet_list.append(_finalize_pallet(current_pallet))
                pallet_id += 1
                current_pallet = new_pallet()
                layer_n = 1
            break

        rimanenti_parziali = unplaced_after

    # Salva l'ultimo pallet se ha layer
    if current_pallet['layers']:
        pallet_list.append(_finalize_pallet(current_pallet))

    return pallet_list


def _finalize_pallet(pallet: Dict) -> Dict:
    """Calcola statistiche finali del pallet."""
    volume_usato = sum(
        b['placed_l_mm'] * b['placed_p_mm'] * b['a_mm']
        for layer in pallet['layers']
        for b in layer['scatole']
    )
    volume_pallet = PALLET_L * PALLET_P * pallet['altezza_totale_mm']
    fill_pct = round(volume_usato / volume_pallet * 100, 1) if volume_pallet > 0 else 0

    return {
        **pallet,
        "volume_usato_mm3": volume_usato,
        "volume_pallet_mm3": volume_pallet,
        "fill_pct": fill_pct
    }


def genera_report_testuale(pallet_list: List[Dict]) -> str:
    """Genera il report testuale leggibile per ogni pallet."""
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  PIANO DI PALLETIZZAZIONE — {len(pallet_list)} PALLET TOTALI")
    lines.append(f"{'='*60}\n")

    for pallet in pallet_list:
        lines.append(f"PALLET {pallet['pallet_id']} — "
                     f"Altezza: {pallet['altezza_totale_mm']}mm  |  "
                     f"Scatole: {pallet['n_scatole']}  |  "
                     f"Riempimento: {pallet['fill_pct']}%")
        lines.append(f"{'-'*60}")

        for layer in pallet['layers']:
            lines.append(
                f"  Layer {layer['layer_n']} [{layer['tipo']}] — "
                f"Altezza layer: {layer['altezza_mm']}mm  |  "
                f"Altezza cumulativa: {layer['altezza_cumulativa_mm']}mm  |  "
                f"Scatole: {len(layer['scatole'])}"
            )
            for box in layer['scatole']:
                rot_str = " (ruotata 90°)" if box['rotated'] else ""
                stato = "PIENA" if box['is_piena'] else f"PARZ. {box['fill_ratio']*100:.0f}%"
                lines.append(
                    f"    • {box['cod_prodotto']} | {box['codice_scatola']} | "
                    f"{box['placed_l_mm']}x{box['placed_p_mm']}x{box['a_mm']}mm{rot_str} | "
                    f"Pos: ({box['pos_x_mm']}, {box['pos_y_mm']})mm | {stato}"
                )
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from boxing_algorithm import calcola_boxing

    # Test con dati di esempio
    prodotti_test = [
        {"cod_prodotto": "4551120610003", "qta": 500, "qta_massima": 220,
         "codice_scatola": "VP8017/0", "l_mm": 500, "p_mm": 390, "a_mm": 290},
        {"cod_prodotto": "990951SLV0003", "qta": 35, "qta_massima": 10,
         "codice_scatola": "VP4129/0", "l_mm": 340, "p_mm": 195, "a_mm": 135},
        {"cod_prodotto": "4551691010003", "qta": 300, "qta_massima": 250,
         "codice_scatola": "VP0200/0", "l_mm": 400, "p_mm": 400, "a_mm": 600},
        {"cod_prodotto": "4551520310003", "qta": 55, "qta_massima": 10,
         "codice_scatola": "VP4175/0", "l_mm": 240, "p_mm": 140, "a_mm": 140},
    ]

    boxing = calcola_boxing(prodotti_test)
    pallet_list = palletizza(boxing['scatole'])

    print(genera_report_testuale(pallet_list))
    print(f"DEBUG: {len(boxing['scatole'])} scatole → {len(pallet_list)} pallet")
