# Info Segugio

Selfwork **AI Search** del modulo Coding AI Agents (Aulab): replica del progetto Info Segugio visto nella video-lezione.

Info Segugio è un agente di ricerca web con interfaccia Chainlit:

```
Domanda utente
   -> Web Search Query Optimiser (LLM)
   -> Web Search (Tavily)
   -> Create Summary (LLM)
   -> Reflect on Next Web Search Query (LLM) -> torna a Web Search
      (il ciclo si ferma dopo max_cycles = 3 ricerche: web search counter)
   -> Riassunto finale con le fonti consultate
```

## Requisiti

- Python 3.13
- Poetry (https://python-poetry.org/)
- una chiave OpenAI e una chiave Tavily (https://tavily.com, piano gratuito)

## Installazione

```powershell
poetry install
copy .env.example .env
```

Nel file `.env` vanno inserite le proprie chiavi:

```
OPENAI_API_KEY=...
TAVILY_API_KEY=...
```

Il file `.env` è escluso da git tramite `.gitignore`, quindi le chiavi non vengono mai pubblicate su GitHub.

Con la configurazione predefinita (`info_segugio/config.py`) si usano i modelli OpenAI `gpt-4o` e `gpt-4o-mini`. Per usare Ollama in locale basta attivare la classe `Config` commentata.

## Avvio

```powershell
poetry run chainlit run info_segugio/__init__.py -w
```

L'applicazione si apre su http://localhost:8000.

## Struttura

- `info_segugio/config.py`: configurazione dei modelli e chiavi lette da `.env`.
- `info_segugio/prompts.py`: prompt per la query ottimizzata (`query_writer_instructions`), il riassunto (`summarizer_instructions`) e la riflessione sulla prossima ricerca (`reflection_instructions`).
- `info_segugio/__init__.py`:
  - `llm()`: chiamata al modello con messaggio `developer` e `user`, risposta JSON o testo;
  - `optimize_search_query()`: genera query, aspetto e motivazione;
  - `web_research()`: ricerca con Tavily (5 risultati) e formattazione delle fonti;
  - `summarize_sources()`: crea o estende il riassunto;
  - `reflect_on_summary()`: trova la lacuna di conoscenza e la domanda di approfondimento;
  - `main()`: ciclo di ricerca con contatore e messaggi di avanzamento in chat.
- `public/`: personalizzazioni grafiche (tema `theme.json`, `app.css`, logo chiaro e scuro, favicon, avatar `segugio_assistant` e `system_assistant`).
- `.chainlit/config.toml`: nome dell'app e foglio di stile personalizzato.
