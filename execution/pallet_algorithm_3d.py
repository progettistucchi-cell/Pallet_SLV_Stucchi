"""
pallet_algorithm_3d.py
Livello 3 — Esecuzione

Algoritmo di palletizzazione 3D VERO (Z-Buffer / Height Map)
Nessun uso di "Layer" fisici. Le scatole vengono incastrate negli spazi vuoti 3D.
Usa la Bottom-Left Fill Heuristic.

L'output viene poi "falsificato" in pseudo-layer (raggruppate per quota Z di partenza)
per mantenere totale retro-compatibilità con le pipeline di PDF e Immagini attuali.

Vincoli aziendali implementati:
  1. VP4268/0: solo orizzontale, lato 1350mm sempre parallelo all'asse Y (120cm).
  2. Altezza max nominale 1450mm + tolleranza 50mm su tutti e tre gli assi.
  3. Primo layer deve coprire >=80% della superficie base; warning se non raggiunta.
  4. Scatole possono essere messe in 6 orientazioni (incluse verticali).
  5. Prodotti con lo stesso codice_scatola devono essere posizionati consecutivamente
     (tutti i box di prodotto A prima di quelli di B, ecc.).
"""
import copy
from typing import List, Dict, Tuple, Optional

# ─── Costanti Pallet ────────────────────────────────────────────────────────
PALLET_L = 800       # mm larghezza nominale
PALLET_P = 1200      # mm profondità nominale
PALLET_H = 1450      # mm altezza nominale (era 1600, ora 145cm)
TOLERANCE_MM = 50    # 5cm tolleranza su tutti gli assi

PALLET_L_MAX = PALLET_L + TOLERANCE_MM   # 850mm
PALLET_P_MAX = PALLET_P + TOLERANCE_MM   # 1250mm
PALLET_H_MAX = PALLET_H + TOLERANCE_MM   # 1500mm

MIN_BASE_COVERAGE = 0.80   # 80% copertura superficie base obbligatoria
CODICE_SOLO_ORIZZONTALE = 'VP4268/0'   # questa scatola non può mai essere verticale


# ─── Orientazioni Scatola ────────────────────────────────────────────────────

def get_orientations(box: Dict) -> List[Tuple]:
    """
    Ritorna la lista di orientazioni valide per la scatola.

    Ogni orientazione è una tupla: (placed_l, placed_p, height, label)
    dove placed_l = dimensione lungo X (larghezza pallet),
          placed_p = dimensione lungo Y (profondità pallet),
          height   = dimensione verticale (altezza sul pallet),
          label    = stringa descrittiva per report/PDF.

    Orientazioni possibili per scatole normali (dimensioni L, P, A):
      - normale:              placed_l=L, placed_p=P, h=A
      - ruotata:              placed_l=P, placed_p=L, h=A
      - verticale_lungo_1:   placed_l=L, placed_p=A, h=P
      - verticale_lungo_2:   placed_l=A, placed_p=L, h=P
      - verticale_corto_1:   placed_l=P, placed_p=A, h=L
      - verticale_corto_2:   placed_l=A, placed_p=P, h=L

    VP4268/0: SOLO orizzontale con il lato 1350mm sempre su Y (asse profondità).
    """
    l, p, a = box['l_mm'], box['p_mm'], box['a_mm']
    codice = box.get('codice_scatola', '')

    if codice == CODICE_SOLO_ORIZZONTALE:
        # Trova il lato lungo (1350mm) e mettilo sempre su Y
        # Le due dimensioni orizzontali sono l e p; a è l'altezza fissa.
        # Il lato lungo deve stare su Y → placed_p = max(l, p)
        long_side = max(l, p)
        short_side = min(l, p)
        return [
            (short_side, long_side, a, 'orizzontale_VP4268')
        ]

    # Per tutte le altre scatole: fino a 6 orientazioni (dedup via set)
    raw = [
        (l, p, a, 'normale'),
        (p, l, a, 'ruotata'),
        (l, a, p, 'verticale_lungo_1'),
        (a, l, p, 'verticale_lungo_2'),
        (p, a, l, 'verticale_corto_1'),
        (a, p, l, 'verticale_corto_2'),
    ]
    # Rimuove duplicati (possibili se due dimensioni sono uguali)
    seen = set()
    result = []
    for pl, pp, h, label in raw:
        key = (pl, pp, h)
        if key not in seen:
            seen.add(key)
            result.append((pl, pp, h, label))
    return result


