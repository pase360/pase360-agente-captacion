import time
import requests

from . import config as C
from .util import log


# -------------------------------------------------------------------
# ESTRATEGIA DE CAPTACIÓN
#
# Busca comercios y generadores en Córdoba Capital mediante Overpass.
#
# Esta versión:
#   - mantiene las 8 consultas actuales
#   - distribuye las consultas entre servidores Overpass
#   - evita repetir inmediatamente el mismo servidor
#   - reduce los reintentos que provocaban 429
#   - espera entre consultas para no saturar Overpass
#   - continúa si una consulta falla
#   - mantiene la mezcla comercio/generador
# -------------------------------------------------------------------


CONSULTAS_COMERCIOS = [
    f"""
    [out:json][timeout:50];
    (
      nwr["name"]["shop"]({C.BBOX});
    );
    out center tags 180;
    """,

    f"""
    [out:json][timeout:50];
    (
      nwr["name"]["craft"]({C.BBOX});
      nwr["name"]["office"~"company|commercial"]({C.BBOX});
    );
    out center tags 140;
    """,

    f"""
    [out:json][timeout:50];
    (
      nwr["name"]["amenity"~"restaurant|cafe|fast_food|bar|pub|food_court"]({C.BBOX});
    );
    out center tags 140;
    """,

    f"""
    [out:json][timeout:50];
    (
      nwr["name"]["amenity"~"clinic|doctors|dentist|pharmacy|veterinary"]({C.BBOX});
      nwr["name"]["healthcare"]({C.BBOX});
    );
    out center tags 120;
    """,
]


CONSULTAS_GENERADORES = [
    f"""
    [out:json][timeout:50];
    (
      nwr["name"]["office"="association"]({C.BBOX});
      nwr["name"]["amenity"="social_centre"]({C.BBOX});
      nwr["name"]["amenity"="community_centre"]({C.BBOX});
    );
    out center tags 160;
    """,

    f"""
    [out:json][timeout:50];
    (
      nwr["name"~"sindicato|sindicatos|gremio|gremial|union de trabajadores|union de empleados|mutual|mutualidad|federacion|federación",i]({C.BBOX});
    );
    out center tags 140;
    """,

    f"""
    [out:json][timeout:50];
    (
      nwr["name"~"colegio de abogados|colegio de escribanos|colegio de arquitectos|colegio de ingenieros|colegio de contadores|colegio de medicos|colegio de médicos|colegio de odontologos|colegio de odontólogos|colegio de psicologos|colegio de psicólogos|colegio de veterinarios|colegio de farmacéuticos|colegio de farmaceuticos|colegio profesional|consejo profesional|asociacion de profesionales|asociación de profesionales",i]({C.BBOX});
    );
    out center tags 140;
    """,

    f"""
    [out:json][timeout:50];
    (
      nwr["name"]["club"]({C.BBOX});
      nwr["name"]["leisure"~"sports_centre|stadium|sports_hall|pitch"]({C.BBOX});
      nwr["name"]["amenity"="arts_centre"]({C.BBOX});
    );
    out center tags 140;
    """,
]


TODAS_LAS_CONSULTAS = (
    [
        ("comercio", q)
        for q in CONSULTAS_COMERCIOS
    ]
    + [
        ("generador", q)
        for q in CONSULTAS_GENERADORES
    ]
)


# -------------------------------------------------------------------
# CONTROL DE SERVIDORES
# -------------------------------------------------------------------
#
# No hacemos:
#
#   servidor A -> A -> A -> B -> B -> B
#
# porque eso fue una de las causas de los 429.
#
# En cambio, vamos rotando los servidores disponibles.
# -------------------------------------------------------------------

SERVIDORES_OVERPASS = list(C.OVERPASS_URLS)

PAUSA_ENTRE_CONSULTAS = 4
PAUSA_ENTRE_REINTENTOS = 8


def _post(url, query):
    r = requests.post(
        url,
        data={"data": query},
        headers={
            "User-Agent": C.USER_AGENT,
            "Accept": "application/json",
        },
        timeout=max(C.REQUEST_TIMEOUT, 50),
        allow_redirects=True,
    )

    r.raise_for_status()

    return r.json()


