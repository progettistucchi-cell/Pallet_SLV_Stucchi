"""Riproduce la chiamata API del frontend per vedere l'errore esatto del backend."""
import urllib.request
import json

file_path = r'C:\Users\HP\.gemini\Pallet_SLV_Stucchi\1018628.XLS'

# Costruisci multipart form-data manualmente
boundary = '----FormBoundary7MA4YWxkTrZu0gW'

with open(file_path, 'rb') as f:
    file_data = f.read()

body = (
    f'------FormBoundary7MA4YWxkTrZu0gW\r\n'
    f'Content-Disposition: form-data; name="file"; filename="esempio di ordine.XLS"\r\n'
    f'Content-Type: application/octet-stream\r\n\r\n'
).encode() + file_data + b'\r\n------FormBoundary7MA4YWxkTrZu0gW--\r\n'

req = urllib.request.Request(
    'http://localhost:8000/api/palletize',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary=----FormBoundary7MA4YWxkTrZu0gW'},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode('utf-8')
        result = json.loads(raw)
        print("SUCCESS:", result.get('n_pallet'), "pallet")
except urllib.error.HTTPError as e:
    raw = e.read().decode('utf-8')
    print(f"HTTP {e.code} — Risposta raw del backend:")
    print(raw[:2000])
except Exception as ex:
    print("Errore:", ex)
