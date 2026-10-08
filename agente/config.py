import os

def env(name, default=""):
    value = os.getenv(name)
    return default if value is None else value.strip()

WEB = env("WEB", "https://www.pase360.online")
WEB_COMERCIO = env("URL_ADHESION_COMERCIO", f"{WEB}/adherir-comercio")
WEB_GENERADOR = env("URL_ADHESION_GENERADOR", f"{WEB}/adherite-como-generador-de-beneficios")

ODOO_URL = env("ODOO_URL").rstrip("/")
ODOO_DB = env("ODOO_DB")
ODOO_USER = env("ODOO_USER")
ODOO_API_KEY = env("ODOO_API_KEY")
ODOO_COMPANY_ID = int(env("ODOO_COMPANY_ID", "3") or "3")

GEMINI_API_KEY = env("GEMINI_API_KEY")
GEMINI_MODEL = env("GEMINI_MODEL", "gemini-2.5-flash")

OWNER_NAME = env("OWNER_NAME", "Pase 360")
OWNER_EMAIL = env("OWNER_EMAIL")
SENDER_EMAIL = env("SENDER_EMAIL", OWNER_EMAIL)

MODO_PRUEBA = (env("MODO_PRUEBA", "si").lower() not in {"no", "false", "0", "produccion", "producción"}) or (env("PERMITIR_ENVIO_REAL", "no").lower() not in {"si", "sí", "yes", "true", "1"})
META_CONTACTOS = int(env("META_CONTACTOS", "100") or "100")
MAX_CANDIDATOS_SCAN = int(env("MAX_CANDIDATOS_SCAN", "1000") or "1000")

GOOGLE_MAPS_API_KEY = env("GOOGLE_MAPS_API_KEY")
REQUEST_TIMEOUT = int(env("REQUEST_TIMEOUT", "20") or "20")
WEB_TIMEOUT = int(env("WEB_TIMEOUT", "15") or "15")
BBOX = "-31.55,-64.32,-31.28,-64.05"

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
USER_AGENT = "Pase360-Captacion/1.0 (+https://www.pase360.online)"
