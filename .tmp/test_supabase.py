"""Test connessione Supabase e creazione tabelle."""
import os, sys
sys.path.insert(0, r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\backend')
from dotenv import load_dotenv
load_dotenv(r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\backend\.env')

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
print('URL:', url)
print('KEY:', key[:30] + '...')

from supabase import create_client
client = create_client(url, key)

# Test connessione: prova a leggere tabella product_boxes
try:
    res = client.table('product_boxes').select('count', count='exact').execute()
    print('✅ Tabella product_boxes esiste! Count:', res.count)
except Exception as e:
    err = str(e)
    if '42P01' in err or 'does not exist' in err.lower() or 'relation' in err.lower():
        print('⚠️  Tabella product_boxes NON ESISTE ancora — va creata')
    else:
        print('❌ Errore connessione:', err)
        sys.exit(1)

# Testa product_boxes insert con un record dummy
try:
    res2 = client.table('pallet_history').select('count', count='exact').execute()
    print('✅ Tabella pallet_history esiste! Count:', res2.count)
except Exception as e:
    err = str(e)
    if '42P01' in err or 'does not exist' in err.lower():
        print('⚠️  Tabella pallet_history NON ESISTE ancora — va creata')
    else:
        print('❌ Errore:', err)
