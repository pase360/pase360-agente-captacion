import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from . import config as C
from .util import normalizar_email, normalizar_texto


EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9-]+"
    r"(?:\.[A-Za-z0-9-]+)+\b"
)

BAD_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "sentry.io",
    "wixpress.com",
}

SEARCH_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "tiktok.com",
    "tripadvisor.com",
    "google.com",
    "maps.google.com",
    "bing.com",
}

GENERIC_NAME_TOKENS = {
    "club",
    "centro",
    "asociacion",
    "asociación",
    "sociedad",
    "grupo",
    "empresa",
    "servicios",
    "comercio",
    "comercial",
    "colegio",
    "profesional",
    "instituto",
    "municipal",
    "municipalidad",
    "san",
    "santa",
    "del",
    "de",
    "la",
    "el",
    "los",
    "las",
    "y",
    "cordoba",
    "córdoba",
}

BING_SEARCH_URL = "https://www.bing.com/search"

# Seguridad de tiempo:
# no hacemos cientos de búsquedas externas en una sola ejecución.
MAX_BUSQUEDAS_PUBLICAS = 60

BING_TIMEOUT = min(
    max(C.WEB_TIMEOUT, 5),
    8,
)

_busquedas_realizadas = 0


def _es_email_real(value):
    value = normalizar_email(value)

    if not value:
        return ""

    if value.count("@") != 1:
        return ""

    local, domain = value.rsplit("@", 1)

    if not local or not domain:
        return ""

    if domain in BAD_EMAIL_DOMAINS:
        return ""

    if "/" in value or "\\" in value:
        return ""

    if domain.startswith(".") or domain.endswith("."):
        return ""

    if ".." in domain:
        return ""

    if domain in SEARCH_DOMAINS:
        return ""

    return value


def _emails(text):
    encontrados = []

    for value in EMAIL_RE.findall(text or ""):
        email = _es_email_real(value)

        if email and email not in encontrados:
            encontrados.append(email)

    return encontrados


def _dominio_base(url):
    try:
        host = urlparse(url).netloc.lower().split("@")[-1]

        if host.startswith("www."):
            host = host[4:]

        return host

    except Exception:
        return ""


def _extraer_datos_osm(c):
    posibles = (
        c.get("email"),
        c.get("contact:email"),
        c.get("contact_email"),
        c.get("contacto"),
    )

    for value in posibles:
        email = _es_email_real(value)

        if email:
            return email

    return ""


def _tokens_nombre(nombre):
    texto = normalizar_texto(nombre)

    tokens = re.findall(
        r"[a-z0-9]+",
        texto,
    )

    return [
        token
        for token in tokens
        if len(token) >= 3
        and token not in GENERIC_NAME_TOKENS
    ]


def _resultado_score(c, title, snippet):
    nombre = normalizar_texto(
        c.get("name")
    )

    texto = normalizar_texto(
        " ".join(
            [
                title or "",
                snippet or "",
            ]
        )
    )

    tokens = _tokens_nombre(
        c.get("name")
    )

    if not tokens:
        return 0.0

    coincidencias = sum(
        token in texto
        for token in tokens
    )

    cobertura = (
        coincidencias / len(tokens)
    )

    score = cobertura * 0.70

    if (
        nombre
        and nombre in normalizar_texto(title)
    ):
        score += 0.20

    if (
        "cordoba" in texto
        or "córdoba" in texto
    ):
        score += 0.10

    return min(score, 1.0)


