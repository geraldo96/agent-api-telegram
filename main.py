"""
Data Agent — Entry point CLI
Uso: python main.py
"""

import argparse
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import settings
from graph.supervisor import pipeline

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]🤖 Data Analytics Multi-Agent[/bold cyan]\n"
        "[dim]LangGraph + Claude + FAISS + Telegram[/dim]\n"
        f"[dim]Model: [/dim][yellow]{settings.CLAUDE_MODEL}[/yellow]",
        border_style="cyan"
    ))


def print_summary(result: dict):
    """Stampa il riepilogo finale dell'esecuzione."""
    table = Table(title="📋 Riepilogo Esecuzione", show_header=True)
    table.add_column("Step", style="cyan")
    table.add_column("Stato", style="green")

    steps = result.get("completed_steps", [])
    all_steps = ["ingester", "analyst", "notifier"]
    for step in all_steps:
        status = "✅ Completato" if step in steps else "⏭️  Saltato"
        table.add_row(step.capitalize(), status)

    console.print(table)

    charts = result.get("charts", [])
    if charts:
        console.print(f"\n[green]📈 Grafici generati:[/green]")
        for c in charts:
            console.print(f"   • {c}")

    errors = result.get("errors", [])
    if errors:
        console.print(f"\n[red]❌ Errori:[/red]")
        for e in errors:
            console.print(f"   • {e}")

    notified = result.get("notification_sent", False)
    console.print(f"\n[{'green' if notified else 'yellow'}]"
                  f"{'📨 Telegram: inviato' if notified else '📭 Telegram: non inviato'}[/]")


def run_pipeline(file_path: str = "", api_url: str = "", task: str = ""):
    """Esegue la pipeline completa."""

    # Validazione input
    if not file_path and not api_url:
        console.print("[red]❌ Specifica --file o --api[/red]")
        return

    if file_path and not Path(file_path).exists():
        console.print(f"[red]❌ File non trovato: {file_path}[/red]")
        return

    if not task:
        task = "Analizza i dati, identifica trend e anomalie, genera un report completo"

    # Stato iniziale
    initial_state = {
        "task": task,
        "file_path": file_path,
        "external_api_url": api_url,
        "raw_data": None,
        "data_summary": "",
        "data_source": "",
        "analysis_result": "",
        "charts": [],
        "anomalies": [],
        "notification_sent": False,
        "notification_error": "",
        "next_agent": "",
        "errors": [],
        "completed_steps": [],
    }

    console.print(f"\n[bold]📂 Sorgente:[/bold] {file_path or api_url}")
    console.print(f"[bold]🎯 Task:[/bold] {task}\n")

    # Esegui pipeline
    with console.status("[bold cyan]Pipeline in esecuzione..."):
        result = pipeline.invoke(initial_state)

    console.print("\n")
    print_summary(result)


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Data Analytics Multi-Agent")
    parser.add_argument("--file", "-f", default="", help="Path CSV o Excel")
    parser.add_argument("--api", "-a", default="", help="URL API esterna JSON")
    parser.add_argument("--task", "-t", default="", help="Task da eseguire")
    args = parser.parse_args()

    # Validazione API key
    try:
        settings.validate()
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        console.print("[dim]Crea un file .env partendo da .env.example[/dim]")
        return

    # Modalità interattiva se nessun argomento
    if not args.file and not args.api:
        console.print("\n[yellow]Nessun argomento fornito — modalità interattiva[/yellow]")
        file_path = console.input("[cyan]Path file (CSV/Excel) o lascia vuoto: [/cyan]").strip()
        api_url = console.input("[cyan]URL API esterna o lascia vuoto: [/cyan]").strip() if not file_path else ""
        task = console.input("[cyan]Task da eseguire (Invio per default): [/cyan]").strip()
        run_pipeline(file_path=file_path, api_url=api_url, task=task)
    else:
        run_pipeline(file_path=args.file, api_url=args.api, task=args.task)


if __name__ == "__main__":
    main()