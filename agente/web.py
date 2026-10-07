import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from . import config as C
from .util import normalizar_email, normalizar_texto


EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9-]+"
    r"(?:\.[A-Za-z0-9-]+)+\b"
)

BAD_DOMAINS = {
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
    "bing.com",
}

CONTACT_WORDS = (
    "contact",
    "contacto",
    "contactanos",
    "contactenos",
    "contacta",
    "email",
    "correo",
    "mail",
    "nosotros",
    "quienes-somos",
    "institucional",
)

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

BING_URL = "https://www.bing.com/search"

MAX_BUSQUEDAS_PUBLICAS = 180
MAX_PAGINAS_POR_WEB = 3
MAX_RESULTADOS_BING = 8

_busquedas_realizadas = 0


def _email_real(value):
    value = normalizar_email(value)

    if not value:
        return ""

    local, domain = value.rsplit(
        "@",
        1,
    )

    if not local or not domain:
        return ""

    if domain in BAD_DOMAINS:
        return ""

    if domain in SEARCH_DOMAINS:
        return ""

    if ".." in domain:
        return ""

    return value


def _emails(texto):
    encontrados = []

    for valor in EMAIL_RE.findall(
        texto or ""
    ):
        email = _email_real(valor)

        if (
            email
            and email not in encontrados
        ):
            encontrados.append(email)

    return encontrados


def _dominio(url):
    try:
        host = (
            urlparse(url)
            .netloc
            .lower()
        )

        if host.startswith("www."):
            host = host[4:]

        return host

    except Exception:
        return ""


def _tokens(nombre):
    texto = normalizar_texto(nombre)

    return [
        token
        for token in re.findall(
            r"[a-z0-9]+",
            texto,
        )
        if len(token) >= 3
        and token not in GENERIC_NAME_TOKENS
    ]


def _score(c, title, snippet):
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

    tokens = _tokens(
        c.get("name")
    )

    if not tokens:
        return 0

    coincidencias = sum(
        token in texto
        for token in tokens
    )

    cobertura = (
        coincidencias / len(tokens)
    )

    score = cobertura * 0.7

    if (
        nombre
        and nombre in normalizar_texto(title)
    ):
        score += 0.2

    if (
        "cordoba" in texto
        or "córdoba" in texto
    ):
        score += 0.1

    return min(
        score,
        1.0,
    )


def _get(url):
    try:
        return requests.get(
            url,
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
            timeout=max(
                min(C.WEB_TIMEOUT, 12),
                8,
            ),
            allow_redirects=True,
        )

    except Exception:
        return None


def _emails_de_web(
    c,
    url,
):
    response = _get(url)

    if not response:
        return []

    if response.status_code >= 400:
        return []

    emails = _emails(
        response.text
    )

    if emails:
        return [
            (
                email,
                response.url,
            )
            for email in emails
        ]

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    enlaces = []

    for a in soup.find_all(
        "a",
        href=True,
    ):
        href = str(
            a.get("href") or ""
        ).strip()

        texto = normalizar_texto(
            a.get_text(
                " ",
                strip=True,
            )
        )

        if any(
            palabra in href.lower()
            or palabra in texto
            for palabra in CONTACT_WORDS
        ):
            enlaces.append(
                urljoin(
                    response.url,
                    href,
                )
            )

    vistos = set()

    for enlace in enlaces[
        :MAX_PAGINAS_POR_WEB
    ]:
        if enlace in vistos:
            continue

        vistos.add(enlace)

        time.sleep(0.3)

        pagina = _get(enlace)

        if not pagina:
            continue

        if pagina.status_code >= 400:
            continue

        encontrados = _emails(
            pagina.text
        )

        if encontrados:
            return [
                (
                    email,
                    pagina.url,
                )
                for email in encontrados
            ]

    return []