# ─── Ordinamento con Vincolo 5 ───────────────────────────────────────────────

def ordina_scatole_con_vincolo(boxes: List[Dict]) -> List[Dict]:
    """
    Vincolo 5: prodotti con lo stesso codice_scatola devono essere consecutivi.

    Logica:
    - Raggruppa per codice_scatola, mantenendo l'ordine di prima apparizione.
    - Dentro ogni gruppo codice_scatola, mantieni l'ordine di prima apparizione
      del cod_prodotto (A prima, poi B, poi C come arrivano dal boxing).
    - Dentro ogni coppia (codice_scatola, cod_prodotto): piene prima, poi parziali.
    - Gruppi con un solo prodotto vengono ordinati per altezza decrescente
      (ottimizzazione stabilità) senza violare il vincolo 5.
    """
    # Step 1: raccolta ordine di apparizione dei gruppi
    scatola_order: List[str] = []
    by_scatola: Dict[str, Dict[str, List[Dict]]] = {}

    for box in boxes:
        cs = box['codice_scatola']
        cp = box['cod_prodotto']

        if cs not in by_scatola:
            by_scatola[cs] = {}
            scatola_order.append(cs)

        if cp not in by_scatola[cs]:
            by_scatola[cs][cp] = []

        by_scatola[cs][cp].append(box)

    result: List[Dict] = []
    for cs in scatola_order:
        prodotti_group = by_scatola[cs]
        prodotti_keys = list(prodotti_group.keys())  # ordine originale

        if len(prodotti_keys) == 1:
            # Un solo prodotto: ordinamento libero per ottimizzazione (altezza desc)
            boxes_cp = prodotti_group[prodotti_keys[0]]
            piene = sorted([b for b in boxes_cp if b['is_piena']],
                           key=lambda x: (x['a_mm'], x['l_mm'] * x['p_mm']), reverse=True)
            parziali = sorted([b for b in boxes_cp if not b['is_piena']],
                              key=lambda x: (x['a_mm'], x['l_mm'] * x['p_mm']), reverse=True)
            result.extend(piene + parziali)
        else:
            # Più prodotti condividono la stessa scatola → ordine prodotto obbligatorio
            for cp in prodotti_keys:
                boxes_cp = prodotti_group[cp]
                piene = [b for b in boxes_cp if b['is_piena']]
                parziali = [b for b in boxes_cp if not b['is_piena']]
                result.extend(piene + parziali)

    return result


# ─── Copertura Base ──────────────────────────────────────────────────────────

def calcola_copertura_base(placed: List[Dict]) -> float:
    """
    Calcola la percentuale di superficie base (z=0) coperta dalle scatole.
    Le scatole a z=0 non si sovrappongono per definizione dell'algoritmo.
    """
    base_area = sum(
        b['placed_l_mm'] * b['placed_p_mm']
        for b in placed
        if b['pos_z_mm'] == 0
    )
    return base_area / (PALLET_L * PALLET_P)


# ─── Candidati Bottom-Left ───────────────────────────────────────────────────

def get_candidates(placed_boxes: List[Dict]) -> Tuple[List[int], List[int]]:
    """Ritorna i punti candidati X e Y per la Bottom-Left Heuristic."""
    cx = {0}
    cy = {0}
    for b in placed_boxes:
        edge_x = b['pos_x_mm'] + b['placed_l_mm']
        edge_y = b['pos_y_mm'] + b['placed_p_mm']
        # Non limitare ai bordi nominali: tolleranza gestita nel check placement
        cx.add(edge_x)
        cy.add(edge_y)
    return sorted(list(cx)), sorted(list(cy))


# ─── Stabilità ───────────────────────────────────────────────────────────────

