"""Script di test per verificare output pipeline - scrive su file."""
import sys, os
sys.path.insert(0, r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\execution')
os.chdir(r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi')

from run_pipeline import run_pipeline

result = run_pipeline(
    sap_file_path=r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\1018628.XLS',
    use_supabase=False
)

# Scrivi su file per evitare problemi encoding PowerShell
out_path = r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\.tmp\result_summary.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(f"SUCCESS: {result['success']}\n")
    if not result['success']:
        f.write(f"ERROR: {result.get('error')}\n")
    else:
        f.write(f"N_PALLET: {result['n_pallet']}\n")
        f.write(f"PDF: {result['pdf_path']}\n")
        f.write(f"IMGS: {result['img_paths']}\n")
        f.write(f"WARNINGS: {result['warnings']}\n\n")
        rb = result['riepilogo_boxing']
        f.write(f"BOXING: Totali={rb['n_scatole_totali']}, Piene={rb['n_scatole_piene']}, Parziali={rb['n_scatole_parziali']}\n\n")
        f.write("=== PALLET ===\n")
        for p in result['pallet_list']:
            f.write(f"  Pallet {p['pallet_id']}: {len(p['layers'])} layers, {p['n_scatole']} scatole, H={p['altezza_totale_mm']}mm, Fill={p['fill_pct']}%\n")
        f.write("\n=== REPORT ===\n")
        f.write(result.get('report_testo', ''))

print(f"Scritto su {out_path}")
