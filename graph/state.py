"""
AgentState — lo stato condiviso che scorre tra tutti gli agenti nel grafo.
Ogni agente legge da qui e scrive qui i propri risultati.
"""

from typing import TypedDict, Annotated, Any
from pathlib import Path
import operator


class AgentState(TypedDict):
    # === Input utente ===
    task: str                          # es. "analizza trend vendite"
    file_path: str                     # path del CSV/Excel caricato
    external_api_url: str              # (opzionale) URL API esterna

    # === Dati grezzi (prodotti da ingester) ===
    raw_data: Any                      # DataFrame serializzato come dict
    data_summary: str                  # descrizione testuale del dataset
    data_source: str                   # "csv" | "excel" | "api"

    # === Risultati analisi (prodotti da analyst) ===
    analysis_result: str               # report testuale generato da Claude
    charts: list[str]                  # lista path immagini grafici generati
    anomalies: list[str]               # eventuali anomalie trovate

    # === Notifica (prodotta da notifier) ===
    notification_sent: bool            # True se Telegram ha risposto OK
    notification_error: str            # messaggio di errore se fallisce

    # === Controllo flusso ===
    next_agent: str                    # quale agente eseguire dopo
    errors: Annotated[list[str], operator.add]   # accumula errori (append-only)
    completed_steps: Annotated[list[str], operator.add]  # step completati
