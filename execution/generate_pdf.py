"""
generate_pdf.py
Livello 3 — Esecuzione

Genera il report PDF completo della palletizzazione.
Struttura PDF:
  - Pagina 1: Copertina riepilogo (cliente, data, n_pallet, n_scatole)
  - Per ogni pallet: pagina testuale + immagine 2D dei layer

Input:  pallet_list, metadati ordine, path immagini PNG
Output: path al PDF generato in .tmp/
"""

import os
import json
from typing import List, Dict
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

PDF_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', '.tmp')

# ─── Colori brand ────────────────────────────────────────────────────────────
COL_PRIMARY = colors.HexColor('#1A3C6E')     # Blu scuro
COL_ACCENT = colors.HexColor('#E87A3C')      # Arancione
COL_LIGHT = colors.HexColor('#F0F4FA')       # Sfondo tabelle
COL_GREEN = colors.HexColor('#2E7D32')       # PIENA
COL_ORANGE = colors.HexColor('#EF6C00')      # PARZIALE
COL_GREY = colors.HexColor('#757575')
COL_BLACK = colors.HexColor('#1A1A1A')


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('Title1', fontSize=22, textColor=COL_PRIMARY,
                              fontName='Helvetica-Bold', spaceAfter=6,
                              alignment=TA_CENTER))
    styles.add(ParagraphStyle('SubTitle', fontSize=13, textColor=COL_GREY,
                              fontName='Helvetica', spaceAfter=4,
                              alignment=TA_CENTER))
    styles.add(ParagraphStyle('SectionH', fontSize=12, textColor=COL_PRIMARY,
                              fontName='Helvetica-Bold', spaceBefore=8, spaceAfter=4))
    styles.add(ParagraphStyle('LayerH', fontSize=9, textColor=COL_ACCENT,
                              fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=2))
    styles.add(ParagraphStyle('Body', fontSize=8, textColor=COL_BLACK,
                              fontName='Helvetica', spaceAfter=2))
    styles.add(ParagraphStyle('Small', fontSize=7, textColor=COL_GREY,
                              fontName='Helvetica'))
    styles.add(ParagraphStyle('Warning', fontSize=8, textColor=COL_ORANGE,
                              fontName='Helvetica-Bold'))
    return styles


def _build_cover(styles, metadati: Dict, pallet_list: List[Dict]) -> List:
    """Costruisce la pagina di copertina."""
    elems = []

    elems.append(Spacer(1, 20*mm))
    elems.append(Paragraph("PIANO DI PALLETIZZAZIONE", styles['Title1']))
    elems.append(Paragraph("SLV Stucchi — Sistema di Ottimizzazione", styles['SubTitle']))
    elems.append(Spacer(1, 8*mm))
    elems.append(HRFlowable(width="100%", thickness=2, color=COL_ACCENT))
    elems.append(Spacer(1, 8*mm))

    # Info ordine
    info_data = [
        ['Cliente:', metadati.get('cliente', 'N/D')],
        ['Nome:', metadati.get('nome_cliente', 'N/D')],
        ['Numero Ordine:', metadati.get('numero_ordine', 'N/D')],
        ['Data Ordine:', metadati.get('data_ordine', 'N/D')],
        ['Data Elaborazione:', datetime.now().strftime('%d/%m/%Y %H:%M')],
    ]
    info_table = Table(info_data, colWidths=[50*mm, 110*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), COL_PRIMARY),
        ('TEXTCOLOR', (1, 0), (1, -1), COL_BLACK),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), COL_LIGHT),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [COL_LIGHT, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('ROUNDEDCORNERS', [4]),
    ]))
    elems.append(info_table)
    elems.append(Spacer(1, 10*mm))

    # Riepilogo statistiche
    n_pallet = len(pallet_list)
    n_scatole = sum(p['n_scatole'] for p in pallet_list)
    n_piene = sum(
        sum(1 for b in layer['scatole'] if b['is_piena'])
        for p in pallet_list for layer in p['layers']
    )
    n_parziali = n_scatole - n_piene

    stat_data = [
        ['TOTALE PALLET', str(n_pallet)],
        ['SCATOLE TOTALI', str(n_scatole)],
        ['SCATOLE PIENE', str(n_piene)],
        ['SCATOLE PARZIALI', str(n_parziali)],
    ]

    stat_table = Table(stat_data, colWidths=[80*mm, 80*mm])
    stat_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (0, -1), COL_GREY),
        ('TEXTCOLOR', (1, 0), (1, -1), COL_PRIMARY),
        ('BACKGROUND', (0, 0), (-1, -1), COL_LIGHT),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [COL_LIGHT, colors.white]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ]))
    elems.append(stat_table)
    elems.append(PageBreak())
    return elems


