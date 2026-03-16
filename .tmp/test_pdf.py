"""Test specifico del PDF con traceback completo."""
import sys, os, traceback
sys.path.insert(0, r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\execution')
os.chdir(r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi')

from boxing_algorithm import calcola_boxing
from pallet_algorithm import palletizza
from generate_pallet_image import genera_tutte_immagini
from generate_pdf import genera_pdf

prodotti_test = [
    {"cod_prodotto": "4551120610003", "qta": 440, "qta_massima": 220,
     "codice_scatola": "VP8017/0", "l_mm": 500, "p_mm": 390, "a_mm": 290},
    {"cod_prodotto": "990951SLV0003", "qta": 20, "qta_massima": 10,
     "codice_scatola": "VP4129/0", "l_mm": 340, "p_mm": 195, "a_mm": 135},
]

boxing = calcola_boxing(prodotti_test)
pallet_list = palletizza(boxing['scatole'])
img_paths = genera_tutte_immagini(pallet_list)

metadati = {"cliente": "TEST-001", "nome_cliente": "Test SLV",
            "numero_ordine": "1018628", "data_ordine": "01/03/2026"}

try:
    pdf_path = genera_pdf(metadati, pallet_list, img_paths, {}, output_dir=r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\.tmp')
    with open(r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\.tmp\pdf_test_result.txt', 'w') as f:
        f.write(f"PDF OK: {pdf_path}\n")
    print("PDF OK:", pdf_path)
except Exception as e:
    err = traceback.format_exc()
    with open(r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\.tmp\pdf_error.txt', 'w') as f:
        f.write(err)
    print("ERRORE - vedi pdf_error.txt")
