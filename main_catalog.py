import json
from config.settings import logger, OPENAI_MODEL
from src.utils.helpers import _cargar_base_de_datos
from src.spotify_client import get_url_metadata
from src.agents.classifier_agent import clasificar_con_ia

DB_PATH = "data/catalog.json"

def procesar_url_spotify(url: str, tamaño_lote: int = 50) -> dict:
    logger.info(f"Cargando base de datos...")
    base_datos = _cargar_base_de_datos(DB_PATH)
    ids_existentes = {cancion["id"] for cancion in base_datos["canciones"]}
    logger.info(f"Base de datos cargada. Ya tienes {len(ids_existentes)} canciones catalogadas históricamente.")

    logger.info("Extrayendo datos de spotify...")
    datos_spotify = get_url_metadata(url)
    total_encontradas = len(datos_spotify)
    logger.info(f"Total de canciones encontradas: {total_encontradas}")

    canciones_nuevas = []
    for cancion in datos_spotify:
        if cancion["id"] not in ids_existentes:
            canciones_nuevas.append(cancion)

    total_nuevas = len(canciones_nuevas)

    if total_nuevas == 0:
        logger.info("🎉 ¡No hay canciones nuevas que procesar! Tu catálogo ya estaba al día.")
        return base_datos
    
    total_input_tokens = 0
    total_output_tokens = 0

    logger.info(f"Procesando {total_nuevas} canciones nuevas con f{OPENAI_MODEL} en lotes de {tamaño_lote}...")
    for i in range(0, total_nuevas, tamaño_lote):
        lote = canciones_nuevas[i:i+tamaño_lote]
        num_lote = (i // tamaño_lote) + 1

        logger.info(f"Enviando lote {num_lote} (Cancion {i} a {min(i + tamaño_lote, total_nuevas)})...")
        try:
            resultado_lote, tokens_lote = clasificar_con_ia(lote)

            base_datos["canciones"].extend(resultado_lote["canciones"])

            total_input_tokens += tokens_lote["prompt_tokens"]
            total_output_tokens += tokens_lote["completion_tokens"]

        except Exception as e:
            logger.error(f"Error Crítico procesando el lote {num_lote}: {e}")
            continue        
    
    gran_total_tokens = total_input_tokens + total_output_tokens


    logger.info("=" * 50)
    logger.info("¡PROCESAMIENTO TERMINADO!")
    logger.info(f" Canciones indexadas con éxito: {len(base_datos['canciones'])}")
    logger.info(f" Tokens de Entrada (Input): {total_input_tokens:,}")
    logger.info(f" Tokens de Salida (Output): {total_output_tokens:,}")
    logger.info(f" Total de Tokens Consumidos: {gran_total_tokens:,}")
    logger.info("=" * 50)

    return base_datos

if __name__ == "__main__":
    
    url = input("Por favor, ingrese url de playlist/album en spotify: ")

    resultado = procesar_url_spotify(url)

    with open("data/catalog.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)

    logger.info(f"¡Catalogo de {len(resultado['canciones'])} canciones guardado con éxito en data/catalog.json!")