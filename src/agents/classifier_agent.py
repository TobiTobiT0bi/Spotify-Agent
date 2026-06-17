from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from config.settings import OPENAI_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_KEY)

class CancionCatalogada(BaseModel):
    id: str
    titulo: str
    artista: str
    coleccion_origen: str
    ritmo: str = Field(description="Clasificación del ritmo: 'lento', 'medio' o 'rapido'")
    energia_emocional: str = Field(description="Nivel de energía: 'baja' (triste/lenta) o 'alta' (alegre/ruidosa)")
    estados_animo: List[str] = Field(description="Lista de 2 o 3 adjetivos de estado de ánimo (ej: 'melancolico', 'euforico')")
    situaciones_ideales: List[str] = Field(description="Lista de contextos ideales (ej: 'estudiar', 'gimnasio')")

class ColeccionCatalogada(BaseModel):
    canciones: List[CancionCatalogada]

def clasificar_con_ia(datos_tecnicos_canciones: list) -> tuple[dict, dict]:
    system_prompt = (
        "Eres un experto psicólogo musical. Analiza los metadatos técnicos de las canciones y catalógalas según su ritmo, vibración emocional y situaciones ideales. Recibirás los datos con llaves acortadas: t=titulo, a=artista, o=colección orígen y tipo de colección, b=bpm, e=energia, v=valencia, ac=acustica"
    )

    user_prompt = f"Por favor, clasifica la siguiente lista de canciones: \n{datos_tecnicos_canciones}"

    completion = client.beta.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=[ 
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=ColeccionCatalogada,
        temperature=0.2,
    )

    resultado_json = completion.choices[0].message.parsed.model_dump()

    info_tokens = {
        "prompt_tokens": completion.usage.prompt_tokens,
        "completion_tokens": completion.usage.completion_tokens,
        "total_tokens": completion.usage.total_tokens,
    }

    return resultado_json, info_tokens

