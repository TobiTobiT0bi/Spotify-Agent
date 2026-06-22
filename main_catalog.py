import json
from config.settings import logger, OPENAI_MODEL
from typing import TypedDict, List, Any
from src.utils.helpers import _cargar_base_de_datos
from src.spotify_client import get_url_metadata
from src.agents.classifier_agent import clasificar_con_ia

from langgraph.graph import StateGraph, START, END

DB_PATH = "data/catalog.json"

class SongState(TypedDict):
    url: str
    raw_songs: List[dict]
    new_songs: List[dict]
    base_datos: dict
    indice_actual: int
    tamaño_lote: int

def filtrar_nuevas(state: SongState) -> dict:
    logger.info(f"Cargando base de datos...")
    base_datos = _cargar_base_de_datos(DB_PATH)
    ids_existentes = {cancion["id"] for cancion in base_datos["canciones"]}
    logger.info(f"Base de datos cargada. Ya tienes {len(ids_existentes)} canciones catalogadas históricamente.")

    logger.info("Extrayendo datos de spotify...")
    raw_songs = get_url_metadata(state["url"])

    new_songs = []
    for cancion in raw_songs:
        if cancion["id"] not in ids_existentes:
            new_songs.append(cancion)

    total_nuevas = len(new_songs)

    if total_nuevas != 0:
        logger.info(f"Total de canciones encontradas: {len(raw_songs)} | Canciones Nuevas: {total_nuevas}")
    else:
        logger.info("🎉 ¡No hay canciones nuevas que procesar! Tu catálogo ya estaba al día.")

    return {
        "raw_songs": raw_songs,
        "new_songs": new_songs,
        "base_datos": base_datos,
    }
    
def clasificar_lote(state: SongState) -> dict:
    total_input_tokens = 0
    total_output_tokens = 0

    index = state["indice_actual"]
    tamaño_lote = state["tamaño_lote"]
    new_songs = state["new_songs"]
    base_datos = state["base_datos"]

    if not new_songs:
        return {}

    total_nuevas = len(new_songs)

    num_lote = (index // tamaño_lote) + 1
    logger.info(f"Enviando lote {num_lote} (Cancion {index} a {min(index + tamaño_lote, total_nuevas)})...")
    try:
        resultado_lote, tokens_lote = clasificar_con_ia(state, index, tamaño_lote)

        base_datos["canciones"].extend(resultado_lote["canciones"])

        total_input_tokens += tokens_lote["prompt_tokens"]
        total_output_tokens += tokens_lote["completion_tokens"]

    except Exception as e:
        logger.error(f"Error Crítico procesando el lote {num_lote}: {e}")       
    
    gran_total_tokens = total_input_tokens + total_output_tokens


    logger.info("=" * 50)
    logger.info("¡PROCESAMIENTO TERMINADO!")
    logger.info(f" Canciones indexadas con éxito: {len(base_datos['canciones'])}")
    logger.info(f" Tokens de Entrada (Input): {total_input_tokens:,}")
    logger.info(f" Tokens de Salida (Output): {total_output_tokens:,}")
    logger.info(f" Total de Tokens Consumidos: {gran_total_tokens:,}")
    logger.info("=" * 50)

    return {
        "base_datos": base_datos,
        "indice_actual": index + tamaño_lote
    }

def decidir_si_continuar(state: SongState):
    if state["indice_actual"] >= len(state["new_songs"]):
        return "terminar"
    return "clasificar_mas"

workflow = StateGraph(SongState)

workflow.add_node("Filtrar_nuevas", filtrar_nuevas)
workflow.add_node("Clasificar_lote", clasificar_lote)

workflow.add_edge(START, "Filtrar_nuevas")
workflow.add_edge("Filtrar_nuevas", "Clasificar_lote")

workflow.add_conditional_edges(
    "Clasificar_lote",
    decidir_si_continuar,
    {
        "clasificar_mas": "Clasificar_lote",
        "terminar": END
    }
)

app = workflow.compile()

if __name__ == "__main__":
    
    url = input("Por favor, ingrese url de playlist/album en spotify: ")

    estado_inicial = {
        "url": url,
        "raw_songs": [],
        "new_songs": [],
        "base_datos": {},
        "indice_actual": 0,
        "tamaño_lote": 50
    }

    estado_final = app.invoke(estado_inicial)

    resultado_bd = estado_final["base_datos"]

    with open("data/catalog.json", "w", encoding="utf-8") as f:
        json.dump(resultado_bd, f, indent=4, ensure_ascii=False)

    logger.info(f"¡Catalogo de {len(resultado_bd.get('canciones', []))} canciones guardado con éxito en data/catalog.json!")