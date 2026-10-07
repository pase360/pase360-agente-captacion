import time
import requests

from . import config as C
from .util import log


PAUSA_ENTRE_CONSULTAS = 1
PAUSA_ENTRE_SERVIDORES = 1

SERVIDORES_OVERPASS = list(
    C.OVERPASS_URLS
)


# ------------------------------------------------------------
# CONSULTAS
# ------------------------------------------------------------

CONSULTAS = [
    (
        "comercio",
        f"""
        [out:json][timeout:30];
        (
          nwr["name"]["shop"]({C.BBOX});
          nwr["name"]["craft"]({C.BBOX});
          nwr["name"]["office"~"company|commercial|estate_agent|insurance|lawyer|accountant"]({C.BBOX});
        );
        out center tags;
        """,
    ),
    (
        "comercio",
        f"""
        [out:json][timeout:30];
        (
          nwr["name"]["amenity"~"restaurant|cafe|fast_food|bar|pub|food_court|pharmacy|clinic|doctors|dentist|veterinary"]({C.BBOX});
          nwr["name"]["healthcare"]({C.BBOX});
        );
        out center tags;
        """,
    ),
    (
        "generador",
        f"""
        [out:json][timeout:30];
        (
          nwr["name"~"sindicato|sindicatos|gremio|gremial|mutual|mutualidad|federacion|federación|cooperativa|cooperativas",i]({C.BBOX});
          nwr["name"]["office"="association"]({C.BBOX});
        );
        out center tags;
        """,
    ),
    (
        "generador",
        f"""
        [out:json][timeout:30];
        (
          nwr["name"~"colegio de abogados|colegio de escribanos|colegio de arquitectos|colegio de ingenieros|colegio de contadores|colegio de médicos|colegio de medicos|colegio de odontólogos|colegio de odontologos|colegio de psicólogos|colegio de psicologos|colegio de veterinarios|colegio de farmacéuticos|colegio de farmaceuticos|colegio profesional|consejo profesional|asociacion de profesionales|asociación de profesionales",i]({C.BBOX});
        );
        out center tags;
        """,
    ),
    (
        "generador",
        f"""
        [out:json][timeout:30];
        (
          nwr["name"]["club"]({C.BBOX});
          nwr["name"~"club atletico|club atlético|club deportivo|club social|club de barrio|institucion deportiva|institución deportiva|asociacion deportiva|asociación deportiva|liga deportiva|entidad deportiva",i]({C.BBOX});
          nwr["leisure"~"sports_centre|stadium|sports_hall"]["name"]({C.BBOX});
        );
        out center tags;
        """,
    ),
    (
        "generador",
        f"""
        [out:json][timeout:30];
        (
          nwr["name"~"centro vecinal|centro de jubilados|centro de pensionados|centro de trabajadores|centro de empleados|asociacion civil|asociación civil|fundacion|fundación",i]({C.BBOX});
          nwr["amenity"~"community_centre|social_centre"]["name"]({C.BBOX});
        );
        out center tags;
        """,
    ),
]


def _post(url, query):
    response = requests.post(
        url,
        data={"data": query},
        headers={
            "User-Agent": C.USER_AGENT,
            "Accept": "application/json",
        },
        timeout=max(
            min(C.REQUEST_TIMEOUT, 35),
            30,
        ),
    )

    response.raise_for_status()

    return response.json()


def _element_to_candidate(elemento):
    tags = elemento.get("tags") or {}
    center = elemento.get("center") or {}

    return {
        "source": "OpenStreetMap",
        "source_id": (
            f'{elemento.get("type", "")}:'
            f'{elemento.get("id", "")}'
        ),
        "name": str(
            tags.get("name") or ""
        ).strip(),
        "website": str(
            tags.get("website")
            or tags.get("contact:website")
            or ""
        ).strip(),
        "email": str(
            tags.get("email")
            or tags.get("contact:email")
            or ""
        ).strip(),
        "phone": str(
            tags.get("phone")
            or tags.get("contact:phone")
            or ""
        ).strip(),
        "direccion": " ".join(
            x
            for x in (
                tags.get("addr:street", ""),
                tags.get("addr:housenumber", ""),
            )
            if x
        ).strip(),
        "lat": (
            elemento.get("lat")
            or center.get("lat")
        ),
        "lon": (
            elemento.get("lon")
            or center.get("lon")
        ),
        "tags": tags,
    }


