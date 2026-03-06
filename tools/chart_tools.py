"""
Tool per generazione grafici con matplotlib
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # backend non-interattivo (no GUI)
import matplotlib.pyplot as plt
from pathlib import Path
from langchain_core.tools import tool
from config import settings

def _parse_json(data_json: str) -> pd.DataFrame:
    import json
    data_json = data_json.strip()
    parsed = json.loads(data_json)
    if isinstance(parsed, list):
        return pd.DataFrame(parsed)
    if isinstance(parsed, dict):
        for key in ["records", "data", "items", "results"]:
            if key in parsed and isinstance(parsed[key], list):
                return pd.DataFrame(parsed[key])
        if "columns" in parsed and "data" in parsed:
            return pd.DataFrame(parsed["data"], columns=parsed["columns"])
        return pd.DataFrame([parsed])
    raise ValueError(f"Formato non riconosciuto")

def _save_fig(fig, filename: str) -> str:
    """Salva figura e restituisce il path."""
    out_path = settings.DATA_OUTPUT_PATH / filename
    fig.savefig(out_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return str(out_path)


@tool
def plot_line_chart(
    data_json: str,
    x_col: str,
    y_col: str,
    title: str = "Trend",
    filename: str = "line_chart.png"
) -> str:
    """
    Genera un grafico a linee da dati JSON (records orient).
    Parametri: data_json (DataFrame in JSON), x_col, y_col, title, filename.
    """
    try:
        df = _parse_json(data_json)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df[x_col], df[y_col], marker="o", linewidth=2)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        path = _save_fig(fig, filename)
        return f"✅ Grafico salvato: {path}"
    except Exception as e:
        return f"Errore generazione grafico: {str(e)}"


@tool
def plot_bar_chart(
    data_json: str,
    x_col: str,
    y_col: str,
    title: str = "Confronto",
    filename: str = "bar_chart.png"
) -> str:
    """
    Genera un grafico a barre da dati JSON.
    Parametri: data_json (DataFrame in JSON), x_col, y_col, title, filename.
    """
    try:
        df = _parse_json(data_json)
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(df[x_col], df[y_col], color="steelblue", edgecolor="white")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.grid(True, axis="y", alpha=0.3)
        # Etichette sopra le barre
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h,
                    f"{h:.1f}", ha="center", va="bottom", fontsize=9)
        plt.xticks(rotation=45)
        plt.tight_layout()
        path = _save_fig(fig, filename)
        return f"✅ Grafico salvato: {path}"
    except Exception as e:
        return f"Errore generazione grafico: {str(e)}"


@tool
def plot_histogram(
    data_json: str,
    col: str,
    bins: int = 20,
    title: str = "Distribuzione",
    filename: str = "histogram.png"
) -> str:
    """
    Genera un istogramma per una colonna numerica.
    Parametri: data_json, col (colonna da analizzare), bins, title, filename.
    """
    try:
        df = _parse_json(data_json)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(df[col].dropna(), bins=bins, color="steelblue",
                edgecolor="white", alpha=0.8)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel(col)
        ax.set_ylabel("Frequenza")
        ax.grid(True, axis="y", alpha=0.3)
        plt.tight_layout()
        path = _save_fig(fig, filename)
        return f"✅ Istogramma salvato: {path}"
    except Exception as e:
        return f"Errore generazione istogramma: {str(e)}"
