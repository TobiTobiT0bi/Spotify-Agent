import os
import pathlib
import logging
import dotenv
import spotipy.oauth2 as spoti
from colorlog import ColoredFormatter

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

SPOTIPY_AUTH = spoti.SpotifyOAuth(
    client_id = os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret= os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri= os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="playlist-read-private playlist-read-collaborative",
)

logger = logging.getLogger("spotify_agent")
logger.setLevel(logging.INFO)

if not logger.handlers:
    ch = logging.StreamHandler()

    formatter = ColoredFormatter("%(log_color)s%(asctime)s - %(levelname)s - %(message)s", datefmt='%H:%M:%S')
    ch.setFormatter(formatter)

    logger.addHandler(ch)