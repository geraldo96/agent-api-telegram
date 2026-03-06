# Data Analytics Multi-Agent System
## Stack: LangGraph + Claude (Anthropic) + Telegram

### Setup rapido

```bash
# 1. Clona e installa
pip install -r requirements.txt

# 2. Configura variabili d'ambiente
cp .env.example .env
# → Compila ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# 3. Esegui con un CSV
python main.py --file data/input/vendite.csv --task "analizza trend mensile"

# 4. Esegui con API esterna
python main.py --api https://api.example.com/sales --task "trova anomalie"

# 5. Modalità interattiva
python main.py
```

### Architettura

```
main.py
  └── graph/supervisor.py        # LangGraph pipeline
        ├── agents/ingester.py   # Carica CSV/Excel/API
        ├── agents/analyst.py    # Analisi + grafici (Claude)
        └── agents/notifier.py   # Invia su Telegram
```

### Flusso dati

```
Input (file/api)
  → [Ingester]  carica → DataFrame + summary
  → [Analyst]   analizza → report .md + grafici .png
  → [Notifier]  invia → Telegram (testo + immagini)
```

### Roadmap

#### Fase 1 — Fondamenta ✅
- [x] LangGraph multi-agent pipeline
- [x] Claude (Anthropic) come LLM
- [x] Supporto CSV / Excel / API esterne
- [x] Notifiche Telegram (testo + grafici)
- [x] CLI con modalità interattiva
- [x] Aggiunto il tool per gestione di lista movimenti

#### Fase 2 — Evoluzione architetturale
- [ ] **MCP (Model Context Protocol)** — i tool diventano MCP Server
      standard richiamabili da qualsiasi LLM compatibile
- [ ] **A2A (Agent to Agent Protocol)** — ogni agente diventa
      un microservizio indipendente comunicante via protocollo standard

#### Fase 3 — Consolidamento
- [ ] Supporto database SQL (SQLite / PostgreSQL)
- [ ] Scheduler (cron) per analisi automatiche periodiche

#### Fase 4 — Livelli superiori
- [ ] FastAPI wrapper per esporre la pipeline come REST API
- [ ] Streamlit dashboard che chiama la FastAPI
- [ ] Documentazione API con Swagger UI

### Protocolli — riferimenti

| Protocollo | Autore | Scopo |
|---|---|---|
| [MCP](https://modelcontextprotocol.io) | Anthropic | Collega LLM ↔ Tool in modo standard |
| [A2A](https://google.github.io/A2A) | Google | Collega Agente ↔ Agente in modo standard |
