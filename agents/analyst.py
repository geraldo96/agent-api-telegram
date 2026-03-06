"""
Analyst Agent — usa Claude + tool per analizzare i dati e generare grafici
Compatibile con LangChain 1.x (usa bind_tools invece di AgentExecutor)
"""

import pandas as pd
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from graph.state import AgentState
from tools.file_tools import save_report
from tools.chart_tools import plot_line_chart, plot_bar_chart, plot_histogram
from config import settings


ANALYST_SYSTEM_PROMPT = """Sei un esperto analista di dati. Il tuo compito è:
1. Se ricevi Lista Movimenti, raggruppa per categoria e somma gli importi, poi genera un grafico a barre "Spese per Categoria".
2. Prepara un diagramma temporale (line chart) con l'andamento delle spese totali nel tempo (giornaliere).
3. Se ci sono molte transazioni, crea un istogramma con la distribuzione degli importi.
4. Analizzare i dati forniti nel task
5. Identificare trend, pattern e anomalie
6. Generare i grafici più adatti usando i tool disponibili
7. Produrre un report chiaro e strutturato in italiano

Linee guida:
- Utilizza almeno queste Categorie quando raggruppi i movimenti: "Alloggio", "Trasporti & Benzina", "Cibo", "Vario"
- Usa SEMPRE almeno un tool per generare un grafico
- Salva sempre il report con save_report
- Il filename dei grafici deve essere descrittivo (es. "trend_vendite_mensili.png")
- Il report deve avere: Sommario Esecutivo, Analisi Dettagliata, Anomalie, Conclusioni
- Sii preciso con i numeri, cita sempre i valori specifici"""


# Mappa nome tool → funzione
TOOLS_MAP = {
    "plot_line_chart": plot_line_chart,
    "plot_bar_chart": plot_bar_chart,
    "plot_histogram": plot_histogram,
    "save_report": save_report,
}

TOOLS_LIST = list(TOOLS_MAP.values())


def analyst_agent(state: AgentState) -> AgentState:
    """
    Nodo LangGraph: analizza i dati con Claude e genera report + grafici.
    Usa il loop ReAct manuale con bind_tools (compatibile LangChain 1.x)
    """
    print("🔬 [Analyst] Avvio analisi...")

    if state.get("errors"):
        print("   ⚠️  Errori nello stato, skip analisi")
        return state

    # Ricostruisce DataFrame dallo stato
    raw_data = state.get("raw_data", [])
    df = pd.DataFrame(raw_data)
    data_summary = state.get("data_summary", "")
    task = state.get("task", "Analizza i dati")

    # Timestamp per output files
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = str(settings.DATA_OUTPUT_PATH / f"report_{ts}.md")

    # Prepara il messaggio per Claude con i dati
    data_json = df.to_json(orient="records")
    user_message = f"""
Task richiesto: {task}

=== RIASSUNTO DATASET ===
{data_summary}

=== DATI (JSON) ===
{data_json[:8000]}

=== ISTRUZIONI ===
1. Analizza i dati sopra
2. Genera almeno 2 grafici appropriati (usa i tool)
3. Salva il report in: {report_path}
4. Nel report includi i path dei grafici generati
"""

    # Setup LLM con tool binding
    llm = ChatAnthropic(
        model=settings.CLAUDE_MODEL,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=settings.MAX_TOKENS,
        temperature=settings.TEMPERATURE,
    )
    llm_with_tools = llm.bind_tools(TOOLS_LIST)

    # Messaggi conversazione
    messages = [
        SystemMessage(content=ANALYST_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    try:
        # === Loop ReAct manuale ===
        for iteration in range(settings.AGENT_MAX_ITERATIONS):
            print(f"   🔄 Iterazione {iteration + 1}...")

            response = llm_with_tools.invoke(messages)
            messages.append(response)

            # Se Claude non chiama tool → ha finito
            if not response.tool_calls:
                print("   ✅ Claude ha completato l'analisi")
                break

            # Esegui i tool chiamati da Claude
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                print(f"   🔧 Tool: {tool_name}({list(tool_args.keys())})")

                if tool_name in TOOLS_MAP:
                    tool_result = TOOLS_MAP[tool_name].invoke(tool_args)
                else:
                    tool_result = f"Tool '{tool_name}' non trovato"

                print(f"   📤 Risultato: {str(tool_result)[:100]}")

                # Aggiungi risultato tool ai messaggi
                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_id,
                ))

        # Estrai testo finale dalla risposta
        analysis_text = response.content
        if isinstance(analysis_text, list):
            analysis_text = " ".join(
                block.get("text", "") for block in analysis_text
                if isinstance(block, dict)
            )

        # Raccogli grafici generati negli ultimi 5 minuti
        charts = [
            str(p) for p in settings.DATA_OUTPUT_PATH.glob("*.png")
            if p.stat().st_mtime > (datetime.now().timestamp() - 300)
        ]

        print(f"   ✅ Analisi completata — {len(charts)} grafici generati")

        return {
            **state,
            "analysis_result": analysis_text,
            "charts": charts,
            "completed_steps": ["analyst"],
            "errors": [],
        }

    except Exception as e:
        error_msg = f"[Analyst] Errore: {str(e)}"
        print(f"   ❌ {error_msg}")
        return {
            **state,
            "errors": [error_msg],
        }