def check_support(x: int, y: int, z: int, l: int, p: int,
                  placed_boxes: List[Dict]) -> bool:
    """Verifica se la scatola alla quota Z ha almeno il 70% di superficie d'appoggio."""
    if z == 0:
        return True  # A terra è sempre stabile

    support_area = 0
    box_area = l * p

    for b in placed_boxes:
        if b['pos_z_mm'] + b['a_mm'] == z:
            ix = max(x, b['pos_x_mm'])
            iy = max(y, b['pos_y_mm'])
            iw = min(x + l, b['pos_x_mm'] + b['placed_l_mm']) - ix
            ih = min(y + p, b['pos_y_mm'] + b['placed_p_mm']) - iy
            if iw > 0 and ih > 0:
                support_area += iw * ih

    return support_area >= (box_area * 0.70)


# ─── Algoritmo principale ────────────────────────────────────────────────────

def palletizza_3d(scatole: List[Dict]) -> List[Dict]:
    """
    Algoritmo Z-Buffer con vincoli aziendali.

    Vincoli applicati:
      1. VP4268/0 solo orizzontale (get_orientations).
      2. Tolleranze dimensionali su tutti gli assi.
      3. Warning copertura base <80%.
      4. 6 orientazioni per scatole normali.
      5. Ordine prodotti consecutivi per stesso codice_scatola.
    """
    if not scatole:
        return []

    # Vincolo 5: ordina rispettando la consecutività per prodotto/scatola
    all_boxes = ordina_scatole_con_vincolo(scatole)

    # Filtra scatole assolutamente oversize (nemmeno con tolleranza entrano)
    to_pack = []
    for b in all_boxes:
        orientations = get_orientations(b)
        fits_at_least_one = any(
            pl <= PALLET_L_MAX and pp <= PALLET_P_MAX and h <= PALLET_H_MAX
            for pl, pp, h, _ in orientations
        )
        if not fits_at_least_one:
            print(f"WARN: Scatola {b['codice_scatola']} oversize, nessuna orientazione valida. Skippata.")
        else:
            to_pack.append(b)

    remaining_boxes = to_pack
    pallet_list = []
    pallet_id = 1

    while remaining_boxes:
        placed: List[Dict] = []
        new_remaining: List[Dict] = []

        for box in remaining_boxes:
            best_z = float('inf')
            best_score = float('inf')
            best_placement: Optional[Dict] = None

            cand_x, cand_y = get_candidates(placed)
            orientations = get_orientations(box)

            for pl, pp, height, label in orientations:
                # Vincolo dimensioni: con tolleranza
                for x in cand_x:
                    if x + pl > PALLET_L_MAX:
                        continue
                    for y in cand_y:
                        if y + pp > PALLET_P_MAX:
                            continue

                        # Trova la Z di "caduta"
                        z = 0
                        for b in placed:
                            if not (x >= b['pos_x_mm'] + b['placed_l_mm'] or
                                    x + pl <= b['pos_x_mm'] or
                                    y >= b['pos_y_mm'] + b['placed_p_mm'] or
                                    y + pp <= b['pos_y_mm']):
                                top = b['pos_z_mm'] + b['a_mm']
                                if top > z:
                                    z = top

                        # Vincolo 2: altezza max con tolleranza
                        if z + height > PALLET_H_MAX:
                            continue

                        # Stabilità fisica (70% appoggio)
                        if not check_support(x, y, z, pl, pp, placed):
                            continue

                        # Score Bottom-Left: priorità a Z bassa, poi a posizione X+Y bassa
                        score = x + y
                        eps = 1e-5
                        if z < best_z - eps or (abs(z - best_z) < eps and score < best_score):
                            best_z = z
                            best_score = score
                            is_rotated = (pl != box['l_mm'] or pp != box['p_mm'])
                            best_placement = dict(
                                box,
                                pos_x_mm=x,
                                pos_y_mm=y,
                                pos_z_mm=z,
                                placed_l_mm=pl,
                                placed_p_mm=pp,
                                a_mm=height,          # altezza effettiva sul pallet
                                rotated=is_rotated,
                                orientation_label=label
                            )

            if best_placement:
                placed.append(best_placement)
            else:
                new_remaining.append(box)

        if not placed:
            break

        # ─── Vincolo 3: copertura base 80% ─────────────────────────────────
        copertura = calcola_copertura_base(placed)
        warning_copertura = None
        if copertura < MIN_BASE_COVERAGE:
            scatole_a_terra = [
                f"{b['codice_scatola']} ({b['cod_prodotto']})"
                for b in placed if b['pos_z_mm'] == 0
            ]
            warning_copertura = (
                f"Copertura base {copertura:.0%} < 80% richiesta. "
                f"Scatole al layer base: {', '.join(scatole_a_terra) if scatole_a_terra else 'nessuna'}. "
                f"Le scatole non posizionate alla base sono state spostate al pallet successivo."
            )
            print(f"  ATTENZIONE Pallet {pallet_id}: {warning_copertura}")

        # ─── Costruisci Pseudo-Layers (retrocompatibilità PDF/Immagini) ─────
        z_groups: Dict[int, List[Dict]] = {}
        max_h = 0
        volume_usato = 0

        for b in placed:
            z = b['pos_z_mm']
            if z not in z_groups:
                z_groups[z] = []
            z_groups[z].append(b)

            top_h = b['pos_z_mm'] + b['a_mm']
            if top_h > max_h:
                max_h = top_h
            volume_usato += b['placed_l_mm'] * b['placed_p_mm'] * b['a_mm']

        sorted_zs = sorted(z_groups.keys())
        layers_compat = []
        layer_n = 1

        for z in sorted_zs:
            boxes_in_z = z_groups[z]
            max_a_in_z = max(b['a_mm'] for b in boxes_in_z)

            layers_compat.append({
                "layer_n": layer_n,
                "vez_start_mm": z,
                "altezza_mm": max_a_in_z,
                "altezza_cumulativa_mm": z + max_a_in_z,
                "tipo": "PIENA" if any(b['is_piena'] for b in boxes_in_z) else "PARZIALE",
                "scatole": boxes_in_z
            })
            layer_n += 1

        volume_pallet = PALLET_L * PALLET_P * max_h
        fill_pct = round((volume_usato / volume_pallet) * 100, 1) if volume_pallet > 0 else 0

        pallet_list.append({
            "pallet_id": pallet_id,
            "layers": layers_compat,
            "altezza_totale_mm": max_h,
            "n_scatole": len(placed),
            "volume_usato_mm3": volume_usato,
            "volume_pallet_mm3": volume_pallet,
            "fill_pct": fill_pct,
            "copertura_base_pct": round(copertura * 100, 1),
            "warning_copertura": warning_copertura,
        })

        pallet_id += 1

        if len(new_remaining) == len(remaining_boxes):
            break

        remaining_boxes = new_remaining

    return pallet_list


