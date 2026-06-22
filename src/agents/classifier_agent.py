from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from config.settings import OPENAI_MODEL

from langchain_openai import ChatOpenAI

class CancionCatalogada(BaseModel):
    id: str
    titulo: str
    artista: str
    origen: str
    ritmo: str = Field(description="Clasificación del ritmo: 'lento', 'medio' o 'rapido'")
    energia_emocional: str = Field(description="Nivel de energía: 'baja' (triste/lenta) o 'alta' (alegre/ruidosa)")
    estados_animo: List[str] = Field(description="Lista de 2 o 3 adjetivos de estado de ánimo (ej: 'melancolico', 'euforico')")
    situaciones_ideales: List[str] = Field(description="Lista de contextos ideales (ej: 'estudiar', 'gimnasio')")

class ColeccionCatalogada(BaseModel):
    canciones: List[CancionCatalogada]

llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.2).with_structured_output(ColeccionCatalogada, include_raw=True)

@traceable(name="Subproceso: Clasificacion con LLM")
def clasificar_con_ia(state: dict, index, tamaño_lote) -> tuple[dict, dict]:
    system_prompt = (
        "Eres un experto psicólogo musical. Analiza los metadatos técnicos de las canciones y catalógalas según su ritmo, vibración emocional y situaciones ideales. Recibirás los datos con llaves acortadas: t=titulo, a=artista, o=orígen y tipo de colección, b=bpm, e=energia, v=valencia, ac=acustica"
    )

    user_prompt = f"Por favor, clasifica la siguiente lista de canciones: \n{state["new_songs"][index:index+tamaño_lote]}"

    completion_raw = llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    resultado_pydantic = completion_raw["parsed"]
    resultado_json = resultado_pydantic.model_dump()

    openai_metadata = completion_raw["raw"].response_metadata.get("token_usage", {})

    info_tokens = {
        "prompt_tokens": openai_metadata.get("prompt_tokens", 0),
        "completion_tokens": openai_metadata.get("completion_tokens", 0),
        "total_tokens": openai_metadata.get("total_tokens", 0),
    }

    return resultado_json, info_tokens

