"""
Tool per lettura/scrittura file CSV ed Excel
"""

import pandas as pd
from pathlib import Path
from langchain_core.tools import tool


@tool
def read_csv(file_path: str) -> str:
    """Legge un file CSV e restituisce un riassunto dei dati."""
    try:
        df = pd.read_csv(file_path)
        return _summarize_df(df, file_path)
    except Exception as e:
        return f"Errore lettura CSV: {str(e)}"


@tool
def read_excel(file_path: str) -> str:
    """Legge un file Excel (.xlsx) e restituisce un riassunto dei dati."""
    try:
        df = pd.read_excel(file_path)
        return _summarize_df(df, file_path)
    except Exception as e:
        return f"Errore lettura Excel: {str(e)}"


@tool
def save_report(content: str, output_path: str) -> str:
    """Salva un report testuale su file .txt o .md"""
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ Report salvato in: {output_path}"
    except Exception as e:
        return f"Errore salvataggio report: {str(e)}"


def _summarize_df(df: pd.DataFrame, file_path: str) -> str:
    """Genera una descrizione testuale del DataFrame per il LLM."""
    lines = [
        f"File: {Path(file_path).name}",
        f"Righe: {len(df)} | Colonne: {len(df.columns)}",
        f"Colonne: {', '.join(df.columns.tolist())}",
        f"Tipi:\n{df.dtypes.to_string()}",
        f"\nPrime 3 righe:\n{df.head(3).to_string()}",
        f"\nStatistiche:\n{df.describe().to_string()}",
    ]
    null_counts = df.isnull().sum()
    if null_counts.any():
        lines.append(f"\nValori nulli:\n{null_counts[null_counts > 0].to_string()}")
    return "\n".join(lines)


def load_dataframe(file_path: str) -> pd.DataFrame:
    """Carica un file in un DataFrame (uso interno, non tool)."""
    ext = Path(file_path).suffix.lower()
    if ext == ".csv":
        return pd.read_csv(file_path)
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Formato non supportato: {ext}")
