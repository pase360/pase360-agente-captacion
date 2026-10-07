import re
import time
from urllib.parse import urlparse

import requests

from . import config as C
from .util import cargar, guardar, log, normalizar_email


CACHE_FILE = "base_candidatos.json"


# ============================================================
# BÚSQUEDA PRIORITARIA DE CONTACTOS YA PUBLICADOS EN OSM
# ============================================================

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
        "generadores_email_organizaciones",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"sindicato|gremio|mutual|federacion|federación|cooperativa|fundacion|fundación"]["email"]({bbox});
          nwr["name"~"sindicato|gremio|mutual|federacion|federación|cooperativa|fundacion|fundación"]["contact:email"]({bbox});
          nwr["office"="association"]["email"]({bbox});
          nwr["office"="association"]["contact:email"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),
    (
        "generadores_email_profesionales",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"colegio profesional|colegio de |consejo profesional|consejo de |asociacion profesional|asociación profesional"]["email"]({bbox});
          nwr["name"~"colegio profesional|colegio de |consejo profesional|consejo de |asociacion profesional|asociación profesional"]["contact:email"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),
    (
        "generadores_email_deportivos",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"club deportivo|club social|club de |jockey club|atletico|atlético|deportivo|deportiva|liga deportiva|federacion deportiva|federación deportiva"]["email"]({bbox});
          nwr["name"~"club deportivo|club social|club de |jockey club|atletico|atlético|deportivo|deportiva|liga deportiva|federacion deportiva|federación deportiva"]["contact:email"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),
]


# ============================================================
# BÚSQUEDA GENERAL
#
# Las consultas están separadas para evitar consultas gigantes
# que terminan en HTTP 504/time-out.
# ============================================================

