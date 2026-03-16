"""
supabase_client.py
Client Supabase per lettura DB prodotti e scrittura storico palletizzazioni.
Usa fallback XLSX locale se non configurato.
"""

import os
from typing import Optional
from dotenv import load_dotenv

from pathlib import Path

# Path assoluto al .env — robusto anche con uvicorn --reload e sottoprocessi
_ENV_PATH = Path(__file__).resolve().parent / '.env'
load_dotenv(_ENV_PATH)


def _get_supabase_url() -> str:
    """Lettura lazy — rilegge sempre dall'ambiente per robustezza con --reload."""
    return os.environ.get("SUPABASE_URL", "")


def _get_supabase_key() -> str:
    """Lettura lazy — rilegge sempre dall'ambiente per robustezza con --reload."""
    return os.environ.get("SUPABASE_KEY", "")


def is_supabase_configured() -> bool:
    url = _get_supabase_url()
    key = _get_supabase_key()
    return bool(url and key and "YOUR_PROJECT_ID" not in url)


def get_supabase_client():
    """Ritorna il client Supabase se configurato, altrimenti None."""
    if not is_supabase_configured():
        return None
    try:
        from supabase import create_client
        return create_client(_get_supabase_url(), _get_supabase_key())
    except Exception as e:
        print(f"WARN Errore connessione Supabase: {e}")
        return None


def save_pallet_session(metadati: dict, result: dict) -> Optional[str]:
    """
    Salva una sessione di palletizzazione in Supabase (tabella pallet_history).
    Ritorna l'ID del record inserito, o None se non disponibile.
    """
    client = get_supabase_client()
    if client is None:
        return None

    try:
        import json
        # Serializza pallet_list rimuovendo dati troppo voluminosi
        pallet_summary = [
            {
                "pallet_id": p['pallet_id'],
                "n_layers": len(p['layers']),
                "n_scatole": p['n_scatole'],
                "altezza_totale_mm": p['altezza_totale_mm'],
                "fill_pct": p['fill_pct']
            }
            for p in result.get('pallet_list', [])
        ]

        record = {
            "cliente": metadati.get("cliente", ""),
            "nome_cliente": metadati.get("nome_cliente", ""),
            "numero_ordine": metadati.get("numero_ordine", ""),
            "data_ordine": metadati.get("data_ordine", ""),
            "n_pallet": result.get("n_pallet", 0),
            "n_scatole": result.get("riepilogo_boxing", {}).get("n_scatole_totali", 0),
            "result_json": json.dumps(pallet_summary, ensure_ascii=False),
            "warnings_json": json.dumps(result.get("warnings", {}), ensure_ascii=False),
        }

        response = client.table("pallet_history").insert(record).execute()
        if response.data:
            return str(response.data[0].get("id", ""))
    except Exception as e:
        print(f"⚠️  Errore scrittura Supabase: {e}")

    return None


def get_pallet_history(limit: int = 20) -> list:
    """Recupera lo storico palletizzazioni da Supabase."""
    client = get_supabase_client()
    if client is None:
        return []

    try:
        response = (client.table("pallet_history")
                    .select("*")
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute())
        return response.data or []
    except Exception as e:
        print(f"⚠️  Errore lettura storico Supabase: {e}")
        return []
