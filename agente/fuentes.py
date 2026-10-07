import json
import re
import time
from urllib.parse import urlparse

import requests

from . import config as C
from .util import cargar, guardar, log, normalizar_email


CACHE_FILE = "base_candidatos.json"

# Consultas livianas: primero buscamos lugares que YA tengan email público
# cargado en OpenStreetMap.
CONSULTAS_EMAIL = [
    (
        "comercios_email",
        """
        [out:json][timeout:45];
        (
          nwr["name"]["shop"]["email"]({bbox});
          nwr["name"]["shop"]["contact:email"]({bbox});
          nwr["name"]["craft"]["email"]({bbox});
          nwr["name"]["craft"]["contact:email"]({bbox});
          nwr["name"]["amenity"]["email"]({bbox});
          nwr["name"]["amenity"]["contact:email"]({bbox});
          nwr["name"]["healthcare"]["email"]({bbox});
          nwr["name"]["healthcare"]["contact:email"]({bbox});
          nwr["name"]["office"]["email"]({bbox});
          nwr["name"]["office"]["contact:email"]({bbox});
        );
        out tags center;
        """,
        "comercio",
    ),
    (
        "generadores_email",
        """
        [out:json][timeout:45];
        (
          nwr["name"~"sindicato|gremio|mutual|federacion|federación|cooperativa|asociacion|asociación|fundacion|fundación"]["email"]({bbox});
          nwr["name"~"sindicato|gremio|mutual|federacion|federación|cooperativa|asociacion|asociación|fundacion|fundación"]["contact:email"]({bbox});

          nwr["name"~"colegio"]["email"]({bbox});
          nwr["name"~"colegio"]["contact:email"]({bbox});

          nwr["name"~"club|deportivo|deportiva|liga"]["email"]({bbox});
          nwr["name"~"club|deportivo|deportiva|liga"]["contact:email"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),
]

# Consultas amplias: se usan para ampliar la base cuando las consultas
# email-first no alcanzan.
CONSULTAS_COMPLETAS = [
    (
        "comercios_shop",
        """
        [out:json][timeout:45];
        (
          nwr["name"]["shop"]({bbox});
          nwr["name"]["craft"]({bbox});
          nwr["name"]["office"]({bbox});
        );
        out tags center;
        """,
        "comercio",
    ),
    (
        "comercios_amenity",
        """
        [out:json][timeout:45];
        (
          nwr["name"]["amenity"~"restaurant|cafe|fast_food|bar|pub|food_court|pharmacy|clinic|doctors|dentist|veterinary"]({bbox});
          nwr["name"]["healthcare"]({bbox});
        );
        out tags center;
        """,
        "comercio",
    ),
    (
        "generadores_organizaciones",
        """
        [out:json][timeout:45];
        (
          nwr["name"~"sindicato|gremio|mutual|federacion|federación|cooperativa"]({bbox});
          nwr["name"~"asociacion profesional|asociación profesional|fundacion|fundación"]({bbox});
          nwr["office"="association"]["name"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),
    (
        "generadores_colegios",
        """
        [out:json][timeout:45];
        (
          nwr["name"~"colegio"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),
    (
        "generadores_deportivos",
        """
        [out:json][timeout:45];
        (
          nwr["name"~"club|deportivo|deportiva|liga"]({bbox});
          nwr["leisure"~"sports_centre|stadium|sports_hall"]({bbox});
          nwr["sport"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),
    (
        "generadores_sociales",
        """
        [out:json][timeout:45];
        (
          nwr["name"~"centro vecinal|asociacion civil|asociación civil|fundacion|fundación"]({bbox});
          nwr["office"="association"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),
]


def _bbox():
    return C.BBOX


def _post_overpass(url, query):
    try:
        respuesta = requests.post(
            url,
            data=query,
            headers={
                "User-Agent": C.USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=C.REQUEST_TIMEOUT + 25,
        )

        if respuesta.status_code != 200:
            log(
                f"[fuente] {url} respondió HTTP "
                f"{respuesta.status_code}"
            )
            return None

        try:
            return respuesta.json()
        except Exception:
            log(f"[fuente] respuesta inválida de {url}")
            return None

    except requests.RequestException as e:
        log(f"[fuente] error de conexión {url}: {e}")
        return None

    except Exception as e:
        log(f"[fuente] error inesperado {url}: {e}")
        return None


def _consultar(nombre, plantilla, grupo):
    query = plantilla.replace("{bbox}", _bbox())

    for url in C.OVERPASS_URLS:
        log(f"[fuente] {nombre} -> {url}")

        data = _post_overpass(url, query)

        if not data:
            continue

        elementos = data.get("elements", [])

        if elementos:
            log(
                f"[fuente] {nombre}: "
                f"{len(elementos)} lugares recibidos"
            )

            resultado = []

            for elemento in elementos:
                candidato = _element_to_candidate(
                    elemento,
                    grupo,
                    nombre,
                )

                if candidato:
                    resultado.append(candidato)

            return resultado

        log(f"[fuente] {nombre}: 0 lugares")

    return []


def _element_to_candidate(elemento, grupo, fuente):
    tags = elemento.get("tags") or {}

    nombre = (
        tags.get("name")
        or tags.get("official_name")
        or tags.get("short_name")
        or ""
    ).strip()

    if not nombre:
        return None

    lat = elemento.get("lat")
    lon = elemento.get("lon")

    center = elemento.get("center") or {}

    if lat is None:
        lat = center.get("lat")

    if lon is None:
        lon = center.get("lon")

    email = normalizar_email(
        tags.get("email")
        or tags.get("contact:email")
        or ""
    )

    website = (
        tags.get("website")
        or tags.get("contact:website")
        or tags.get("url")
        or ""
    ).strip()

    phone = (
        tags.get("phone")
        or tags.get("contact:phone")
        or ""
    ).strip()

    address = _direccion(tags)

    source_id = (
        f"{elemento.get('type', '')}:"
        f"{elemento.get('id', '')}"
    )

    return {
        "source_id": source_id,
        "fuente": fuente,
        "grupo_fuente": grupo,
        "nombre": nombre,
        "email": email,
        "website": website,
        "telefono": phone,
        "direccion": address,
        "lat": lat,
        "lon": lon,
        "tags": tags,
    }


def _direccion(tags):
    partes = []

    street = (
        tags.get("addr:street")
        or tags.get("address:street")
        or ""
    ).strip()

    number = (
        tags.get("addr:housenumber")
        or tags.get("address:housenumber")
        or ""
    ).strip()

    city = (
        tags.get("addr:city")
        or tags.get("address:city")
        or ""
    ).strip()

    if street:
        partes.append(street)

    if number:
        if partes:
            partes[-1] = f"{partes[-1]} {number}"
        else:
            partes.append(number)

    if city and city.lower() not in " ".join(partes).lower():
        partes.append(city)

    return ", ".join(partes)


def _clave(candidato):
    source_id = str(candidato.get("source_id") or "").strip()

    if source_id:
        return f"osm:{source_id}"

    nombre = str(candidato.get("nombre") or "").strip().lower()
    lat = str(candidato.get("lat") or "")
    lon = str(candidato.get("lon") or "")

    return f"base:{nombre}|{lat}|{lon}"


def _clave_flexible(candidato):
    email = normalizar_email(candidato.get("email"))

    if email:
        return f"email:{email}"

    nombre = re.sub(
        r"\s+",
        " ",
        str(candidato.get("nombre") or "").strip().lower(),
    )

    website = str(candidato.get("website") or "").strip().lower()

    if website:
        try:
            host = urlparse(website).netloc.lower()
            host = host.removeprefix("www.")
        except Exception:
            host = website
        return f"web:{nombre}|{host}"

    telefono = re.sub(
        r"\D+",
        "",
        str(candidato.get("telefono") or ""),
    )

    direccion = re.sub(
        r"\s+",
        " ",
        str(candidato.get("direccion") or "").strip().lower(),
    )

    return f"nombre:{nombre}|tel:{telefono}|dir:{direccion}"


def _fusionar(candidatos):
    resultado = {}

    for candidato in candidatos:
        if not candidato:
            continue

        clave = _clave(candidato)

        if clave not in resultado:
            resultado[clave] = candidato
            continue

        actual = resultado[clave]

        # Conservamos la información más completa.
        for campo in (
            "email",
            "website",
            "telefono",
            "direccion",
            "lat",
            "lon",
        ):
            if not actual.get(campo) and candidato.get(campo):
                actual[campo] = candidato[campo]

        tags_actuales = actual.get("tags") or {}
        tags_nuevos = candidato.get("tags") or {}

        if tags_nuevos:
            tags_actuales.update(tags_nuevos)
            actual["tags"] = tags_actuales

    # Segunda deduplicación por identidad práctica.
    finales = {}
    for candidato in resultado.values():
        clave = _clave_flexible(candidato)

        if clave not in finales:
            finales[clave] = candidato
            continue

        actual = finales[clave]

        # Si una versión tiene email y la otra no,
        # gana la que tiene email.
        email_actual = normalizar_email(actual.get("email"))
        email_nuevo = normalizar_email(candidato.get("email"))

        if email_nuevo and not email_actual:
            finales[clave] = candidato

    return list(finales.values())


def _cargar_base():
    base = cargar(CACHE_FILE, [])

    if not isinstance(base, list):
        return []

    limpia = []

    for candidato in base:
        if isinstance(candidato, dict) and candidato.get("nombre"):
            limpia.append(candidato)

    return limpia


def _guardar_base(candidatos):
    candidatos = _fusionar(candidatos)

    # Evitamos que la base crezca indefinidamente por errores externos.
    if len(candidatos) > 20000:
        candidatos = candidatos[:20000]

    guardar(CACHE_FILE, candidatos)

    log(
        f"[fuente] base persistente: "
        f"{len(candidatos)} candidatos"
    )


def buscar():
    """
    Obtiene candidatos para captación.

    Estrategia:
    1. Primero intenta lugares que ya tienen email en OSM.
    2. Después amplía con consultas normales.
    3. Fusiona todo con la base persistente de ESTE agente.
    4. Si Overpass falla completamente, devuelve la base persistente
       en lugar de romper la captación.
    """

    encontrados = []
    consultas_ok = 0
    consultas_error = 0

    # ---------------------------------------------------------
    # ETAPA 1: EMAIL-FIRST
    # ---------------------------------------------------------
    log("[fuente] etapa 1: búsqueda prioritaria con email")

    for nombre, plantilla, grupo in CONSULTAS_EMAIL:
        resultado = _consultar(nombre, plantilla, grupo)

        if resultado:
            consultas_ok += 1
            encontrados.extend(resultado)
        else:
            consultas_error += 1

        time.sleep(0.4)

    log(
        f"[fuente] email-first: "
        f"{len(encontrados)} candidatos"
    )

    # ---------------------------------------------------------
    # ETAPA 2: AMPLIACIÓN
    # ---------------------------------------------------------
    log("[fuente] etapa 2: ampliación de candidatos")

    for nombre, plantilla, grupo in CONSULTAS_COMPLETAS:
        resultado = _consultar(nombre, plantilla, grupo)

        if resultado:
            consultas_ok += 1
            encontrados.extend(resultado)
        else:
            consultas_error += 1

        time.sleep(0.4)

    # ---------------------------------------------------------
    # FUSIÓN CON BASE PERSISTENTE
    # ---------------------------------------------------------
    base_anterior = _cargar_base()

    if base_anterior:
        log(
            f"[fuente] base anterior encontrada: "
            f"{len(base_anterior)} candidatos"
        )

    combinados = _fusionar(
        base_anterior + encontrados
    )

    # ---------------------------------------------------------
    # GUARDADO
    # ---------------------------------------------------------
    if combinados:
        _guardar_base(combinados)

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------
    if not encontrados:
        if base_anterior:
            log(
                "[fuente] Overpass no entregó candidatos nuevos. "
                "Se utiliza la base persistente."
            )
            return base_anterior

        raise RuntimeError(
            "Overpass no devolvió candidatos y todavía "
            "no existe una base persistente."
        )

    log(
        f"[fuente] resultado final: "
        f"{len(combinados)} candidatos"
    )

    log(
        f"[fuente] consultas OK={consultas_ok} "
        f"errores={consultas_error}"
    )

    return combinados
