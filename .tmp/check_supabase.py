"""Test rapido: verifica quanti prodotti ci sono in Supabase"""
import os, sys
sys.path.insert(0, r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\backend')
from dotenv import load_dotenv
load_dotenv(r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\backend\.env')

from supabase import create_client
url = os.environ['SUPABASE_URL']
key = os.environ['SUPABASE_KEY']
client = create_client(url, key)

res = client.table('product_boxes').select('codice_prodotto, qta_massima').execute()
print(f"Prodotti in Supabase: {len(res.data)}")
for r in res.data[:5]:
    print(f"  {r['codice_prodotto']} — max {r['qta_massima']} pz")
if len(res.data) > 5:
    print(f"  ... e altri {len(res.data)-5}")
