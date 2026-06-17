import os
import json
from config.settings import logger

def _obtener_audio_features_en_lotes(track_ids: list, sp) -> list:
    """
    Función auxiliar para pedir Audio Features a Spotify en lotes de 100 
    (Evita que Spotify rechace la petición por exceso de items).
    """

    all_features = []
    try:
        for i in range(0, len(track_ids), 100):
            lote_ids = track_ids[i:i+100]
            features_lote = sp.audio_features(lote_ids)
            all_features.extend(features_lote)
    except Exception as e:
        logger.warning(f"⚠️  Nota: No se pudo acceder a Audio Features (Error 403). Continuando solo con metadatos básicos.")
        all_features = [{} for _ in track_ids]
    return all_features

def _cargar_base_de_datos(dbpath: str) -> dict:
    """
    Lee el archivo catalog.json si existe, sino, devuelve la estructura base
    """
    if os.path.exists(dbpath):
        try:
            with open(dbpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Base de datos corrupta. Se creará una nueva.")
    return {"canciones": []}