def _build_pallet_page(styles, pallet: Dict, img_path: str = None) -> List:
    """Costruisce le pagine per un singolo pallet."""
    elems = []
    pid = pallet['pallet_id']

    # Header pallet
    elems.append(Paragraph(f"PALLET {pid}", styles['SectionH']))
    meta_str = (
        f"Altezza totale: <b>{pallet['altezza_totale_mm']} mm</b>  |  "
        f"Scatole: <b>{pallet['n_scatole']}</b>  |  "
        f"Riempimento: <b>{pallet['fill_pct']}%</b>"
    )
    elems.append(Paragraph(meta_str, styles['Body']))
    elems.append(HRFlowable(width="100%", thickness=1, color=COL_ACCENT,
                            spaceAfter=4))

    # Tabella distinta layer
    header = ['Layer', 'Tipo', 'H Layer', 'H Cum.', 'N. Scatole', 'Scatole (cod. prodotto)']
    t_data = [header]

    for layer in pallet['layers']:
        codici = ', '.join(
            f"{b['cod_prodotto']} ({'P' if b['is_piena'] else 'p'})"
            for b in layer['scatole']
        )
        tipo_col = layer['tipo']
        t_data.append([
            str(layer['layer_n']),
            tipo_col,
            f"{layer['altezza_mm']} mm",
            f"{layer['altezza_cumulativa_mm']} mm",
            str(len(layer['scatole'])),
            codici[:80] + ('…' if len(codici) > 80 else '')
        ])

    t = Table(t_data, colWidths=[15*mm, 22*mm, 20*mm, 20*mm, 22*mm, None])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COL_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COL_LIGHT, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (5, 1), (5, -1), 'LEFT'),
    ]))

    # Colora tipo layer
    for i, layer in enumerate(pallet['layers'], start=1):
        col = COL_GREEN if layer['tipo'] == 'PIENA' else COL_ORANGE
        t.setStyle(TableStyle([('TEXTCOLOR', (1, i), (1, i), col)]))

    elems.append(t)
    elems.append(Spacer(1, 5*mm))

    # Dettaglio scatole per layer
    for layer in pallet['layers']:
        tipo_label = layer['tipo']
        elems.append(Paragraph(
            f"Layer {layer['layer_n']} — {tipo_label}  "
            f"| Alt. layer: {layer['altezza_mm']}mm  "
            f"| Alt. cumul.: {layer['altezza_cumulativa_mm']}mm",
            styles['LayerH']
        ))
        box_data = [['Cod. Prodotto', 'Scatola', 'Dim. (LxPxA) mm',
                     'Pos. (X,Y) mm', 'Rot.', 'Stato', 'Pezzi']]
        for b in layer['scatole']:
            rot = '90°' if b['rotated'] else '—'
            stato = 'PIENA' if b['is_piena'] else f"PARZ {b['fill_ratio']*100:.0f}%"
            box_data.append([
                b['cod_prodotto'],
                b['codice_scatola'],
                f"{b['placed_l_mm']}×{b['placed_p_mm']}×{b['a_mm']}",
                f"({b['pos_x_mm']}, {b['pos_y_mm']})",
                rot,
                stato,
                str(b['n_pezzi'])
            ])
        bt = Table(box_data, colWidths=[35*mm, 22*mm, 30*mm, 26*mm, 10*mm, 22*mm, 15*mm])
        bt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COL_PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 6.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COL_LIGHT, colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#DDDDDD')),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elems.append(bt)
        elems.append(Spacer(1, 2*mm))

    # Immagine 2D pallet
    if img_path and os.path.exists(img_path):
        elems.append(Spacer(1, 4*mm))
        elems.append(Paragraph("Vista Top-Down per Layer", styles['LayerH']))
        # Calcola altezza proporzionale con Pillow
        try:
            from PIL import Image as PILImage
            with PILImage.open(img_path) as pil_img:
                orig_w, orig_h = pil_img.size
            max_w = 160 * mm
            ratio = orig_h / orig_w if orig_w > 0 else 1
            img_h = max_w * ratio
            
            # Limite altezza pagina intera
            max_h_page = 230 * mm
            if img_h > max_h_page:
                img_h = max_h_page
                max_w = img_h / ratio
                
            img = Image(img_path, width=max_w, height=img_h)
        except ImportError:
            # Fallback senza Pillow: stima fissa
            img = Image(img_path, width=160*mm, height=120*mm)
        elems.append(img)

    elems.append(PageBreak())
    return elems