def _buscar_bing(c):
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
        c.get("phone") or ""
    ).strip()

    consultas = [
        f'"{nombre}" Córdoba email',
        f'"{nombre}" Córdoba contacto',
    ]

    if direccion:
        consultas.append(
            f'"{nombre}" "{direccion}" email'
        )

    if telefono:
        consultas.append(
            f'"{nombre}" "{telefono}" email'
        )

    resultados = []

    for consulta in consultas:
        if (
            _busquedas_realizadas
            >= MAX_BUSQUEDAS_PUBLICAS
        ):
            break

        _busquedas_realizadas += 1

        try:
            response = requests.get(
                BING_URL,
                params={
                    "q": consulta,
                    "count": MAX_RESULTADOS_BING,
                    "setlang": "es-AR",
                    "cc": "ar",
                },
                headers={
                    "User-Agent": C.USER_AGENT,
                    "Accept": "text/html",
                    "Accept-Language": (
                        "es-AR,es;q=0.9"
                    ),
                },
                timeout=max(
                    min(C.WEB_TIMEOUT, 8),
                    6,
                ),
            )

            if response.status_code >= 400:
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

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

                if not href.startswith(
                    "http"
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

                score = _score(
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
                        "emails": _emails(
                            " ".join(
                                [
                                    title,
                                    snippet,
                                ]
                            )
                        ),
                    }
                )

        except Exception:
            continue

        time.sleep(0.5)

    resultados.sort(
        key=lambda x: (
            bool(x["emails"]),
            x["score"],
        ),
        reverse=True,
    )

    return resultados


def _aceptar_resultado(
    c,
    resultado,
):
    score = resultado.get(
        "score",
        0,
    )

    if score < 0.55:
        return False

    nombre = normalizar_texto(
        c.get("name")
    )

    texto = normalizar_texto(
        " ".join(
            [
                resultado.get(
                    "title",
                    "",
                ),
                resultado.get(
                    "snippet",
                    "",
                ),
            ]
        )
    )

    tokens = _tokens(
        c.get("name")
    )

    if tokens:
        coincidencias = sum(
            token in texto
            for token in tokens
        )

        if coincidencias == 0:
            return False

    return bool(
        resultado.get("emails")
        or resultado.get("url")
    )


def _descubrir(c):
    resultados = _buscar_bing(c)

    # Primero: email que aparece directamente
    # en el resultado del buscador.
    for resultado in resultados:
        if not _aceptar_resultado(
            c,
            resultado,
        ):
            continue

        for email in resultado.get(
            "emails",
            [],
        ):
            c["email"] = email
            c["email_source"] = (
                "buscador_publico"
            )
            c["email_source_url"] = (
                resultado["url"]
            )
            c["email_confidence"] = round(
                resultado["score"],
                2,
            )

            return c

    # Segundo: visitar sitios claramente
    # relacionados y buscar contacto.
    for resultado in resultados:
        if not _aceptar_resultado(
            c,
            resultado,
        ):
            continue

        url = resultado.get(
            "url",
            "",
        )

        if not url:
            continue

        dominio = _dominio(url)

        if dominio in SEARCH_DOMAINS:
            continue

        encontrados = _emails_de_web(
            c,
            url,
        )

        if not encontrados:
            continue

        email, origen = encontrados[0]

        c["email"] = email
        c["email_source"] = (
            "web_publica"
        )
        c["email_source_url"] = origen
        c["email_confidence"] = round(
            max(
                resultado.get(
                    "score",
                    0,
                ),
                0.60,
            ),
            2,
        )

        return c

    return c


def completar(c):
    # 1. OSM.
    for campo in (
        "email",
        "contact:email",
        "contact_email",
        "contacto",
    ):
        email = _email_real(
            c.get(campo)
        )

        if email:
            c["email"] = email
            c["email_source"] = (
                "OpenStreetMap"
            )
            c["email_confidence"] = 1.0
            return c

    c["email"] = ""

    # 2. Website ya conocido por OSM.
    website = str(
        c.get("website") or ""
    ).strip()

    if website:
        if not website.startswith(
            ("http://", "https://")
        ):
            website = (
                "https://"
                + website
            )

        encontrados = _emails_de_web(
            c,
            website,
        )

        if encontrados:
            email, origen = encontrados[0]

            c["email"] = email
            c["email_source"] = (
                "web_publica"
            )
            c["email_source_url"] = origen
            c["email_confidence"] = 0.95

            return c

    # 3. Buscador público.
    return _descubrir(c)
