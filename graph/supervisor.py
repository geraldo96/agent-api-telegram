"""
Supervisor — costruisce e compila il grafo LangGraph
Definisce il flusso: ingester → analyst → notifier
"""

from langgraph.graph import StateGraph, END

from graph.state import AgentState
from agents.ingester import ingester_agent
from agents.analyst import analyst_agent
from agents.notifier import notifier_agent


def should_continue_after_ingest(state: AgentState) -> str:
    """Routing dopo ingester: vai avanti solo se non ci sono errori critici."""
    if state.get("errors") and not state.get("raw_data"):
        print("⛔ Errore in ingester, terminazione")
        return "end"
    return "analyst"


def should_continue_after_analysis(state: AgentState) -> str:
    """Routing dopo analyst: notifica sempre, anche con errori parziali."""
    if not state.get("analysis_result") and state.get("errors"):
        print("⛔ Analisi fallita, terminazione")
        return "end"
    return "notifier"


def build_graph() -> StateGraph:
    """Costruisce e compila il grafo degli agenti."""

    graph = StateGraph(AgentState)

    # === Aggiungi nodi ===
    graph.add_node("ingester", ingester_agent)
    graph.add_node("analyst", analyst_agent)
    graph.add_node("notifier", notifier_agent)

    # === Entry point ===
    graph.set_entry_point("ingester")

    # === Edge condizionali ===
    graph.add_conditional_edges(
        "ingester",
        should_continue_after_ingest,
        {
            "analyst": "analyst",
            "end": END,
        }
    )

    graph.add_conditional_edges(
        "analyst",
        should_continue_after_analysis,
        {
            "notifier": "notifier",
            "end": END,
        }
    )

    # === Edge finale ===
    graph.add_edge("notifier", END)

    return graph.compile()


# Istanza globale del grafo compilato
pipeline = build_graph()
