import csv
import html
import json
import os
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "datos")
REPORTS = os.path.join(DATA, "reportes")
TZ = ZoneInfo("America/Argentina/Cordoba")
os.makedirs(DATA, exist_ok=True)
os.makedirs(REPORTS, exist_ok=True)

def ahora():
    return datetime.now(TZ)

def log(*args):
    print(*args, flush=True)

def normalizar_texto(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", value).strip().lower()

def normalizar_email(value):
    value = str(value or "").strip().lower()
    value = value.replace("mailto:", "").split("?", 1)[0]
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", value):
        return ""
    return value

def dominio(email):
    return email.rsplit("@", 1)[1] if "@" in email else ""

def cargar(nombre, default):
    path = os.path.join(DATA, nombre)
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def guardar(nombre, value):
    path = os.path.join(DATA, nombre)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def append_csv(nombre, rows, fields):
    if not rows:
        return
    path = os.path.join(REPORTS, nombre)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def actividad(tipo, **data):
    events = cargar("actividad.json", [])
    events.append({"t": ahora().isoformat(timespec="seconds"), "tipo": tipo, **data})
    guardar("actividad.json", events[-5000:])

def html_text(value):
    return html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
