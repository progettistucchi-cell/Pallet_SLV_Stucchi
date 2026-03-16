"""Script di test per la pipeline completa."""
import sys, os
sys.path.insert(0, r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\execution')
os.chdir(r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi')

from run_pipeline import run_pipeline

result = run_pipeline(
    sap_file_path=r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\1018628.XLS',
    use_supabase=False
)

print('SUCCESS:', result['success'])
if not result['success']:
    print('ERROR:', result.get('error'))
    sys.exit(1)

print('N_PALLET:', result['n_pallet'])
print('PDF:', result['pdf_path'])
print('IMGS:', len(result['img_paths']), 'immagini')
print('WARNINGS:', result['warnings'])
print()

rb = result['riepilogo_boxing']
print('=== RIEPILOGO BOXING ===')
print('  Scatole totali:', rb['n_scatole_totali'])
print('  Piene:', rb['n_scatole_piene'])
print('  Parziali:', rb['n_scatole_parziali'])
print()
print('=== PALLET SUMMARY ===')
for p in result['pallet_list']:
    print(f"  Pallet {p['pallet_id']}: {len(p['layers'])} layers, {p['n_scatole']} scatole, H={p['altezza_totale_mm']}mm, Fill={p['fill_pct']}%")

print()
print('=== REPORT TESTUALE ===')
print(result['report_testo'])
