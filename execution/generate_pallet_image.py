"""
generate_pallet_image.py
Livello 3 — Esecuzione

Genera immagini 2D top-down (bird's eye view) per ogni layer di ogni pallet.
Usa matplotlib. Output: PNG files in .tmp/images/

Input:  lista pallet da pallet_algorithm.palletizza
Output: lista path PNG generati, uno per pallet (con tutti i layer impilati)
"""

import os
import math
import json
from typing import List, Dict

import matplotlib
matplotlib.use('Agg')  # Backend non-interattivo
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import to_rgba

# Cartella output immagini
IMG_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '.tmp', 'images')

# Palette colori per tipo scatola (codice_scatola → colore)
PALETTE = [
    '#4A90D9', '#E87A3C', '#52B26B', '#9B59B6', '#E74C3C',
    '#1ABC9C', '#F39C12', '#2980B9', '#D35400', '#27AE60',
    '#8E44AD', '#C0392B', '#16A085', '#E67E22', '#2C3E50',
]

PALLET_L = 800
PALLET_P = 1200


def _get_color_map(scatole: List[Dict]) -> Dict[str, str]:
    """Assegna un colore univoco per ogni tipo di scatola (codice_scatola)."""
    tipi = list(dict.fromkeys(b['codice_scatola'] for b in scatole))
    return {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(tipi)}


def genera_immagine_pallet(pallet: Dict, output_dir: str = None) -> str:
    """
    Genera un'immagine PNG con tutti i layer del pallet in vista top-down.
    I layer sono disposti verticalmente nella figura (Layer 1 in basso, ultimo in alto).

    Args:
        pallet: dict da pallet_algorithm con layers, altezza_totale_mm, ecc.
        output_dir: cartella output (default: .tmp/images)

    Returns:
        path al file PNG generato
    """
    out_dir = output_dir or IMG_OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    pid = pallet['pallet_id']
    layers = pallet['layers']
    n_layers = len(layers)

    # Raccoglie tutte le scatole per la color map
    all_boxes = [b for layer in layers for b in layer['scatole']]
    color_map = _get_color_map(all_boxes)

    # Layout figura: n_layers righe, 1 colonna
    fig_height = max(6, n_layers * 3.5)
    fig_width = 7
    fig, axes = plt.subplots(n_layers, 1, figsize=(fig_width, fig_height))
    if n_layers == 1:
        axes = [axes]

    # I layer sono disposti dal basso verso l'alto → inverti l'ordine degli assi
    axes_reversed = list(reversed(axes))

    fig.suptitle(
        f"PALLET {pid}  |  Alt. totale: {pallet['altezza_totale_mm']}mm  |  "
        f"Fill: {pallet['fill_pct']}%  |  Scatole: {pallet['n_scatole']}",
        fontsize=10, fontweight='bold', y=1.01
    )

    for ax, layer in zip(axes, layers):
        ax.set_xlim(0, PALLET_L)
        ax.set_ylim(0, PALLET_P)
        ax.set_aspect('equal')
        ax.set_facecolor('#F5F5F0')
        ax.tick_params(labelsize=6)

        # Titolo layer
        ax.set_title(
            f"Layer {layer['layer_n']} [{layer['tipo']}]  "
            f"H layer: {layer['altezza_mm']}mm  |  "
            f"H cumulativa: {layer['altezza_cumulativa_mm']}mm",
            fontsize=7, pad=3
        )

        # Bordo pallet
        pallet_rect = patches.Rectangle(
            (0, 0), PALLET_L, PALLET_P,
            linewidth=2, edgecolor='#333333', facecolor='none', zorder=1
        )
        ax.add_patch(pallet_rect)

        # Disegna scatole
        for box in layer['scatole']:
            x = box['pos_x_mm']
            y = box['pos_y_mm']
            w = box['placed_l_mm']
            h = box['placed_p_mm']
            col = color_map.get(box['codice_scatola'], '#AAAAAA')

            # Scatole parziali: colore più chiaro + tratteggio
            if box['is_piena']:
                face_col = to_rgba(col, 0.75)
                lw = 1.0
                ls = 'solid'
                hatch = None
            else:
                face_col = to_rgba(col, 0.35)
                lw = 1.0
                ls = 'dashed'
                hatch = '//'

            rect = patches.Rectangle(
                (x, y), w, h,
                linewidth=lw, linestyle=ls,
                edgecolor=col, facecolor=face_col,
                hatch=hatch, zorder=2
            )
            ax.add_patch(rect)

            # Etichetta: codice scatola + dimensioni
            label_f = f"{box['codice_scatola']}\n{w}×{h}"
            ax.text(
                x + w / 2, y + h / 2, label_f,
                ha='center', va='center', fontsize=4.5,
                color='#111111', zorder=3, fontweight='bold',
                wrap=True
            )

            # Indicatore rotazione
            if box['rotated']:
                ax.text(
                    x + w - 8, y + 8, '↺', ha='right', va='bottom',
                    fontsize=5, color='#555555', zorder=4
                )

        ax.set_xlabel("Lunghezza (mm)", fontsize=6)
        ax.set_ylabel("Profondità (mm)", fontsize=6)

    # Legenda tipi scatola
    legend_patches = [
        patches.Patch(facecolor=col, edgecolor='#333333', label=tipo)
        for tipo, col in color_map.items()
    ]
    if legend_patches:
        fig.legend(
            handles=legend_patches, loc='lower center',
            ncol=min(4, len(legend_patches)),
            fontsize=6, title="Tipo Scatola",
            title_fontsize=7, bbox_to_anchor=(0.5, -0.01)
        )

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    out_path = os.path.join(out_dir, f"pallet_{pid:02d}.png")
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

    return out_path


def genera_tutte_immagini(pallet_list: List[Dict], output_dir: str = None) -> List[str]:
    """Genera le immagini per tutti i pallet. Ritorna lista path PNG."""
    paths = []
    for pallet in pallet_list:
        path = genera_immagine_pallet(pallet, output_dir)
        paths.append(path)
        print(f"  🖼️  Pallet {pallet['pallet_id']} → {path}")
    return paths


if __name__ == "__main__":
    # Test rapido con dati sintetici
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from boxing_algorithm import calcola_boxing
    from pallet_algorithm import palletizza

    prodotti_test = [
        {"cod_prodotto": "A001", "qta": 500, "qta_massima": 220,
         "codice_scatola": "VP8017/0", "l_mm": 500, "p_mm": 390, "a_mm": 290},
        {"cod_prodotto": "B002", "qta": 35, "qta_massima": 10,
         "codice_scatola": "VP4129/0", "l_mm": 340, "p_mm": 195, "a_mm": 135},
        {"cod_prodotto": "C003", "qta": 55, "qta_massima": 10,
         "codice_scatola": "VP4175/0", "l_mm": 240, "p_mm": 140, "a_mm": 140},
    ]

    boxing = calcola_boxing(prodotti_test)
    pallet_list = palletizza(boxing['scatole'])
    paths = genera_tutte_immagini(pallet_list)
    print(f"\n✅ Generate {len(paths)} immagini: {paths}")
