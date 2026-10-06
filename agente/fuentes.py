import time
import requests

from . import config as C
from .util import log


OVERPASS_QUERIES = [
    f"""
    [out:json][timeout:90];
    (
      nwr["name"]["shop"]({C.BBOX});
      nwr["name"]["craft"]({C.BBOX});
    );
    out center tags;
    """,
    f"""
    [out:json][timeout:90];
    (
      nwr["name"]["amenity"]({C.BBOX});
      nwr["name"]["office"]({C.BBOX});
    );
    out center tags;
    """,
    f"""
    [out:json][timeout:90];
    (
      nwr["name"]["leisure"]({C.BBOX});
      nwr["name"]["tourism"]({C.BBOX});
      nwr["name"]["club"]({C.BBOX});
    );
    out center tags;
    """,
]


def _post(url, query):
    r = requests.post(
        url,
        data={"data": query},
        headers={
            "User-Agent": C.USER_AGENT,
            "Accept": "application/json",
        },
        timeout=max(C.REQUEST_TIMEOUT, 45),
    )
    r.raise_for_status()
    return r.json()


def _element_to_candidate(el):
    tags = el.get("tags") or {}
    center = el.get("center") or {}

    return {
        "source": "OpenStreetMap",
        "source_id": str(el.get("id", "")),
        "name": (
            tags.get("name")
            or ""
        ).strip(),
        "website": (
            tags.get("website")
            or tags.get("contact:website")
            or ""
        ).strip(),
        "email": (
            tags.get("email")
            or tags.get("contact:email")
            or ""
        ).strip(),
        "phone": (
            tags.get("phone")
            or tags.get("contact:phone")
            or ""
        ).strip(),
        "direccion": " ".join(
            x
            for x in [
                tags.get("addr:street", ""),
                tags.get("addr:housenumber", ""),
            ]
            if x
        ).strip(),
        "lat": (
            el.get("lat")
            or center.get("lat")
        ),
        "lon": (
            el.get("lon")
            or center.get("lon")
        ),
        "tags": tags,
    }


def _clave_elemento(el):
    elemento_id = str(
        el.get("id", "")
    ).strip()

    tipo = str(
        el.get("type", "")
    ).strip()

    if tipo and elemento_id:
        return f"{tipo}:{elemento_id}"

    tags = el.get("tags") or {}

    nombre = str(
        tags.get("name", "")
    ).strip().lower()

    return (
        nombre,
        el.get("lat"),
        el.get("lon"),
    )


def _consultar_con_reintentos(query, indice_query):
    ultimo_error = None

    for intento in range(2):
        for url in C.OVERPASS_URLS:
            try:
                log(
                    f"[fuente] bloque {indice_query}/"
                    f"{len(OVERPASS_QUERIES)} "
                    f"consultando {url} "
                    f"(intento {intento + 1}/2)"
                )

                data = _post(
                    url,
                    query,
                )

                elementos = data.get(
                    "elements",
                    [],
                )

                log(
                    f"[fuente] bloque {indice_query}: "
                    f"{len(elementos)} elementos recibidos"
                )

                return elementos

            except Exception as exc:
                ultimo_error = exc

                log(
                    f"[fuente] bloque {indice_query} "
                    f"falló en {url}: {exc}"
                )

                time.sleep(2)

        if intento == 0:
            log(
                f"[fuente] reintentando bloque "
                f"{indice_query}..."
            )
            time.sleep(3)

    raise RuntimeError(
        f"No se pudo obtener el bloque "
        f"{indice_query}: {ultimo_error}"
    )


def buscar():
    todos = {}
    errores = []

    for indice, query in enumerate(
        OVERPASS_QUERIES,
        start=1,
    ):
        try:
            elementos = _consultar_con_reintentos(
                query,
                indice,
            )

            for elemento in elementos:
                clave = _clave_elemento(
                    elemento
                )

                if clave not in todos:
                    todos[clave] = elemento

        except Exception as exc:
            errores.append(
                {
                    "bloque": indice,
                    "error": str(exc),
                }
            )

            log(
                f"[fuente] bloque {indice} "
                f"no disponible: {exc}"
            )

    rows = [
        _element_to_candidate(el)
        for el in todos.values()
    ]

    rows = [
        x
        for x in rows
        if x["name"]
    ]

    log(
        f"[fuente] total final: "
        f"{len(rows)} lugares únicos recibidos"
    )

    if not rows:
        raise RuntimeError(
            "Ningún bloque de Overpass pudo "
            "devolver lugares."
        )

    if errores:
        log(
            f"[fuente] advertencia: "
            f"{len(errores)} bloque(s) fallaron, "
            f"pero se continúa con los datos obtenidos."
        )

    return rows
