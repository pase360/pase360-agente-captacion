import re
import time
from urllib.parse import urlparse

import requests

from . import config as C
from .util import cargar, guardar, log, normalizar_email


CACHE_FILE = "base_candidatos.json"

# ============================================================
# CONSULTAS OVERPASS
#
# Se redujeron deliberadamente:
# - menos consultas
# - menos regex gigantes
# - prioridad a etiquetas estructuradas
# - fallback entre servidores solamente cuando hace falta
#
# La clasificación fina la hace clasificador.py.
# ============================================================

CONSULTAS = [

    # --------------------------------------------------------
    # 1. CONTACTOS PUBLICADOS EN OSM
    # --------------------------------------------------------

    (
        "osm_email",
        """
        [out:json][timeout:25];
        (
          nwr["email"]({bbox});
          nwr["contact:email"]({bbox});
        );
        out tags center;
        """,
        "mixto",
    ),

    # --------------------------------------------------------
    # 2. COMERCIOS
    # --------------------------------------------------------

    (
        "comercios_shop",
        """
        [out:json][timeout:30];
        (
          nwr["shop"]["name"]({bbox});
          nwr["craft"]["name"]({bbox});
          nwr["office"]["name"]({bbox});
        );
        out tags center;
        """,
        "comercio",
    ),

    (
        "comercios_servicios",
        """
        [out:json][timeout:30];
        (
          nwr["amenity"~"restaurant|cafe|fast_food|bar|pub|food_court|pharmacy|clinic|doctors|dentist|veterinary"]["name"]({bbox});
          nwr["healthcare"]["name"]({bbox});
        );
        out tags center;
        """,
        "comercio",
    ),

    # --------------------------------------------------------
    # 3. GENERADORES POR ETIQUETA OSM
    # --------------------------------------------------------

    (
        "generadores_clubes",
        """
        [out:json][timeout:30];
        (
          nwr["club"]["name"]({bbox});
          nwr["leisure"="sports_club"]["name"]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    # --------------------------------------------------------
    # 4. GENERADORES IMPORTANTES POR NOMBRE
    #
    # Se mantienen solamente grupos pequeños para evitar que
    # Overpass tenga que procesar expresiones enormes.
    # --------------------------------------------------------

    (
        "generadores_sindicales",
        """
        [out:json][timeout:30];
        (
          nwr["name"~"sindicato|gremio|union de trabajadores|unión de trabajadores",i]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_mutuales",
        """
        [out:json][timeout:30];
        (
          nwr["name"~"mutual|asociacion mutual|asociación mutual",i]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_cooperativas",
        """
        [out:json][timeout:30];
        (
          nwr["name"~"cooperativa",i]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_cajas_profesionales",
        """
        [out:json][timeout:30];
        (
          nwr["name"~"caja de abogados|caja de profesionales|caja de previsión de abogados|caja de prevision de abogados|caja previsional de profesionales",i]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_profesionales",
        """
        [out:json][timeout:30];
        (
          nwr["name"~"colegio profesional|colegio de |consejo profesional|consejo de ",i]({bbox});
        );
        out tags center;
        """,
        "generador",
    ),

    (
        "generadores_deportivos",
        """
        [out:json][timeout:30];
        (
          nwr["name"~"club deportivo|club social|club de futbol|club de fútbol|club de rugby|club de hockey|club de basquet|club de básquet|jockey club|club atletico|club atlético|asociacion deportiva|asociación deportiva|asociacion de futbol|asociación de fútbol|federacion deportiva|federación deportiva|federacion de futbol|federación de fútbol|liga deportiva|liga de futbol|liga de fútbol|entidad deportiva|entidad deportiva y social|asociacion atletica|asociación atlética|asociacion de atletismo|asociación de atletismo",i]({bbox});
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
            timeout=C.REQUEST_TIMEOUT + 15,
        )

        if respuesta.status_code == 200:
            try:
                return respuesta.json()
            except Exception:
                log(
                    f"[fuente] respuesta JSON inválida: {url}"
                )
                return None

        log(
            f"[fuente] {url} respondió HTTP "
            f"{respuesta.status_code}"
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


def _bbox_generador_fragmentos():
    """
    Fragmenta Córdoba en cuatro sectores solamente para las consultas
    de generadores que fallan sobre el bbox completo.

    Esto reduce el trabajo que Overpass debe hacer por consulta sin
    aumentar el volumen normal de consultas cuando el bbox completo
    responde correctamente.
    """
    partes = C.BBOX.split(",")
    if len(partes) != 4:
        return [C.BBOX]

    sur, oeste, norte, este = map(float, partes)
    mitad_lat = (sur + norte) / 2
    mitad_lon = (oeste + este) / 2

    return [
        f"{sur},{oeste},{mitad_lat},{mitad_lon}",
        f"{sur},{mitad_lon},{mitad_lat},{este}",
        f"{mitad_lat},{oeste},{norte},{mitad_lon}",
        f"{mitad_lat},{mitad_lon},{norte},{este}",
    ]


def _consultar_una_area(nombre, plantilla, grupo, bbox):
    query = plantilla.replace("{bbox}", bbox)

    for indice, url in enumerate(C.OVERPASS_URLS):
        log(
            f"[fuente] {nombre} -> "
            f"servidor {indice + 1}/{len(C.OVERPASS_URLS)}"
        )

        data = _post_overpass(url, query)

        if data is None:
            if indice < len(C.OVERPASS_URLS) - 1:
                time.sleep(1.5)
            continue

        elementos = data.get("elements", [])
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

    return None


def _consultar(nombre, plantilla, grupo):
    resultado = _consultar_una_area(
        nombre,
        plantilla,
        grupo,
        C.BBOX,
    )

    # Si la consulta completa de un generador falla, se divide el
    # territorio en cuatro sectores. Esto es un fallback, no una
    # multiplicación permanente de consultas.
    if resultado is not None:
        log(
            f"[fuente] {nombre}: "
            f"{len(resultado)} lugares recibidos"
        )
        return resultado

    if grupo != "generador":
        return []

    log(
        f"[fuente] {nombre}: "
        "consulta completa falló; "
        "reintentando por sectores"
    )

    todos = []
    fragmentos = _bbox_generador_fragmentos()

    for indice, bbox in enumerate(fragmentos, start=1):
        log(
            f"[fuente] {nombre}: "
            f"sector {indice}/{len(fragmentos)}"
        )

        sector = _consultar_una_area(
            nombre,
            plantilla,
            grupo,
            bbox,
        )

        if sector is None:
            continue

        todos.extend(sector)
        time.sleep(0.8)

    if not todos:
        return []

    # Un mismo objeto puede caer en el borde de dos sectores.
    unicos = {}
    for candidato in todos:
        clave = _clave(candidato)
        unicos[clave] = candidato

    log(
        f"[fuente] {nombre}: "
        f"{len(unicos)} lugares recibidos "
        "tras fragmentar"
    )

    return list(unicos.values())


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

    direccion = _direccion(tags)

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

    if city:
        ciudad_actual = " ".join(partes).lower()

        if city.lower() not in ciudad_actual:
            partes.append(city)

    return ", ".join(partes)


# ============================================================
# CLAVES
# ============================================================

def _clave(candidato):
    source_id = str(
        candidato.get("source_id") or ""
    ).strip()

    if source_id:
        return f"osm:{source_id}"

    email = normalizar_email(
        candidato.get("email")
    )

    if email:
        return f"email:{email}"

    name = str(
        candidato.get("name") or ""
    ).strip().lower()

    website = str(
        candidato.get("website") or ""
    ).strip().lower()

    phone = re.sub(
        r"\D+",
        "",
        str(
            candidato.get("phone") or ""
        ),
    )

    direccion = re.sub(
        r"\s+",
        " ",
        str(
            candidato.get("direccion") or ""
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
            candidato.get("name") or ""
        ).strip().lower(),
    )

    website = str(
        candidato.get("website") or ""
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
            candidato.get("phone") or ""
        ),
    )

    direccion = re.sub(
        r"\s+",
        " ",
        str(
            candidato.get("direccion") or ""
        ).strip().lower(),
    )

    return (
        f"nombre:{name}|"
        f"tel:{phone}|"
        f"dir:{direccion}"
    )


# ============================================================
# FUSIÓN
# ============================================================

def _fusionar(candidatos):
    resultado = {}

    for candidato in candidatos:

        if not candidato:
            continue

        if not candidato.get("name"):
            continue

        clave = _clave(candidato)

        if clave not in resultado:
            resultado[clave] = dict(candidato)
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
            actual.get("tags") or {}
        )

        tags_nuevos = (
            candidato.get("tags") or {}
        )

        if tags_nuevos:
            tags_actuales.update(
                tags_nuevos
            )
            actual["tags"] = tags_actuales

    finales = {}

    for candidato in resultado.values():

        clave = _clave_flexible(candidato)

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

    return list(finales.values())


# ============================================================
# BASE PERSISTENTE
# ============================================================

def _cargar_base():
    base = cargar(
        CACHE_FILE,
        [],
    )

    if not isinstance(base, list):
        return []

    resultado = []

    for candidato in base:

        if (
            isinstance(candidato, dict)
            and candidato.get("name")
        ):
            resultado.append(candidato)

    return resultado


def _guardar_base(candidatos):
    candidatos = _fusionar(candidatos)

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

    encontrados = []

    consultas_ok = 0
    consultas_error = 0

    log(
        "[fuente] iniciando captación "
        "desde fuentes públicas"
    )

    for (
        nombre,
        plantilla,
        grupo,
    ) in CONSULTAS:

        resultado = _consultar(
            nombre,
            plantilla,
            grupo,
        )

        if resultado:
            consultas_ok += 1
            encontrados.extend(resultado)
        else:
            consultas_error += 1

        # Pequeña pausa para no golpear
        # continuamente al servidor.
        time.sleep(0.7)

    log(
        f"[fuente] candidatos nuevos "
        f"obtenidos: {len(encontrados)}"
    )

    # --------------------------------------------------------
    # BASE PERSISTENTE
    # --------------------------------------------------------

    base_actual = _cargar_base()

    if base_actual:
        log(
            f"[fuente] base persistente "
            f"encontrada: "
            f"{len(base_actual)} candidatos"
        )

    # Los nuevos tienen prioridad.
    combinados = _fusionar(
        encontrados + base_actual
    )

    if combinados:
        _guardar_base(combinados)

    # --------------------------------------------------------
    # FALLBACK SI TODAS LAS FUENTES FALLAN
    # --------------------------------------------------------

    if not encontrados:

        if base_actual:
            log(
                "[fuente] no hubo candidatos "
                "nuevos; se conserva la base "
                "persistente."
            )

            log(
                f"[fuente] consultas OK="
                f"{consultas_ok} "
                f"errores="
                f"{consultas_error}"
            )

            return base_actual

        raise RuntimeError(
            "Las fuentes públicas no "
            "devolvieron candidatos y "
            "todavía no existe una base "
            "persistente."
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