CONSULTAS_COMPLETAS = [

    # --------------------------------------------------------
    # COMERCIOS
    # --------------------------------------------------------

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
        [out:json][timeout:35];
        (
          nwr["name"]["amenity"~"restaurant|cafe|fast_food|bar|pub|food_court|pharmacy|clinic|doctors|dentist|veterinary"]({bbox});
          nwr["name"]["healthcare"]({bbox});
        );
        out tags center;
        """,
        "comercio",
    ),

    # --------------------------------------------------------
    # GENERADORES FUERTES
    # --------------------------------------------------------

    (
        "generadores_sindicatos",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"sindicato|gremio|union de trabajadores|unión de trabajadores|sindical"]({bbox});
          nwr["office"="association"]["name"~"sindicato|gremio|union|unión"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_mutuales",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"mutual|asociacion mutual|asociación mutual"]({bbox});
          nwr["office"="association"]["name"~"mutual"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_cooperativas",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"cooperativa|cooperativa de servicios|cooperativa de trabajo|cooperativa obrera"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_federaciones",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"federacion|federación|confederacion|confederación"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_asociaciones",
        """
        [out:json][timeout:35];
        (
          nwr["office"="association"]["name"]({bbox});
          nwr["name"~"asociacion civil|asociación civil|asociacion profesional|asociación profesional"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_fundaciones",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"fundacion|fundación"]({bbox});
          nwr["office"~"foundation|association"]["name"~"fundacion|fundación"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    # --------------------------------------------------------
    # COLEGIOS Y CONSEJOS PROFESIONALES
    # --------------------------------------------------------

    (
        "generadores_colegios_profesionales",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"colegio profesional|colegio de abogados|colegio de arquitectos|colegio de ingenieros|colegio de contadores|colegio de escribanos|colegio de médicos|colegio de medicos|colegio de odontologos|colegio de odontólogos|colegio de psicologos|colegio de psicólogos|colegio de farmacéuticos|colegio de farmaceuticos|colegio profesional"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_consejos_profesionales",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"consejo profesional|consejo de profesionales|consejo de abogados|consejo de ciencias economicas|consejo de ciencias económicas"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    # --------------------------------------------------------
    # CLUBES E INSTITUCIONES DEPORTIVAS
    #
    # IMPORTANTE:
    # No buscamos todos los sports_centre/stadium/sports_hall,
    # porque eso mete instalaciones que no necesariamente son
    # organizaciones de afiliados.
    # --------------------------------------------------------

    (
        "generadores_clubes",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"club deportivo|club social|club de futbol|club de fútbol|club de rugby|club de hockey|club de basquet|club de básquet|jockey club|club atletico|club atlético"]({bbox});
          nwr["club"]["name"]({bbox});
          nwr["club"="sport"]["name"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_deportivos",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"liga deportiva|federacion deportiva|federación deportiva|asociacion deportiva|asociación deportiva|union deportiva|unión deportiva"]({bbox});
          nwr["sport"]["name"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    # --------------------------------------------------------
    # ORGANIZACIONES SOCIALES
    # --------------------------------------------------------

    (
        "generadores_centros_vecinales",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"centro vecinal|centro barrial|centro comunitario|centro comunitaria"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_jubilados",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"centro de jubilados|centro de pensionados|jubilados y pensionados|pensionados"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_sociedades",
        """
        [out:json][timeout:35];
        (
          nwr["name"~"sociedad de fomento|sociedad civil|circulo|círculo|union de |unión de |agrupacion|agrupación"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),
]


# ============================================================
# OVERPASS
# ============================================================

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
            log(
                f"[fuente] respuesta inválida de {url}"
            )
            return None

    except requests.RequestException as e:
        log(
            f"[fuente] error de conexión "
            f"{url}: {e}"
        )
        return None

    except Exception as e:
        log(
            f"[fuente] error inesperado "
            f"{url}: {e}"
        )
        return None


def _consultar(nombre, plantilla, grupo):
    query = plantilla.replace(
        "{bbox}",
        C.BBOX,
    )

    for url in C.OVERPASS_URLS:
        log(
            f"[fuente] {nombre} -> {url}"
        )

        data = _post_overpass(
            url,
            query,
        )

        if not data:
            continue

        elementos = data.get(
            "elements",
            [],
        )

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
                    resultado.append(
                        candidato
                    )

            return resultado

        log(
            f"[fuente] {nombre}: 0 lugares"
        )

    return []


# ============================================================
# CONVERSIÓN OSM -> CANDIDATO
# ============================================================

def _element_to_candidate(
    elemento,
    grupo,
    fuente,
):
    tags = elemento.get("tags") or {}

    name = (
        tags.get("name")
        or tags.get("official_name")
        or tags.get("short_name")
        or ""
    ).strip()

    if not name:
        return None

    lat = elemento.get("lat")
    lon = elemento.get("lon")

    center = elemento.get(
        "center"
    ) or {}

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

    direccion = _direccion(
        tags
    )

    source_id = (
        f"{elemento.get('type', '')}:"
        f"{elemento.get('id', '')}"
    )

    return {
        "name": name,
        "email": email,
        "website": website,
        "phone": phone,
        "direccion": direccion,
        "source": fuente,
        "source_id": source_id,
        "grupo_fuente": grupo,
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
            partes[-1] = (
                f"{partes[-1]} {number}"
            )
        else:
            partes.append(number)

    if city and city.lower() not in (
        " ".join(partes).lower()
    ):
        partes.append(city)

    return ", ".join(partes)


# ============================================================
# CLAVES Y FUSIÓN
# ============================================================

def _clave(candidato):
    source_id = str(
        candidato.get(
            "source_id"
        ) or ""
    ).strip()

    if source_id:
        return f"osm:{source_id}"

    email = normalizar_email(
        candidato.get("email")
    )

    if email:
        return f"email:{email}"

    name = str(
        candidato.get("name")
        or ""
    ).strip().lower()

    website = str(
        candidato.get("website")
        or ""
    ).strip().lower()

    phone = re.sub(
        r"\D+",
        "",
        str(
            candidato.get("phone")
            or ""
        ),
    )

    direccion = re.sub(
        r"\s+",
        " ",
        str(
            candidato.get("direccion")
            or ""
        ).strip().lower(),
    )

    return (
        f"{name}|{website}|"
        f"{phone}|{direccion}"
    )


def _clave_flexible(candidato):
    email = normalizar_email(
        candidato.get("email")
    )

    if email:
        return f"email:{email}"

    name = re.sub(
        r"\s+",
        " ",
        str(
            candidato.get("name")
            or ""
        ).strip().lower(),
    )

    website = str(
        candidato.get("website")
        or ""
    ).strip().lower()

    if website:
        try:
            host = urlparse(
                website
            ).netloc.lower()

            host = host.removeprefix(
                "www."
            )
        except Exception:
            host = website

        return f"web:{name}|{host}"

    phone = re.sub(
        r"\D+",
        "",
        str(
            candidato.get("phone")
            or ""
        ),
    )

    direccion = re.sub(
        r"\s+",
        " ",
        str(
            candidato.get("direccion")
            or ""
        ).strip().lower(),
    )

    return (
        f"nombre:{name}|"
        f"tel:{phone}|"
        f"dir:{direccion}"
    )


def _fusionar(candidatos):
    resultado = {}

    for candidato in candidatos:
        if not candidato:
            continue

        if not candidato.get("name"):
            continue

        clave = _clave(
            candidato
        )

        if clave not in resultado:
            resultado[clave] = dict(
                candidato
            )
            continue

        actual = resultado[clave]

        for campo in (
            "email",
            "website",
            "phone",
            "direccion",
            "lat",
            "lon",
        ):
            if (
                not actual.get(campo)
                and candidato.get(campo)
            ):
                actual[campo] = candidato[campo]

        tags_actuales = (
            actual.get("tags")
            or {}
        )

        tags_nuevos = (
            candidato.get("tags")
            or {}
        )

        if tags_nuevos:
            tags_actuales.update(
                tags_nuevos
            )
            actual["tags"] = (
                tags_actuales
            )

    finales = {}

    for candidato in resultado.values():
        clave = _clave_flexible(
            candidato
        )

        if clave not in finales:
            finales[clave] = candidato
            continue

        actual = finales[clave]

        email_actual = normalizar_email(
            actual.get("email")
        )

        email_nuevo = normalizar_email(
            candidato.get("email")
        )

        if (
            email_nuevo
            and not email_actual
        ):
            finales[clave] = candidato

    return list(
        finales.values()
    )


# ============================================================
# BASE PERSISTENTE DE ESTE AGENTE
# ============================================================

def _cargar_base():
    base = cargar(
        CACHE_FILE,
        [],
    )

    if not isinstance(
        base,
        list,
    ):
        return []

    resultado = []

    for candidato in base:
        if (
            isinstance(candidato, dict)
            and candidato.get("name")
        ):
            resultado.append(
                candidato
            )

    return resultado


def _guardar_base(candidatos):
    candidatos = _fusionar(
        candidatos
    )

    if len(candidatos) > 20000:
        candidatos = candidatos[:20000]

    guardar(
        CACHE_FILE,
        candidatos,
    )

    log(
        f"[fuente] base persistente "
        f"de este agente: "
        f"{len(candidatos)} candidatos"
    )


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def buscar():
    """
    1. Busca primero contactos publicados directamente en OSM.
    2. Busca comercios.
    3. Busca generadores por categorías pequeñas.
    4. Pone los candidatos NUEVOS antes de la base histórica.
    5. Fusiona sin perder los datos existentes.
    6. Si Overpass falla, conserva la base disponible.
    """

    encontrados = []

    consultas_ok = 0
    consultas_error = 0

    # --------------------------------------------------------
    # ETAPA 1 - EMAIL PUBLICADO
    # --------------------------------------------------------

    log(
        "[fuente] etapa 1: "
        "búsqueda prioritaria con email"
    )

    for (
        nombre,
        plantilla,
        grupo,
    ) in CONSULTAS_EMAIL:

        resultado = _consultar(
            nombre,
            plantilla,
            grupo,
        )

        if resultado:
            consultas_ok += 1
            encontrados.extend(
                resultado
            )
        else:
            consultas_error += 1

        time.sleep(0.4)

    log(
        f"[fuente] email-first: "
        f"{len(encontrados)} candidatos"
    )

    # --------------------------------------------------------
    # ETAPA 2 - AMPLIACIÓN
    # --------------------------------------------------------

    log(
        "[fuente] etapa 2: "
        "ampliación de candidatos"
    )

    for (
        nombre,
        plantilla,
        grupo,
    ) in CONSULTAS_COMPLETAS:

        resultado = _consultar(
            nombre,
            plantilla,
            grupo,
        )

        if resultado:
            consultas_ok += 1
            encontrados.extend(
                resultado
            )
        else:
            consultas_error += 1

        time.sleep(0.4)

    # --------------------------------------------------------
    # BASE PERSISTENTE
    #
    # IMPORTANTE:
    # Los nuevos van PRIMERO.
    #
    # Antes era:
    #     base_actual + encontrados
    #
    # Eso hacía que una base de ~18.000 registros pudiera
    # ocultar los candidatos recién encontrados cuando el
    # motor limitaba el escaneo.
    # --------------------------------------------------------

    base_actual = _cargar_base()

    if base_actual:
        log(
            f"[fuente] base persistente "
            f"del agente encontrada: "
            f"{len(base_actual)} candidatos"
        )

    combinados = _fusionar(
        encontrados + base_actual
    )

    if combinados:
        _guardar_base(
            combinados
        )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not encontrados:

        if base_actual:
            log(
                "[fuente] Overpass no "
                "entregó candidatos nuevos. "
                "Se conserva la base persistente."
            )

            return base_actual

        raise RuntimeError(
            "Overpass no devolvió "
            "candidatos y todavía "
            "no existe una base persistente."
        )

    log(
        f"[fuente] resultado final: "
        f"{len(combinados)} candidatos"
    )

    log(
        f"[fuente] consultas OK="
        f"{consultas_ok} "
        f"errores="
        f"{consultas_error}"
    )

    return combinados
