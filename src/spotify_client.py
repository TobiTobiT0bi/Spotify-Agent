import spotipy
from config.settings import logger, SPOTIPY_AUTH
from src.utils.helpers import _obtener_audio_features_en_lotes

sp = spotipy.Spotify(auth_manager=SPOTIPY_AUTH)

def get_url_metadata(url: str) -> list:
    """
    Recibe un link de un álbum de Spotify y extrae los metadatos de todas sus canciones.
    """
    raw_songs = []
    nombre = ""
    tipo = ""
    artistas_str = None

    url_limpia = url.split("?")[0]

    if "album/" in url_limpia:
        tipo = "Album"
        album_id = url_limpia.split("album/")[-1]

        try:
            album_data = sp.album(album_id)
        except Exception as e:
            logger.error(f"No se puede acceder al album. Verifica la URL. Error: {e}")
            return []

        nombre = album_data.get('name', 'Álbum desconocido')
        resultados = album_data.get('tracks', {})

        if resultados and 'items' in resultados:
            raw_songs.extend(resultados['items'])
            while resultados.get('next'):
                resultados = sp.next(resultados)
                raw_songs.extend(resultados['items'])

        artistas_album = [art['name'] for art in album_data.get('artists', [])]
        artistas_str = ", ".join(artistas_album)

    elif "playlist/" in url_limpia:
        tipo = "Playlist"
        playlist_id = url_limpia.split("playlist/")[-1]

        try:   
            playlist_data = sp.playlist(playlist_id)
        except Exception as e:
            logger.error(f"No se puede acceder a la playlist. Verifica la URL. Error: {e}")
            return []

        nombre = playlist_data.get('name', 'Playlist desconocida')
        resultados = playlist_data.get('tracks', {})
        if resultados and 'items' in resultados:
            raw_songs.extend(resultados['items'])
            logger.info(f"🔍 API Spotify: Se recuperaron {len(resultados['items'])} ítems de la página 1.")

            page = 1
            while resultados.get('next'):
                if resultados and 'items' in resultados:
                    raw_songs.extend(resultados['items'])
                    page += 1
                    logger.info(f"🔍 API Spotify: Se recuperaron {len(resultados['items'])} ítems de la página {page}.")

        items = resultados.get('items', [])
        logger.info(f"🔍 API Spotify: Se encontraron {len(items)} ítems crudos en la primera página de la playlist.")

    else:
        raise ValueError("La URL proporcionada no es un álbum ni una playlist válida de Spotify.")

    if not raw_songs:
        logger.warning("⚠️ No se recuperaron canciones crudas de la URL.")
        return []
    
    track_ids = []
    es_playlist = "playlist/" in url

    logger.info("🛠️ Iniciando el análisis y filtrado de canciones...")
    for idx, item in enumerate(raw_songs):
        if es_playlist:
            track_obj = item.get('track', {})
            is_local = item.get('is_local', False)
            t_name = track_obj.get('name', 'Sin Nombre') if track_obj else "Objeto Track Vacío"
            t_id = track_obj.get('id') if track_obj else None
            
            logger.info(f"  👉 Ítem [{idx}]: '{t_name}' | ¿Es Local?: {is_local} | ID: {t_id}")
            
            if is_local or not track_obj:
                logger.warning(f"     ↳ ❌ Saltada: Es un archivo local o no tiene datos de track.")
                continue
            t_id = track_obj.get('id')
        else:
            t_id = item.get('id')
            
        if t_id:
            track_ids.append(t_id)
            
    logger.info(f"📊 Filtrado terminado. IDs válidos para pedir características de audio: {len(track_ids)}")
    
    audio_features_list = _obtener_audio_features_en_lotes(track_ids, sp)

    lista_canciones_tecnica = []
    indice_valido = 0

    for item in raw_songs:
        track = item['track'] if "playlist" in url else item

        if not track or not track.get('id') or (es_playlist and item.get('is_local')):
            continue

        features = audio_features_list[indice_valido] if (indice_valido < len(audio_features_list) and audio_features_list[indice_valido]) else {}
        indice_valido += 1

        artistas_track = [art['name'] for art in track.get('artists', [])]
        artista_final = ", ".join(artistas_track) if artistas_track else artistas_str

        datos_cancion = {
            "id": track['id'],
            "t": track['name'],
            "a": artista_final,
            "o": f"{tipo}: {nombre}",
            "b": features.get("tempo"),
            "e": features.get("energy"),
            "v": features.get("valence"),
            "ac": features.get("acousticness")
        }
        lista_canciones_tecnica.append(datos_cancion)
    
    return lista_canciones_tecnica