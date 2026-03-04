"""
Notifier Agent — invia report e grafici su Telegram
"""

from graph.state import AgentState
from tools.telegram_tool import send_telegram_message, send_telegram_photo, send_telegram_document
from pathlib import Path


def notifier_agent(state: AgentState) -> AgentState:
    """
    Nodo LangGraph: invia il report e i grafici su Telegram.
    """
    print("📨 [Notifier] Invio notifiche Telegram...")

    analysis = state.get("analysis_result", "")
    charts = state.get("charts", [])
    task = state.get("task", "")
    errors = state.get("errors", [])

    try:
        # === 1. Messaggio di apertura ===
        header = f"📊 *Report Data Agent*\n\n*Task:* {task}\n\n"

        # Tronca il report se troppo lungo per Telegram (limite 4096 char)
        max_len = 4096 - len(header) - 100
        body = analysis[:max_len] + ("..." if len(analysis) > max_len else "")

        send_telegram_message.invoke({"text": header + body})

        # === 2. Invia grafici ===
        for i, chart_path in enumerate(charts):
            caption = f"📈 Grafico {i+1}/{len(charts)}: {Path(chart_path).stem}"
            result = send_telegram_photo.invoke({
                "image_path": chart_path,
                "caption": caption,
            })
            print(f"   {result}")

        # === 3. Se ci sono stati errori, segnalali ===
        if errors:
            error_text = "⚠️ *Warning — alcuni step hanno avuto errori:*\n"
            error_text += "\n".join(f"• {e}" for e in errors)
            send_telegram_message.invoke({"text": error_text})

        # === 4. Messaggio di chiusura ===
        footer = f"✅ *Analisi completata* — {len(charts)} grafici generati"
        send_telegram_message.invoke({"text": footer})

        print(f"   ✅ Notifiche inviate ({len(charts)} grafici)")

        return {
            **state,
            "notification_sent": True,
            "notification_error": "",
            "completed_steps": ["notifier"],
        }

    except Exception as e:
        error_msg = f"[Notifier] Errore Telegram: {str(e)}"
        print(f"   ❌ {error_msg}")
        return {
            **state,
            "notification_sent": False,
            "notification_error": error_msg,
            "errors": [error_msg],
        }
