"""
Tool per inviare notifiche e grafici su Telegram
"""

import requests
from pathlib import Path
from langchain_core.tools import tool
from config import settings


def _bot_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"


@tool
def send_telegram_message(text: str) -> str:
    """
    Invia un messaggio di testo su Telegram.
    Supporta markdown (usa *grassetto*, _corsivo_, `codice`).
    """
    try:
        resp = requests.post(
            _bot_url("sendMessage"),
            json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return "✅ Messaggio Telegram inviato correttamente"
    except Exception as e:
        return f"❌ Errore Telegram: {str(e)}"


@tool
def send_telegram_photo(image_path: str, caption: str = "") -> str:
    """
    Invia un'immagine (grafico) su Telegram con una didascalia opzionale.
    Parametri: image_path (path locale del file), caption (testo sotto l'immagine).
    """
    try:
        path = Path(image_path)
        if not path.exists():
            return f"❌ File non trovato: {image_path}"

        with open(path, "rb") as img:
            resp = requests.post(
                _bot_url("sendPhoto"),
                data={
                    "chat_id": settings.TELEGRAM_CHAT_ID,
                    "caption": caption[:1024],  # limite Telegram
                    #"parse_mode": "Markdown",
                },
                files={"photo": img},
                timeout=30,
            )
        resp.raise_for_status()
        return f"✅ Immagine '{path.name}' inviata su Telegram"
    except Exception as e:
        return f"❌ Errore invio immagine Telegram: {str(e)}"


@tool
def send_telegram_document(file_path: str, caption: str = "") -> str:
    """
    Invia un file generico (es. report .txt, .csv) su Telegram.
    Parametri: file_path (path locale), caption (descrizione).
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"❌ File non trovato: {file_path}"

        with open(path, "rb") as doc:
            resp = requests.post(
                _bot_url("sendDocument"),
                data={
                    "chat_id": settings.TELEGRAM_CHAT_ID,
                    "caption": caption[:1024],
                    "parse_mode": "Markdown",
                },
                files={"document": doc},
                timeout=30,
            )
        resp.raise_for_status()
        return f"✅ Documento '{path.name}' inviato su Telegram"
    except Exception as e:
        return f"❌ Errore invio documento Telegram: {str(e)}"