def _buscar_resultados_bing(c):
    global _busquedas_realizadas

    if (
        _busquedas_realizadas
        >= MAX_BUSQUEDAS_PUBLICAS
    ):
        return []

    nombre = str(
        c.get("name") or ""
    ).strip()

    if not nombre:
        return []

    direccion = str(
        c.get("direccion") or ""
    ).strip()

    telefono = str(
        c.get("telefono") or ""
    ).strip()

    consulta = (
        f'"{nombre}" Córdoba '
        "email OR correo OR contacto"
    )

    if direccion:
        consulta += f' "{direccion}"'
    elif telefono:
        consulta += f' "{telefono}"'

    _busquedas_realizadas += 1

    try:
        r = requests.get(
            BING_SEARCH_URL,
            params={
                "q": consulta,
                "count": 8,
                "setlang": "es-AR",
                "cc": "ar",
            },
            headers={
                "User-Agent": C.USER_AGENT,
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml"
                ),
                "Accept-Language": (
                    "es-AR,es;q=0.9"
                ),
            },
            timeout=BING_TIMEOUT,
            allow_redirects=True,
        )

        if r.status_code >= 400:
            return []

        soup = BeautifulSoup(
            r.text,
            "html.parser",
        )

        resultados = []

        for item in soup.select(
            "li.b_algo"
        ):
            a = item.select_one(
                "h2 a"
            )

            if not a:
                continue

            href = str(
                a.get("href") or ""
            ).strip()

            if not re.match(
                r"^https?://",
                href,
                re.I,
            ):
                continue

            title = a.get_text(
                " ",
                strip=True,
            )

            p = item.select_one(
                ".b_caption p"
            )

            snippet = (
                p.get_text(
                    " ",
                    strip=True,
                )
                if p
                else item.get_text(
                    " ",
                    strip=True,
                )
            )

            texto_resultado = " ".join(
                [
                    title,
                    snippet,
                ]
            )

            emails = _emails(
                texto_resultado
            )

            score = _resultado_score(
                c,
                title,
                snippet,
            )

            resultados.append(
                {
                    "url": href,
                    "title": title,
                    "snippet": snippet,
                    "score": score,
                    "emails": emails,
                }
            )

        return sorted(
            resultados,
            key=lambda x: (
                bool(x["emails"]),
                x["score"],
            ),
            reverse=True,
        )

    except Exception:
        return []


def _contacto_desde_resultados(
    c,
    resultados,
):
    """
    Acepta solamente emails que aparezcan
    públicamente asociados al resultado buscado.

    No exige que el dominio del email sea igual
    al dominio de la empresa.

    Ejemplo válido:
    Distribuidora Santiago
    -> jlvidela@hotmail.com
    """

    nombre = normalizar_texto(
        c.get("name")
    )

    for item in resultados:
        if item["score"] < 0.72:
            continue

        texto = normalizar_texto(
            " ".join(
                [
                    item.get("title", ""),
                    item.get("snippet", ""),
                ]
            )
        )

        # El resultado debe contener alguna
        # coincidencia razonable con el nombre.
        if nombre:
            tokens = _tokens_nombre(
                c.get("name")
            )

            if tokens:
                coincidencias = sum(
                    token in texto
                    for token in tokens
                )

                if coincidencias == 0:
                    continue

        for email in item.get(
            "emails",
            [],
        ):
            c["email"] = email
            c["email_source"] = (
                "buscador_publico"
            )
            c["email_source_url"] = (
                item["url"]
            )
            c["email_confidence"] = round(
                item["score"],
                2,
            )

            return True

    return False


def _descubrir_contacto(c):
    resultados = _buscar_resultados_bing(c)

    if not resultados:
        return c

    _contacto_desde_resultados(
        c,
        resultados,
    )

    return c


def completar(c):
    """
    Orden de búsqueda:

    1. Email publicado directamente en OSM.
    2. Web publicada en OSM, sólo para compatibilidad.
    3. Búsqueda pública rápida.

    IMPORTANTE:
    Esta versión NO visita las webs encontradas
    por Bing. Eso evita que cientos de candidatos
    conviertan una ejecución en una espera de 20+ minutos.

    El objetivo de esta etapa es encontrar emails
    públicos aunque el negocio no tenga página web.
    """

    # 1. Email directo desde OSM.
    email_original = _extraer_datos_osm(c)

    if email_original:
        c["email"] = email_original
        c["email_source"] = (
            "OpenStreetMap"
        )
        return c

    c["email"] = ""

    # 2. Si OSM trae email oculto en otra variante.
    posibles = (
        c.get("contact:email"),
        c.get("contact_email"),
        c.get("contacto"),
    )

    for value in posibles:
        email = _es_email_real(value)

        if email:
            c["email"] = email
            c["email_source"] = (
                "OpenStreetMap"
            )
            return c

    # 3. Búsqueda pública rápida.
    return _descubrir_contacto(c)
    
