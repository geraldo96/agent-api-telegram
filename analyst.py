"""
Analyst Agent — usa Claude + tool per analizzare i dati e generare grafici
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from graph.state import AgentState
from tools.file_tools import save_report
from tools.chart_tools import plot_line_chart, plot_bar_chart, plot_histogram
from config import settings


ANALYST_SYSTEM_PROMPT = """Sei un esperto analista di dati. Il tuo compito è:
1. Analizzare i dati forniti nel task
2. Identificare trend, pattern e anomalie
3. Generare i grafici più adatti usando i tool disponibili
4. Produrre un report chiaro e strutturato in italiano

Linee guida:
- Usa SEMPRE almeno un tool per generare un grafico
- Salva sempre il report con save_report
- Il filename dei grafici deve essere descrittivo (es. "trend_vendite_mensili.png")
- Il report deve avere: Sommario Esecutivo, Analisi Dettagliata, Anomalie, Conclusioni
- Sii preciso con i numeri, cita sempre i valori specifici"""


def analyst_agent(state: AgentState) -> AgentState:
    """
    Nodo LangGraph: analizza i dati con Claude e genera report + grafici.
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

=== DATI (JSON, prime 100 righe) ===
{data_json[:8000]}  

=== ISTRUZIONI ===
1. Analizza i dati sopra
2. Genera almeno 2 grafici appropriati (usa i tool)
3. Salva il report in: {report_path}
4. Nel report includi i path dei grafici generati
"""

    # Setup LLM e tools
    llm = ChatAnthropic(
        model=settings.CLAUDE_MODEL,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=settings.MAX_TOKENS,
        temperature=settings.TEMPERATURE,
    )

    tools = [plot_line_chart, plot_bar_chart, plot_histogram, save_report]

    prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYST_SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=settings.AGENT_MAX_ITERATIONS,
        verbose=True,
        handle_parsing_errors=True,
    )

    try:
        result = executor.invoke({"input": user_message})
        analysis_text = result.get("output", "")

        # Raccogli i grafici generati (cerca nella output folder)
        charts = [
            str(p) for p in settings.DATA_OUTPUT_PATH.glob("*.png")
            if p.stat().st_mtime > (datetime.now().timestamp() - 300)  # ultimi 5 min
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
