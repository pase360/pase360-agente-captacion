import time
import requests
from . import config as C
from .util import log

OVERPASS_QUERY = f"""
[out:json][timeout:60];
(
  nwr["name"]["shop"]({C.BBOX});
  nwr["name"]["craft"]({C.BBOX});
  nwr["name"]["amenity"]({C.BBOX});
  nwr["name"]["office"]({C.BBOX});
  nwr["name"]["leisure"]({C.BBOX});
  nwr["name"]["tourism"]({C.BBOX});
  nwr["name"]["club"]({C.BBOX});
);
out center tags;
"""

def _post(url):
    r = requests.post(
        url,
        data={"data": OVERPASS_QUERY},
        headers={"User-Agent": C.USER_AGENT, "Accept": "application/json"},
        timeout=C.REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()

def _element_to_candidate(el):
    tags = el.get("tags") or {}
    center = el.get("center") or {}
    return {
        "source": "OpenStreetMap",
        "source_id": str(el.get("id", "")),
        "name": (tags.get("name") or "").strip(),
        "website": (tags.get("website") or tags.get("contact:website") or "").strip(),
        "email": (tags.get("email") or tags.get("contact:email") or "").strip(),
        "phone": (tags.get("phone") or tags.get("contact:phone") or "").strip(),
        "direccion": " ".join(x for x in [tags.get("addr:street", ""), tags.get("addr:housenumber", "")] if x).strip(),
        "lat": el.get("lat") or center.get("lat"),
        "lon": el.get("lon") or center.get("lon"),
        "tags": tags,
    }

def buscar():
    last_error = None
    for url in C.OVERPASS_URLS:
        try:
            log(f"[fuente] consultando {url}")
            data = _post(url)
            rows = [_element_to_candidate(e) for e in data.get("elements", [])]
            rows = [x for x in rows if x["name"]]
            log(f"[fuente] {len(rows)} lugares recibidos")
            return rows
        except Exception as exc:
            last_error = exc
            log(f"[fuente] fallo {url}: {exc}")
            time.sleep(1)
    raise RuntimeError(f"Ningún servidor Overpass respondió: {last_error}")