# ─── Report Testuale ─────────────────────────────────────────────────────────

def genera_report_testuale_3d(pallet_list: List[Dict]) -> str:
    """Genera report testuale aggiornato per il 3D Z-Buffer con vincoli aziendali."""
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  PIANO DI PALLETIZZAZIONE 3D — {len(pallet_list)} PALLET TOTALI")
    lines.append(f"{'='*60}\n")

    for pallet in pallet_list:
        lines.append(
            f"PALLET {pallet['pallet_id']} — "
            f"Altezza: {pallet['altezza_totale_mm']}mm  |  "
            f"Scatole: {pallet['n_scatole']}  |  "
            f"Fill: {pallet['fill_pct']}%  |  "
            f"Copertura base: {pallet.get('copertura_base_pct', '?')}%"
        )
        if pallet.get('warning_copertura'):
            lines.append(f"  ⚠️  {pallet['warning_copertura']}")
        lines.append(f"{'-'*60}")

        for step in pallet['layers']:
            lines.append(
                f"  Step Z: {step['vez_start_mm']}mm [{step['tipo']}] — "
                f"Scatole a questa quota: {len(step['scatole'])}"
            )
            for box in step['scatole']:
                orient = box.get('orientation_label', '')
                orient_str = f" [{orient}]" if orient else ""
                lines.append(
                    f"    • {box['cod_prodotto']} | {box['codice_scatola']} | "
                    f"{box['placed_l_mm']}x{box['placed_p_mm']}x{box['a_mm']}mm{orient_str} | "
                    f"Pos: (X:{box['pos_x_mm']}, Y:{box['pos_y_mm']}, Z:{box['pos_z_mm']})mm"
                )
        lines.append("")

    return "\n".join(lines)
