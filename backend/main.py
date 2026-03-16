"""
main.py — Backend FastAPI
Sistema di Ottimizzazione Palletizzazione SLV Stucchi

Endpoints:
  POST /api/palletize          → Esegue pipeline completa, ritorna JSON + streaming
  GET  /api/download-pdf/{ts}  → Scarica PDF generato
  GET  /api/history            → Storico palletizzazioni (Supabase)
  GET  /api/db-status          → Stato connessione Supabase / XLSX
  GET  /api/health             → Health check
"""

import os
import sys
import shutil
import json
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

# Fix encoding Windows: forza UTF-8 su stdout/stderr del processo uvicorn
# Necessario su Windows con encoding default CP1252 per evitare crash
# con print() che contengono caratteri Unicode negli script execution/
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
# Variabile d'ambiente alternativa per sottoprocessi
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

# Setup path per gli script execution/
BASE_DIR = Path(__file__).parent.parent.absolute()
EXECUTION_DIR = BASE_DIR / "execution"
TMP_DIR = BASE_DIR / ".tmp"
sys.path.insert(0, str(EXECUTION_DIR))

from run_pipeline import run_pipeline
from supabase_client import (
    is_supabase_configured, save_pallet_session, get_pallet_history
)

# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Pallet SLV Stucchi API",
    description="Backend per il sistema di ottimizzazione palletizzazione",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, limita agli origin del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_xlsx_path() -> Optional[str]:
    """Cerca il file XLSX del DB prodotti nella root del progetto."""
    for f in BASE_DIR.iterdir():
        if 'SLV' in f.name and f.suffix.lower() == '.xlsx':
            return str(f)
    return None


def _cleanup_tmp_file(path: str):
    """Rimuove un file temporaneo (usato come background task)."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "supabase": is_supabase_configured(),
        "xlsx_db": _get_xlsx_path() is not None
    }


@app.get("/api/db-status")
async def db_status():
    """Restituisce lo stato del database prodotti."""
    xlsx = _get_xlsx_path()
    supabase_ok = is_supabase_configured()
    return {
        "supabase_configured": supabase_ok,
        "xlsx_available": xlsx is not None,
        "xlsx_path": xlsx,
        "active_source": "supabase" if supabase_ok else ("xlsx" if xlsx else "none")
    }


@app.post("/api/palletize")
async def palletize(file: UploadFile = File(...)):
    """
    Esegue la pipeline di palletizzazione su un file SAP (.XLS).

    Uploads:
        file: il file .XLS esportato da SAP

    Returns:
        JSON con pallet_list, riepilogo, warnings, pdf_url, img_paths
    """
    # Validazione estensione
    if not file.filename.upper().endswith(('.XLS', '.XLSX', '.CSV')):
        raise HTTPException(
            status_code=400,
            detail="Formato file non supportato. Usa .XLS, .XLSX o .CSV"
        )

    # Salva file temporaneo
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    tmp_sap = TMP_DIR / f"sap_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}{Path(file.filename).suffix}"

    try:
        content = await file.read()
        tmp_sap.write_bytes(content)

        # Esegui pipeline — Supabase come DB primario, XLSX sempre come fallback
        use_supabase = is_supabase_configured()
        xlsx_path = _get_xlsx_path()  # sempre disponibile come fallback

        if not use_supabase and xlsx_path is None:
            raise HTTPException(
                status_code=503,
                detail="DB prodotti non disponibile. Configura Supabase o assicurati che il file SLV.xlsx sia presente."
            )

        result = run_pipeline(
            sap_file_path=str(tmp_sap),
            xlsx_db_path=xlsx_path,
            use_supabase=use_supabase,
            output_dir=str(TMP_DIR)
        )

        if not result['success']:
            raise HTTPException(status_code=422, detail=result.get('error', 'Errore pipeline'))

        # Salva storico in Supabase (se configurato)
        session_id = None
        if is_supabase_configured():
            session_id = save_pallet_session(result['metadati'], result)

        # Prepara risposta
        pdf_filename = None
        if result.get('pdf_path') and os.path.exists(result['pdf_path']):
            pdf_filename = Path(result['pdf_path']).name

        # Calcola path immagini relative per il frontend
        img_filenames = []
        for img_path in result.get('img_paths', []):
            if os.path.exists(img_path):
                img_filenames.append(Path(img_path).name)

        # Serializza pallet_list (rimuovi dati troppo pesanti per la response)
        pallet_summary = []
        for p in result['pallet_list']:
            layers_summary = []
            for layer in p['layers']:
                layers_summary.append({
                    "layer_n": layer['layer_n'],
                    "tipo": layer['tipo'],
                    "altezza_mm": layer['altezza_mm'],
                    "altezza_cumulativa_mm": layer['altezza_cumulativa_mm'],
                    "n_scatole": len(layer['scatole']),
                    "scatole": layer['scatole']
                })
            pallet_summary.append({
                "pallet_id": p['pallet_id'],
                "layers": layers_summary,
                "altezza_totale_mm": p['altezza_totale_mm'],
                "n_scatole": p['n_scatole'],
                "fill_pct": p['fill_pct']
            })

        return JSONResponse(content={
            "success": True,
            "session_id": session_id,
            "metadati": result['metadati'],
            "n_pallet": result['n_pallet'],
            "pallet_list": pallet_summary,
            "riepilogo_boxing": result['riepilogo_boxing'],
            "warnings": result['warnings'],
            "report_testo": result['report_testo'],
            "pdf_filename": pdf_filename,
            "img_filenames": img_filenames,
        })

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}\n{traceback.format_exc()}")
    finally:
        # Rimuovi file upload temporaneo
        if tmp_sap.exists():
            tmp_sap.unlink()


@app.get("/api/download-pdf/{filename}")
async def download_pdf(filename: str, background_tasks: BackgroundTasks):
    """
    Scarica il PDF del report dal filesystem .tmp/.
    Il file viene eliminato 60 secondi dopo il download (background task).
    """
    # Sicurezza: no path traversal
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Nome file non valido")

    pdf_path = TMP_DIR / filename
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF non trovato o scaduto")

    if not filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo file PDF ammessi")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/images/{filename}")
async def get_image(filename: str):
    """Restituisce un'immagine PNG generata dalla pipeline."""
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Nome file non valido")
    if not filename.endswith('.png'):
        raise HTTPException(status_code=400, detail="Solo file PNG ammessi")

    img_path = TMP_DIR / "images" / filename
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Immagine non trovata")

    return FileResponse(str(img_path), media_type="image/png")


@app.get("/api/history")
async def get_history(limit: int = 20):
    """Recupera lo storico delle palletizzazioni da Supabase."""
    if not is_supabase_configured():
        return {"configured": False, "history": [], "message": "Supabase non configurato"}

    history = get_pallet_history(limit=limit)
    return {"configured": True, "history": history}


# ─── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
