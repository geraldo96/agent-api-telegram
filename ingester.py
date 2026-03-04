"""
Ingester Agent — carica dati da CSV, Excel o API esterne
e popola lo stato con il DataFrame e il suo riassunto
"""

import json
import requests
import pandas as pd
from pathlib import Path

from graph.state import AgentState
from tools.file_tools import load_dataframe


def ingester_agent(state: AgentState) -> AgentState:
    """
    Nodo LangGraph: carica i dati e aggiorna lo stato.
    Gestisce: CSV, Excel, API esterna (JSON).
    """
    print("📥 [Ingester] Caricamento dati...")

    file_path = state.get("file_path", "")
    api_url = state.get("external_api_url", "")

    try:
        # === Caso 1: file locale (CSV / Excel) ===
        if file_path:
            df = load_dataframe(file_path)
            source = Path(file_path).suffix.lstrip(".").lower()
            print(f"   ✅ Caricato file: {Path(file_path).name} — {len(df)} righe, {len(df.columns)} colonne")

        # === Caso 2: API esterna ===
        elif api_url:
            print(f"   🌐 Chiamata API: {api_url}")
            resp = requests.get(api_url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Se è una lista di oggetti → DataFrame diretto
            if isinstance(data, list):
                df = pd.DataFrame(data)
            # Se ha una chiave "data" o "results" → cerca dentro
            elif isinstance(data, dict):
                for key in ["data", "results", "records", "items"]:
                    if key in data and isinstance(data[key], list):
                        df = pd.DataFrame(data[key])
                        break
                else:
                    # Ultimo tentativo: appiattisci il dict
                    df = pd.DataFrame([data])
            source = "api"
            print(f"   ✅ Dati API caricati: {len(df)} righe")

        else:
            raise ValueError("Nessun file_path né external_api_url specificato")

        # Genera riassunto testuale per il LLM
        summary = _build_summary(df)

        return {
            **state,
            "raw_data": df.to_dict(orient="records"),
            "data_summary": summary,
            "data_source": source,
            "completed_steps": ["ingester"],
            "errors": [],
        }

    except Exception as e:
        error_msg = f"[Ingester] Errore: {str(e)}"
        print(f"   ❌ {error_msg}")
        return {
            **state,
            "errors": [error_msg],
            "completed_steps": [],
        }


def _build_summary(df: pd.DataFrame) -> str:
    """Costruisce un riassunto leggibile dal LLM."""
    lines = [
        f"Dataset: {len(df)} righe × {len(df.columns)} colonne",
        f"Colonne: {', '.join(df.columns.tolist())}",
        "",
        "Tipi di dati:",
        df.dtypes.to_string(),
        "",
        "Statistiche descrittive:",
        df.describe(include="all").to_string(),
    ]
    nulls = df.isnull().sum()
    if nulls.any():
        lines += ["", "Valori nulli per colonna:", nulls[nulls > 0].to_string()]

    return "\n".join(lines)
