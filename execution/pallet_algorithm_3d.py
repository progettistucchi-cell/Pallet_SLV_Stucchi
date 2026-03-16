"""
pallet_algorithm_3d.py
Livello 3 — Esecuzione

Algoritmo di palletizzazione 3D VERO (Z-Buffer / Height Map)
Nessun uso di "Layer" fisici. Le scatole vengono incastrate negli spazi vuoti 3D.
Usa la Bottom-Left Fill Heuristic.

L'output viene poi "falsificato" in pseudo-layer (raggruppate per quota Z di partenza)
per mantenere totale retro-compatibilità con le pipeline di PDF e Immagini attuali.
"""
import copy
from typing import List, Dict

PALLET_L = 800
PALLET_P = 1200
PALLET_H = 1600


def get_candidates(placed_boxes: List[Dict]) -> tuple[List[int], List[int]]:
    """Ritorna i punti candidati X e Y per la Bottom-Left Heuristic (inclusa coordinata 0)."""
    cx = {0}
    cy = {0}
    for b in placed_boxes:
        if b['pos_x_mm'] + b['placed_l_mm'] < PALLET_L:
            cx.add(b['pos_x_mm'] + b['placed_l_mm'])
        if b['pos_y_mm'] + b['placed_p_mm'] < PALLET_P:
            cy.add(b['pos_y_mm'] + b['placed_p_mm'])
    return sorted(list(cx)), sorted(list(cy))


def check_support(x: int, y: int, z: int, l: int, p: int, placed_boxes: List[Dict]) -> bool:
    """Verifica se la scatola alla quota Z ha almeno il 75% di superficie d'appoggio."""
    if z == 0:
        return True  # A terra è perfetto

    support_area = 0
    box_area = l * p
    
    for b in placed_boxes:
        # Se la scatola b fa da "pavimento" per la nuova scatola
        if b['pos_z_mm'] + b['a_mm'] == z:
            # Intersezione 2D
            ix = max(x, b['pos_x_mm'])
            iy = max(y, b['pos_y_mm'])
            iw = min(x + l, b['pos_x_mm'] + b['placed_l_mm']) - ix
            ih = min(y + p, b['pos_y_mm'] + b['placed_p_mm']) - iy
            
            if iw > 0 and ih > 0:
                support_area += iw * ih
                
    return support_area >= (box_area * 0.70)


