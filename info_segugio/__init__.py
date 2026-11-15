import json

import chainlit as cl
from config import Config
from openai import OpenAI
from prompts import query_writer_instructions, reflection_instructions, summarizer_instructions
from tavily import TavilyClient

# Inizializzazione del client OpenAI con le configurazioni
client = OpenAI(base_url=Config.AI_API_URL, api_key=Config.AI_API_KEY)


# Funzione per interagire con l'AI
def llm(developer_prompt, user_prompt, temperature=0, response_format={"type": "json_object"}):
    response = client.chat.completions.create(
        model=Config.LLM_MODEL_LOW,
        messages=[
            {"role": "developer", "content": developer_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        response_format=response_format,
    )
    return response.choices[0].message.content


# Genera una query ottimizzata per la ricerca web
def optimize_search_query(research_topic):
    formatted_instructions = query_writer_instructions.format(research_topic=research_topic)
    result = llm(formatted_instructions, "Genera una query per la ricerca web:")
    obj = json.loads(result)
    print(obj)
    return obj


def _format_content(result):
    return f"""
Fonte {result['title']}:\n===\n
URL: {result['url']}\n===\n
Contenuto più rilevante: {result['content']}\n===\n
"""


# Esegue la ricerca web con Tavily
def web_research(search_query):
    max_results = 5
    include_raw = False

    tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY)
    response = tavily_client.search(
        query=search_query,
        max_results=max_results,
        include_raw_content=include_raw,
    )
    results = response.get("results", [])
    titles = [f"{result['title']} ({result['url']})" for result in results]
    contents = [_format_content(result) for result in results]

    return {
        "sources_gathered": titles,
        "web_research_results": contents,
    }


# Sintetizza i risultati della ricerca in un riassunto coerente
def summarize_sources(web_research_results, research_topic, running_summary=None):
    current_results = "\n".join(web_research_results)

    if running_summary:
        message = (
            f"Estendi questo riassunto: {running_summary}\n\n"
            f"Con questi nuovi risultati: {current_results} "
            f"Sul tema: {research_topic}"
        )
    else:
        message = (
            f"Genera un riassunto di questi risultati: {current_results} "
            f"Sul tema: {research_topic}"
        )

    output_formatter = None  # Vogliamo del testo semplice
    return llm(summarizer_instructions, message, 0.2, output_formatter)


# Analizza il riassunto corrente e genera una domanda di approfondimento
def reflect_on_summary(research_topic, running_summary):
    result = llm(
        reflection_instructions.format(research_topic=research_topic),
        f"Identifica una lacuna e genera una domanda per la prossima ricerca basandoti su: {running_summary}",
    )
    return json.loads(result)


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Ricerca sul web",
            message="Quali sono le ultime novità sugli agenti di intelligenza artificiale?",
        ),
    ]


@cl.on_message
async def main(message: cl.Message):
    if not Config.AI_API_KEY or not Config.TAVILY_API_KEY:
        await cl.Message(
            author="system_assistant",
            content="Mancano le chiavi API: inserisci OPENAI_API_KEY e TAVILY_API_KEY nel file .env",
        ).send()
        return

    # Fase 1: Generazione della query iniziale
    user_message = message.content
    osq = optimize_search_query(user_message)

    # feedback per l'utente
    query, aspect, reason = osq["query"], osq["aspect"], osq["reason"]
    await cl.Message(
        author="system_assistant",
        content=f"Query di ricerca ottimizzata:\n {query}.\n Mi sono soffermato su questo aspetto:\n {aspect}.\n Per questo motivo:\n {reason}.\n",
    ).send()

    # Fase 2: Ciclo di ricerca e approfondimento
    running_summary = None
    max_cycles = 3
    web_search_counter = 0
    all_sources = []

    while True:
        web_search_counter += 1

        # Esegui la ricerca web
        results = web_research(query)
        titles = "\n".join(results["sources_gathered"])
        all_sources.extend(results["sources_gathered"])

        # feedback per l'utente
        await cl.Message(
            author="system_assistant",
            content=f"Ricerca {web_search_counter} di {max_cycles}. Fonti trovate:\n{titles}",
        ).send()

        # Genera o aggiorna il riassunto
        summary = summarize_sources(results["web_research_results"], query, running_summary)
        running_summary = summary

        # feedback per l'utente
        await cl.Message(author="system_assistant", content=f"Riassunto attuale: {summary}").send()

        # Controllo del contatore delle ricerche web
        if web_search_counter >= max_cycles:
            break

        # Genera la prossima query di approfondimento
        ros = reflect_on_summary(query, summary)
        query = ros.get("domanda_approfondimento", f"Dimmi di più su {query}")
        lacuna_conoscenza = ros.get("lacuna_conoscenza", "")

        # feedback per l'utente
        await cl.Message(
            author="system_assistant",
            content=f"Prossima ricerca:\n {query}.\n Mi sono soffermato su questo perche':\n {lacuna_conoscenza}",
        ).send()

    # Fase 3: Riassunto finale con le fonti consultate
    sources = "\n".join(f"- {source}" for source in all_sources)
    await cl.Message(
        author="segugio_assistant",
        content=f"## Riassunto finale\n\n{running_summary}\n\n### Fonti consultate\n{sources}",
    ).send()
