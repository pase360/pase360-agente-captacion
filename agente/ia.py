import json
import requests
from . import config as C

def disponible():
    return bool(C.GEMINI_API_KEY)

def revisar(c):
    if not C.GEMINI_API_KEY:
        return {"tipo": "dudoso", "confianza": 0, "motivo": "Gemini no configurado"}
    prompt = f"""
Clasificá este prospecto para Pase 360 en Córdoba Capital.
Opciones: comercio, generador, descartado, dudoso.
Generador: sindicato, gremio, mutual, colegio profesional, club, cámara,
asociación, cooperativa, empresa u organización que puede entregar beneficios
a empleados, afiliados, socios o miembros.
Comercio: negocio que puede ofrecer un beneficio.
No inventes datos.

Nombre: {c.get("name","")}
Dirección: {c.get("direccion","")}
Website: {c.get("website","")}
Tags: {json.dumps(c.get("tags",{}), ensure_ascii=False)}

Respondé SOLO JSON:
{{"tipo":"comercio|generador|descartado|dudoso","confianza":0.0,"motivo":"breve"}}
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{C.GEMINI_MODEL}:generateContent"
    try:
        r = requests.post(url, params={"key": C.GEMINI_API_KEY},
                           json={"contents":[{"parts":[{"text":prompt}]}]},
                           timeout=C.REQUEST_TIMEOUT)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = text.removeprefix("```json").removesuffix("```").strip()
        return json.loads(text)
    except Exception as exc:
        return {"tipo": "dudoso", "confianza": 0, "motivo": f"error IA: {exc}"}