def palletizza_3d(scatole: List[Dict]) -> List[Dict]:
    """
    Algoritmo Z-Buffer.
    """
    if not scatole:
        return []

    # 1. Smistamento Intelligente per 3D (Z-Buffer):
    # Altezza decrescente, poi Area decrescente.
    piene = sorted([s for s in scatole if s['is_piena']], 
                   key=lambda x: (x['a_mm'], x['l_mm'] * x['p_mm']), reverse=True)
    parziali = sorted([s for s in scatole if not s['is_piena']], 
                      key=lambda x: (x['a_mm'], x['l_mm'] * x['p_mm']), reverse=True)
                      
    all_boxes = piene + parziali
    
    pallet_list = []
    pallet_id = 1
    
    remaining_boxes = copy.deepcopy(all_boxes)
    # Filtro tolleranza
    to_pack = []
    for b in remaining_boxes:
        if (b['l_mm'] > PALLET_L and b['l_mm'] > PALLET_P) or (b['p_mm'] > PALLET_L and b['p_mm'] > PALLET_P):
            print(f"WARN: Scatola {b['codice_scatola']} oversize {b['l_mm']}x{b['p_mm']}")
            continue
        to_pack.append(b)
        
    remaining_boxes = to_pack
    
    while remaining_boxes:
        placed = []
        new_remaining = []
        
        for box in remaining_boxes:
            best_z = float('inf')
            best_score = float('inf')
            best_placement = None
            
            cand_x, cand_y = get_candidates(placed)
            
            # Prova entrambe le piazze (L x P) e (P x L)
            orientations = [(False, box['l_mm'], box['p_mm'])]
            if box['l_mm'] != box['p_mm']:
                orientations.append((True, box['p_mm'], box['l_mm']))
                
            for rot, l, p in orientations:
                for x in cand_x:
                    if x + l > PALLET_L: continue
                    for y in cand_y:
                        if y + p > PALLET_P: continue
                        
                        # Trova la Z di "caduta" (dove si appoggia)
                        z = 0
                        for b in placed:
                            # Controlla intersezione orizzontale
                            if not (x >= b['pos_x_mm'] + b['placed_l_mm'] or 
                                    x + l <= b['pos_x_mm'] or 
                                    y >= b['pos_y_mm'] + b['placed_p_mm'] or 
                                    y + p <= b['pos_y_mm']):
                                top = b['pos_z_mm'] + b['a_mm']
                                if top > z:
                                    z = top
                                    
                        # Verifica altezza max pallet
                        if z + box['a_mm'] > PALLET_H:
                            continue
                            
                        # Verifica stabilità fisica (70% appoggio)
                        if not check_support(x, y, z, l, p, placed):
                            continue
                            
                        # Calcola score Bottom-Left
                        score = x + y
                        
                        eps = 1e-5
                        if z < best_z - eps or (abs(z - best_z) < eps and score < best_score):
                            best_z = z
                            best_score = score
                            best_placement = dict(box, 
                                pos_x_mm=x, pos_y_mm=y, pos_z_mm=z,
                                placed_l_mm=l, placed_p_mm=p, rotated=rot
                            )
            
            if best_placement:
                placed.append(best_placement)
            else:
                new_remaining.append(box)
                
        if not placed:
            break
            
        # Costruisci "Pseudo-Layers" (per retrocompatibilità PDF/Immagini)
        # Raggruppa le scatole con la stessa Z d'inizio in uno step di montaggio
        z_groups = {}
        max_h = 0
        volume_usato = 0
        for b in placed:
            z = b['pos_z_mm']
            if z not in z_groups: z_groups[z] = []
            z_groups[z].append(b)
            
            top_h = b['pos_z_mm'] + b['a_mm']
            if top_h > max_h: max_h = top_h
            volume_usato += (b['placed_l_mm'] * b['placed_p_mm'] * b['a_mm'])
            
        sorted_zs = sorted(list(z_groups.keys()))
        layers_compat = []
        layer_n = 1
        
        for z in sorted_zs:
            boxes_in_z = z_groups[z]
            max_a_in_z = max(b['a_mm'] for b in boxes_in_z)
            
            layers_compat.append({
                "layer_n": layer_n,
                "vez_start_mm": z,           # Metadato aggiunto per 3D
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
            "layers": layers_compat, # Sono Step Z-Buffer ora
            "altezza_totale_mm": max_h,
            "n_scatole": len(placed),
            "volume_usato_mm3": volume_usato,
            "volume_pallet_mm3": volume_pallet,
            "fill_pct": fill_pct
        })
        
        pallet_id += 1
        
        if len(new_remaining) == len(remaining_boxes):
            break
            
        remaining_boxes = new_remaining
        
    return pallet_list


def genera_report_testuale_3d(pallet_list: List[Dict]) -> str:
    """Genera report textuale aggiornato per il 3D Z-Buffer."""
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  PIANO DI PALLETIZZAZIONE 3D — {len(pallet_list)} PALLET TOTALI")
    lines.append(f"{'='*60}\n")

    for pallet in pallet_list:
        lines.append(f"PALLET {pallet['pallet_id']} — "
                     f"Altezza picco: {pallet['altezza_totale_mm']}mm  |  "
                     f"Scatole: {pallet['n_scatole']}  |  "
                     f"Riempimento Vero: {pallet['fill_pct']}%")
        lines.append(f"{'-'*60}")

        for step in pallet['layers']:
            lines.append(
                f"  Step Z: {step['vez_start_mm']}mm [{step['tipo']}] — "
                f"Scatole posizionate a questa quota: {len(step['scatole'])}"
            )
            for box in step['scatole']:
                rot_str = " (ruotata 90°)" if box['rotated'] else ""
                lines.append(
                    f"    • {box['cod_prodotto']} | {box['codice_scatola']} | "
                    f"{box['placed_l_mm']}x{box['placed_p_mm']}x{box['a_mm']}mm{rot_str} | "
                    f"Pos: (X:{box['pos_x_mm']}, Y:{box['pos_y_mm']}, Z:{box['pos_z_mm']})mm"
                )
        lines.append("")

    return "\n".join(lines)