def _element_to_candidate(el):
    tags = el.get("tags") or {}
    center = el.get("center") or {}

    return {
        "source": "OpenStreetMap",
        "source_id": str(
            el.get("id", "")
        ),
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


def _servidores_rotados(indice):
    if not SERVIDORES_OVERPASS:
        return []

    posicion = (indice - 1) % len(SERVIDORES_OVERPASS)

    return (
        SERVIDORES_OVERPASS[posicion:]
        + SERVIDORES_OVERPASS[:posicion]
    )


def _consultar_con_reintentos(
    query,
    etiqueta,
    indice,
    total,
):
    ultimo_error = None

    servidores = _servidores_rotados(indice)

    # Primera ronda:
    # probamos cada servidor una sola vez.
    for numero, url in enumerate(
        servidores,
        start=1,
    ):
        try:
            log(
                f"[fuente] {etiqueta} "
                f"{indice}/{total} "
                f"consultando servidor "
                f"{numero}/{len(servidores)}: "
                f"{url}"
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
                f"[fuente] {etiqueta} "
                f"{indice}/{total}: "
                f"{len(elementos)} elementos recibidos"
            )

            return elementos

        except requests.HTTPError as exc:
            ultimo_error = exc

            codigo = (
                exc.response.status_code
                if exc.response is not None
                else None
            )

            log(
                f"[fuente] {etiqueta} "
                f"{indice}/{total} "
                f"falló en {url} "
                f"(HTTP {codigo}): {exc}"
            )

            # Un 429 significa que ese servidor pide bajar
            # el ritmo. No insistimos inmediatamente.
            if codigo == 429:
                log(
                    "[fuente] servidor respondió 429; "
                    "se continúa con el siguiente servidor."
                )

            time.sleep(2)

        except Exception as exc:
            ultimo_error = exc

            log(
                f"[fuente] {etiqueta} "
                f"{indice}/{total} "
                f"falló en {url}: {exc}"
            )

            time.sleep(2)

    # Segunda oportunidad:
    #
    # Solamente hacemos UNA nueva ronda y con una espera previa.
    # Esto evita el ciclo anterior de 6 intentos consecutivos
    # sobre los servidores.
    log(
        f"[fuente] todos los servidores fallaron para "
        f"{etiqueta} {indice}/{total}; "
        f"esperando antes de una segunda ronda..."
    )

    time.sleep(PAUSA_ENTRE_REINTENTOS)

    for numero, url in enumerate(
        servidores,
        start=1,
    ):
        try:
            log(
                f"[fuente] {etiqueta} "
                f"{indice}/{total} "
                f"segunda ronda "
                f"{numero}/{len(servidores)}: "
                f"{url}"
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
                f"[fuente] {etiqueta} "
                f"{indice}/{total}: "
                f"{len(elementos)} elementos recibidos"
            )

            return elementos

        except Exception as exc:
            ultimo_error = exc

            log(
                f"[fuente] {etiqueta} "
                f"{indice}/{total} "
                f"segunda ronda falló en {url}: "
                f"{exc}"
            )

            time.sleep(2)

    raise RuntimeError(
        f"No se pudo obtener "
        f"{etiqueta} {indice}/{total}: "
        f"{ultimo_error}"
    )


def _mezclar_por_tipo(
    candidatos_comercio,
    candidatos_generador,
):
    """
    Mezcla los dos grupos en forma alternada.

    Esto es importante porque engine.py posteriormente aplica
    MAX_CANDIDATOS_SCAN. Así los primeros candidatos contienen
    ambos tipos.
    """

    resultado = []

    max_len = max(
        len(candidatos_comercio),
        len(candidatos_generador),
    )

    for i in range(max_len):

        if i < len(candidatos_generador):
            resultado.append(
                candidatos_generador[i]
            )

        if i < len(candidatos_comercio):
            resultado.append(
                candidatos_comercio[i]
            )

    return resultado


def buscar():
    todos = {}

    resultados_comercio = []
    resultados_generador = []

    errores = []

    total = len(
        TODAS_LAS_CONSULTAS
    )

    for indice, (grupo, query) in enumerate(
        TODAS_LAS_CONSULTAS,
        start=1,
    ):

        # Pausa entre consultas para reducir 429.
        if indice > 1:
            log(
                f"[fuente] pausa de "
                f"{PAUSA_ENTRE_CONSULTAS}s "
                f"antes de la siguiente consulta..."
            )

            time.sleep(
                PAUSA_ENTRE_CONSULTAS
            )

        try:
            elementos = _consultar_con_reintentos(
                query,
                grupo,
                indice,
                total,
            )

            destino = (
                resultados_generador
                if grupo == "generador"
                else resultados_comercio
            )

            for elemento in elementos:

                clave = _clave_elemento(
                    elemento
                )

                if clave in todos:
                    continue

                todos[clave] = elemento

                destino.append(
                    elemento
                )

        except Exception as exc:

            errores.append(
                {
                    "grupo": grupo,
                    "indice": indice,
                    "error": str(exc),
                }
            )

            log(
                f"[fuente] consulta "
                f"{grupo} {indice}/{total} "
                f"no disponible: {exc}"
            )

    # ---------------------------------------------------------------
    # Convertimos los elementos OSM a candidatos.
    # ---------------------------------------------------------------

    comercios = [
        _element_to_candidate(el)
        for el in resultados_comercio
    ]

    generadores = [
        _element_to_candidate(el)
        for el in resultados_generador
    ]

    # Quitamos registros sin nombre.

    comercios = [
        x
        for x in comercios
        if x["name"]
    ]

    generadores = [
        x
        for x in generadores
        if x["name"]
    ]

    # Mezcla deliberada:
    #
    # generador
    # comercio
    # generador
    # comercio
    #
    # etc.

    rows = _mezclar_por_tipo(
        comercios,
        generadores,
    )

    log(
        f"[fuente] comercios candidatos: "
        f"{len(comercios)}"
    )

    log(
        f"[fuente] generadores candidatos: "
        f"{len(generadores)}"
    )

    log(
        f"[fuente] total final: "
        f"{len(rows)} lugares únicos recibidos"
    )

    if not rows:
        raise RuntimeError(
            "Ninguna consulta de Overpass pudo "
            "devolver lugares."
        )

    if errores:
        log(
            f"[fuente] advertencia: "
            f"{len(errores)} consulta(s) fallaron, "
            f"pero se continúa con los datos obtenidos."
        )

    return rows
