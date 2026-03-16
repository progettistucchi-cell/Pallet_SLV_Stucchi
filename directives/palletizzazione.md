# Direttiva: Sistema di Ottimizzazione Palletizzazione SLV Stucchi

## Obiettivo
Ricevere un file ordine SAP (.XLS), incrociarlo con il DB prodotti/scatole, calcolare il boxing ottimale e generare un piano di palletizzazione 3D con report PDF e visualizzazioni 2D.

## Input
| File | Formato | Note |
|------|---------|-------|
| File ordine SAP | `.XLS` UTF-16 TSV | Esportato da SAP |
| DB prodotti | Supabase `product_boxes` o fallback XLSX locale | `SLV qtà scatola.xlsx` |

### Struttura File SAP (UTF-16 TSV)
Colonne (indice 0-based):
- `[0]` Cliente
- `[1]` Nome 1
- `[2]` Dt. OrdAcq
- `[6]` Materiale (numero doc SAP — NON è il codice prodotto)
- `[7]` Cd. materiale cliente → **codice prodotto** (coincide con DB SLV)
- `[9]` Qtà ord. → **quantità pezzi da palletizzare**
- Righe da SKIPPARE: prima riga (header), righe con `*` in col [0], righe vuote

### Struttura DB Prodotti (Supabase `product_boxes`)
Colonne: `codice_prodotto, qta_massima, codice_scatola, l_mm, p_mm, a_mm`
- Prodotti con "dato mancante" → log warning → skip (non palletizzare)

## Costanti Pallet
- Base: 800mm × 1200mm (Euro pallet)
- Altezza massima: 1600mm
- Altezza layer: = altezza_max delle scatole presenti nel layer (spazio vuoto sopra le scatole basse è accettabile)
- Rotazione: ammessa sul piano XY (swap L e P), altezza Z rimane fissa

## Pipeline di Esecuzione
```
parse_sap_order.py
  → parse_product_db.py (join con DB)
    → boxing_algorithm.py
      → pallet_algorithm.py
        → generate_pallet_image.py
          → generate_pdf.py
```

## Logica Boxing
1. Per ogni prodotto nell'ordine → cerca nel DB per `codice_prodotto`
2. `n_scatole_piene = qta // qta_massima`
3. `resto = qta % qta_massima`
4. Se `resto > 0` → crea 1 scatola parziale con `n_pezzi = resto`
5. **MAI mischiare prodotti diversi nella stessa scatola**

## Logica Palletizzazione
1. Separa scatole in due liste: PIENE e PARZIALI
2. Ordina ogni lista per volume scatola decrescente (scatole più grandi prima)
3. Processo layer-by-layer:
   a. Prendi il pallet corrente
   b. Tenta di riempire un layer con scatole PIENE (rect bin packing 2D su 800×1200mm)
   c. Se altezza cumulativa + altezza_layer_successivo > 1600mm → chiudi pallet, apri nuovo
   d. Quando PIENE esaurite → passa alle PARZIALI (stessa logica, layer superiori)
4. Ottimizzazione: massimizza il numero di scatole per layer (meno pallet = meglio)
5. Orientamento scatole: prova entrambe le orientazioni (L×P e P×L) per massimizzare fit

## Output
- JSON strutturato: `{n_pallet, pallet: [{id, layers: [{n, altezza_mm, scatole: [{...}]}]}]}`
- PDF report: distinta per pallet e per layer
- PNG immagini: top-down view di ogni layer (colori diversi per tipo scatola)

## Casi Edge
- Prodotto non trovato nel DB → log warning, skip, includi nel report come "NON PALLETIZZATO"
- Scatola con `dato mancante` nel DB → stessa gestione
- Qty = 0 → skip
- Scatola più grande del pallet → log error, skip
- Ordine vuoto → errore con messaggio chiaro

## Dipendenze Python
```
openpyxl, supabase, rectpack, reportlab, matplotlib, Pillow, fastapi, uvicorn, python-multipart
```

## Aggiornamenti
- 2026-03-02: Prima versione. File SAP: UTF-16 TSV, col [7] = codice prodotto, col [9] = quantità.