def _build_warnings_page(styles, warnings: Dict) -> List:
    """Aggiunge pagina con i warning (prodotti non trovati, skippati)."""
    elems = []
    non_trovati = warnings.get('prodotti_non_trovati', [])
    skippati_db = warnings.get('skippati_db', [])

    if not non_trovati and not skippati_db:
        return elems

    elems.append(Paragraph("⚠️ Avvisi e Prodotti Non Palletizzati", styles['SectionH']))
    elems.append(HRFlowable(width="100%", thickness=1, color=COL_ORANGE))
    elems.append(Spacer(1, 3*mm))

    if non_trovati:
        elems.append(Paragraph(
            "Prodotti nell'ordine SAP NON trovati nel DB:", styles['Warning']
        ))
        for cod in non_trovati:
            elems.append(Paragraph(f"  • {cod}", styles['Body']))
        elems.append(Spacer(1, 3*mm))

    if skippati_db:
        elems.append(Paragraph("Prodotti nel DB con dati mancanti (skippati):", styles['Warning']))
        for item in skippati_db:
            if isinstance(item, dict):
                elems.append(Paragraph(
                    f"  • {item.get('cod', '?')} — {item.get('motivo', '')}", styles['Body']
                ))
            else:
                elems.append(Paragraph(f"  • {item}", styles['Body']))

    return elems


def genera_pdf(metadati: Dict, pallet_list: List[Dict],
               img_paths: List[str], warnings: Dict = None,
               output_dir: str = None) -> str:
    """
    Genera il PDF completo.

    Args:
        metadati: info ordine (cliente, data, ecc.)
        pallet_list: lista pallet da pallet_algorithm
        img_paths: lista path PNG (uno per pallet)
        warnings: {prodotti_non_trovati, skippati_db}
        output_dir: cartella output

    Returns:
        path al PDF generato
    """
    out_dir = output_dir or PDF_OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    pdf_path = os.path.join(out_dir, f"pallet_report_{ts}.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    styles = _styles()
    story = []

    # Copertina
    story.extend(_build_cover(styles, metadati, pallet_list))

    # Pagine pallet
    img_map = {os.path.basename(p): p for p in (img_paths or [])}
    for pallet in pallet_list:
        pid = pallet['pallet_id']
        img_key = f"pallet_{pid:02d}.png"
        img_path = img_map.get(img_key, None)
        story.extend(_build_pallet_page(styles, pallet, img_path))

    # Pagina warning
    if warnings:
        story.extend(_build_warnings_page(styles, warnings))

    doc.build(story)
    print(f"✅ PDF generato: {pdf_path}")
    return pdf_path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from boxing_algorithm import calcola_boxing
    from pallet_algorithm import palletizza
    from generate_pallet_image import genera_tutte_immagini

    prodotti_test = [
        {"cod_prodotto": "4551120610003", "qta": 500, "qta_massima": 220,
         "codice_scatola": "VP8017/0", "l_mm": 500, "p_mm": 390, "a_mm": 290},
        {"cod_prodotto": "990951SLV0003", "qta": 35, "qta_massima": 10,
         "codice_scatola": "VP4129/0", "l_mm": 340, "p_mm": 195, "a_mm": 135},
    ]

    boxing = calcola_boxing(prodotti_test)
    pallet_list = palletizza(boxing['scatole'])
    img_paths = genera_tutte_immagini(pallet_list)

    metadati = {"cliente": "TEST-001", "nome_cliente": "Test SLV",
                "numero_ordine": "1018628", "data_ordine": "01/03/2026"}
    warnings = {"prodotti_non_trovati": ["CODICE_XXX"], "skippati_db": []}

    pdf_path = genera_pdf(metadati, pallet_list, img_paths, warnings)
    print(f"PDF: {pdf_path}")
