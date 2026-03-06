"""
Tool dedicato per leggere estratti conto bancari in formato Excel.
Riconosce automaticamente file con nomi tipo:
- movimenti_*.xlsx
- lista_movimenti_*.xlsx
- estratto_conto_*.xlsx
- movimenti_carta_*.xlsx
"""

import re
import warnings
import pandas as pd
from pathlib import Path
from langchain_core.tools import tool

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def _find_header_row(df_raw: pd.DataFrame) -> int:
    """
    Cerca automaticamente la riga che contiene l'header dei movimenti.
    Cerca 'Data contabile' o 'Data' + 'Descrizione' come indicatori.
    """
    for i, row in df_raw.iterrows():
        values = [str(v).strip() for v in row.values if str(v) != "nan"]
        if "Data contabile" in values or (
            any("data" in v.lower() for v in values) and
            any("descr" in v.lower() for v in values)
        ):
            return i
    raise ValueError("Header movimenti non trovato nel file")


def _extract_metadata(df_raw: pd.DataFrame) -> dict:
    """
    Estrae i metadati dall'intestazione del file:
    intestatario, numero carta, periodo, sbilancio.
    """
    meta = {}
    for _, row in df_raw.iterrows():
        vals = list(row.values)
        for j, v in enumerate(vals):
            sv = str(v).strip()
            if sv == "Intestatario carta:" and j + 1 < len(vals):
                meta["intestatario"] = str(vals[j + 1]).strip()
            if sv == "Numero carta:" and j + 1 < len(vals):
                meta["numero_carta"] = str(vals[j + 1]).strip()
            if sv == "Periodo:" and j + 1 < len(vals):
                meta["periodo"] = str(vals[j + 1]).strip()
            if sv == "Sbilancio alla data:" and j + 2 < len(vals):
                try:
                    meta["sbilancio"] = float(vals[j + 2])
                except (ValueError, TypeError):
                    pass
            if sv == "I movimenti selezionati sono:" and j + 1 < len(vals):
                try:
                    meta["n_movimenti"] = int(vals[j + 1])
                except (ValueError, TypeError):
                    pass
    return meta


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pulisce il DataFrame dei movimenti:
    - rimuove righe vuote
    - normalizza date
    - aggiunge colonne Importo e Tipo
    """
    # Rimuove righe completamente vuote
    df = df.dropna(how="all").reset_index(drop=True)

    # Normalizza nomi colonne
    df.columns = [str(c).strip() for c in df.columns]

    # Colonna Data contabile → datetime
    date_col = next((c for c in df.columns if "data contabile" in c.lower()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])  # rimuove righe senza data

    # Colonne importi
    addebiti_col  = next((c for c in df.columns if "addebiti" in c.lower() and "valuta" not in c.lower()), None)
    accrediti_col = next((c for c in df.columns if "accrediti" in c.lower() and "valuta" not in c.lower()), None)

    if addebiti_col and accrediti_col:
        df[addebiti_col]  = pd.to_numeric(df[addebiti_col],  errors="coerce").fillna(0)
        df[accrediti_col] = pd.to_numeric(df[accrediti_col], errors="coerce").fillna(0)
        df["Importo"] = df[addebiti_col] - df[accrediti_col]
        df["Tipo"]    = df.apply(
            lambda r: "Addebito" if r[addebiti_col] > 0 else "Accredito", axis=1
        )

    return df


def is_bank_statement(file_path: str) -> bool:
    """
    Controlla se il nome del file è riconducibile a un estratto conto.
    Usato dall'ingester per decidere quale tool usare.
    """
    name = Path(file_path).stem.lower()
    keywords = [
        "moviment", "estratto", "lista_mov", "movimenti_carta",
        "bank", "statement", "conto", "transaz"
    ]
    return any(k in name for k in keywords)


@tool
def read_bank_statement(file_path: str) -> str:
    """
    Legge un estratto conto bancario in formato Excel (.xlsx).
    Riconosce automaticamente l'intestazione, salta le righe di metadati,
    e restituisce un riassunto strutturato con statistiche sui movimenti.
    Usalo quando il file contiene movimenti bancari o transazioni con carta.
    """
    try:
        # Leggi file raw senza header
        df_raw = pd.read_excel(file_path, header=None)

        # Estrai metadati intestazione
        meta = _extract_metadata(df_raw)

        # Trova riga header automaticamente
        header_row = _find_header_row(df_raw)

        # Leggi movimenti con header corretto
        df = pd.read_excel(file_path, skiprows=header_row, header=0)
        df = _clean_dataframe(df)

        # Calcola statistiche
        addebiti  = df[df["Tipo"] == "Addebito"]["Importo"].sum()  if "Tipo" in df.columns else 0
        accrediti = df[df["Tipo"] == "Accredito"]["Importo"].abs().sum() if "Tipo" in df.columns else 0
        n_mov     = len(df)

        # Top 5 spese
        top_spese = ""
        if "Importo" in df.columns:
            top = df[df["Tipo"] == "Addebito"].nlargest(5, "Importo")
            top_spese = "\n".join(
                f"  - {row['Descrizione']}: €{row['Importo']:.2f}"
                for _, row in top.iterrows()
            )

        # Costruisci summary
        lines = ["=== ESTRATTO CONTO ==="]
        if meta.get("intestatario"): lines.append(f"Intestatario: {meta['intestatario']}")
        if meta.get("numero_carta"): lines.append(f"Carta: {meta['numero_carta']}")
        if meta.get("periodo"):      lines.append(f"Periodo: {meta['periodo']}")
        if meta.get("sbilancio"):    lines.append(f"Sbilancio: €{meta['sbilancio']:.2f}")

        lines += [
            "",
            f"=== MOVIMENTI ({n_mov} transazioni) ===",
            f"Totale addebiti:  €{addebiti:.2f}",
            f"Totale accrediti: €{accrediti:.2f}",
            "",
            "=== TOP 5 SPESE ===",
            top_spese,
            "",
            "=== COLONNE DISPONIBILI ===",
            ", ".join(df.columns.tolist()),
            "",
            "=== PRIME 10 RIGHE ===",
            df.head(10).to_string(index=False),
        ]

        return "\n".join(lines)

    except Exception as e:
        return f"Errore lettura estratto conto: {str(e)}"


def load_bank_statement_df(file_path: str) -> pd.DataFrame:
    """
    Carica l'estratto conto come DataFrame pulito (uso interno, non tool).
    """
    df_raw = pd.read_excel(file_path, header=None)
    header_row = _find_header_row(df_raw)
    df = pd.read_excel(file_path, skiprows=header_row, header=0)
    return _clean_dataframe(df)