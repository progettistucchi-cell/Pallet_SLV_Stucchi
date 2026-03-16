"""
generate_pallet_image_3d.py
Livello 3 — Esecuzione

Nuovo generatore di immagini top-down 2D per il 3D Z-Buffer.
Ogni step di assemblaggio Z disegna in background tenue le scatole
già piazzate sotto! Crea un effetto "manuale Ikea" formidabile.
"""

import os
from typing import List, Dict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import to_rgba

from generate_pallet_image import IMG_OUTPUT_DIR, PALETTE, PALLET_L, PALLET_P, _get_color_map


def genera_immagine_pallet_3d(pallet: Dict, output_dir: str = None) -> List[str]:
    out_dir = output_dir or IMG_OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    pid = pallet['pallet_id']
    steps = pallet['layers'] # per algoritmi Z-buffer, layers = step di assemblaggio per quota Z
    n_steps = len(steps)

    all_boxes = [b for step in steps for b in step['scatole']]
    color_map = _get_color_map(all_boxes)
    
    boxes_placed_so_far = []
    generated_paths = []

    for idx, step in enumerate(steps, start=1):
        fig, ax = plt.subplots(figsize=(7, 6))
        
        fig.suptitle(
            f"PALLET {pid} (3D Assembly) | Alt picco: {pallet['altezza_totale_mm']}mm | "
            f"Step {idx}/{n_steps}",
            fontsize=10, fontweight='bold', y=0.98
        )

        ax.set_xlim(0, PALLET_L)
        ax.set_ylim(0, PALLET_P)
        ax.set_aspect('equal')
        ax.set_facecolor('#F8F9FA')
        ax.tick_params(labelsize=6)

        z = step.get('vez_start_mm', 0)
        ax.set_title(
            f"Step di montaggio Z = {z}mm | {len(step['scatole'])} scatole da posizionare",
            fontsize=8, pad=3, color='#34495E', fontweight='bold'
        )

        # Disegna scatole GIA' PIAZZATE: sbiadite in background
        for box in boxes_placed_so_far:
            rect = patches.Rectangle(
                (box['pos_x_mm'], box['pos_y_mm']), box['placed_l_mm'], box['placed_p_mm'],
                linewidth=0.5, edgecolor='#999999', facecolor=to_rgba('#CCCCCC', 0.2), zorder=1
            )
            ax.add_patch(rect)

        # Disegna scatole CORRENTI
        for box in step['scatole']:
            w = box['placed_l_mm']
            h = box['placed_p_mm']
            col = color_map.get(box['codice_scatola'], '#AAAAAA')

            if box['is_piena']:
                face_col = to_rgba(col, 0.85)
                lw, ls, hatch = 1.0, 'solid', None
            else:
                face_col = to_rgba(col, 0.6)
                lw, ls, hatch = 1.0, 'dashed', '//'

            rect = patches.Rectangle(
                (box['pos_x_mm'], box['pos_y_mm']), w, h,
                linewidth=lw, linestyle=ls, edgecolor=col, facecolor=face_col, hatch=hatch, zorder=2
            )
            ax.add_patch(rect)
            
            label_f = f"{box['codice_scatola']}\nZ: {box.get('pos_z_mm', 0)}"
            ax.text(
                box['pos_x_mm'] + w/2, box['pos_y_mm'] + h/2, label_f,
                ha='center', va='center', fontsize=4.5, color='#FFFFFF', zorder=3, fontweight='bold', wrap=True
            )
            
            boxes_placed_so_far.append(box)

        ax.set_xlabel("Lunghezza (mm)", fontsize=6)
        ax.set_ylabel("Profondità (mm)", fontsize=6)
        
        # Legenda
        legend_patches = [patches.Patch(facecolor=col, edgecolor='#333333', label=tipo) for tipo, col in color_map.items()]
        if legend_patches:
            # Posizionamento legenda sotto il plot
            box = ax.get_position()
            ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            ax.legend(handles=legend_patches, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=min(4, len(legend_patches)), fontsize=6)

        plt.tight_layout()
        out_path = os.path.join(out_dir, f"pallet_{pid:02d}_step_{idx:02d}.png")
        fig.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        generated_paths.append(out_path)

    return generated_paths


def genera_tutte_immagini_3d(pallet_list: List[Dict], output_dir: str = None) -> List[str]:
    paths = []
    for pallet in pallet_list:
        step_paths = genera_immagine_pallet_3d(pallet, output_dir)
        paths.extend(step_paths)
    return paths