def _clave(elemento):
    tipo = str(
        elemento.get("type") or ""
    ).strip()

    elemento_id = str(
        elemento.get("id") or ""
    ).strip()

    if tipo and elemento_id:
        return (
            tipo,
            elemento_id,
        )

    tags = elemento.get("tags") or {}

    return (
        str(tags.get("name") or "").strip().lower(),
        elemento.get("lat"),
        elemento.get("lon"),
    )


def _servidores_rotados(indice):
    if not SERVIDORES_OVERPASS:
        return []

    posicion = (
        (indice - 1)
        % len(SERVIDORES_OVERPASS)
    )

    return (
        SERVIDORES_OVERPASS[posicion:]
        + SERVIDORES_OVERPASS[:posicion]
    )


def _consultar(query, etiqueta, indice):
    ultimo_error = None

    for numero, servidor in enumerate(
        _servidores_rotados(indice),
        start=1,
    ):
        try:
            log(
                f"[fuente] {etiqueta} "
                f"{indice}/{len(CONSULTAS)} "
                f"servidor {numero}/"
                f"{len(SERVIDORES_OVERPASS)}"
            )

            data = _post(
                servidor,
                query,
            )

            elementos = data.get(
                "elements",
                [],
            )

            log(
                f"[fuente] {etiqueta}: "
                f"{len(elementos)} elementos"
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
                f"[fuente] {etiqueta}: "
                f"HTTP {codigo}"
            )

        except requests.Timeout as exc:
            ultimo_error = exc

            log(
                f"[fuente] {etiqueta}: timeout"
            )

        except Exception as exc:
            ultimo_error = exc

            log(
                f"[fuente] {etiqueta}: "
                f"error {exc}"
            )

        time.sleep(
            PAUSA_ENTRE_SERVIDORES
        )

    raise RuntimeError(
        f"No se pudo consultar {etiqueta}: "
        f"{ultimo_error}"
    )


def _mezclar(comercios, generadores):
    resultado = []

    i = 0
    j = 0

    while (
        i < len(comercios)
        or j < len(generadores)
    ):
        if j < len(generadores):
            resultado.append(
                generadores[j]
            )
            j += 1

        if i < len(comercios):
            resultado.append(
                comercios[i]
            )
            i += 1

    return resultado


def buscar():
    elementos_unicos = {}

    comercios = []
    generadores = []

    errores = []

    for indice, (grupo, query) in enumerate(
        CONSULTAS,
        start=1,
    ):
        if indice > 1:
            time.sleep(
                PAUSA_ENTRE_CONSULTAS
            )

        try:
            elementos = _consultar(
                query,
                grupo,
                indice,
            )

            for elemento in elementos:
                clave = _clave(elemento)

                if clave in elementos_unicos:
                    continue

                elementos_unicos[clave] = True

                candidato = (
                    _element_to_candidate(
                        elemento
                    )
                )

                if not candidato["name"]:
                    continue

                if grupo == "generador":
                    generadores.append(
                        candidato
                    )
                else:
                    comercios.append(
                        candidato
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
                f"[fuente] se continúa: "
                f"{exc}"
            )

    resultado = _mezclar(
        comercios,
        generadores,
    )

    log(
        f"[fuente] comercios: "
        f"{len(comercios)}"
    )

    log(
        f"[fuente] generadores: "
        f"{len(generadores)}"
    )

    log(
        f"[fuente] únicos: "
        f"{len(resultado)}"
    )

    if errores:
        log(
            f"[fuente] consultas con error: "
            f"{len(errores)}"
        )

    if not resultado:
        raise RuntimeError(
            "Overpass no devolvió candidatos."
        )

    return resultado
