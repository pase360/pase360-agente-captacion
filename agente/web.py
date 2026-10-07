import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from . import config as C
from .util import normalizar_email

EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9-]+"
    r"(?:\.[A-Za-z0-9-]+)+\b"
)

HINTS = (
    "contacto",
    "contact",
    "contactanos",
    "contactenos",
    "nosotros",
    "institucional",
    "empresa",
    "about",
    "quienes",
    "comunicacion",
    "prensa",
    "atencion",
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
}


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


def _fetch(url):
    return requests.get(
        url,
        headers={
            "User-Agent": C.USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.7",
        },
        timeout=C.WEB_TIMEOUT,
        allow_redirects=True,
    )


def _links_relevantes(soup):
    links = []

    for a in soup.find_all("a", href=True):
        href = str(a.get("href") or "").strip()

        if not href:
            continue

        label = (
            a.get_text(" ", strip=True)
            + " "
            + href
        ).lower()

        if any(h in label for h in HINTS):
            links.append(href)

    resultado = []
    vistos = set()

    for href in links:
        if href not in vistos:
            vistos.add(href)
            resultado.append(href)

    return resultado[:15]


def _buscar_en_pagina(url, profundidad=0):
    try:
        r = _fetch(url)

        content_type = r.headers.get(
            "content-type",
            "",
        ).lower()

        if r.status_code >= 400:
            return [], r.url

        if "text/html" not in content_type:
            return [], r.url

        soup = BeautifulSoup(
            r.text,
            "html.parser",
        )

        emails = []

        # Buscar mailto:
        for a in soup.find_all("a", href=True):
            href = str(a.get("href") or "").strip()

            if href.lower().startswith("mailto:"):
                value = href[len("mailto:")].split("?", 1)[0]

                email = _es_email_real(value)

                if email and email not in emails:
                    emails.append(email)

        # Buscar correos visibles en HTML.
        for email in _emails(r.text):
            if email not in emails:
                emails.append(email)

        if emails:
            return emails, r.url

        # Solo una segunda profundidad.
        if profundidad >= 1:
            return [], r.url

        base_host = r.url.split("/", 3)[2].lower()

        # Buscar enlaces de contacto.
        for href in _links_relevantes(soup):
            try:
                target = urljoin(r.url, href)
                target_host = target.split("/", 3)[2].lower()

                if target_host != base_host:
                    continue

                encontrados, final_url = _buscar_en_pagina(
                    target,
                    profundidad=1,
                )

                if encontrados:
                    return encontrados, final_url

            except Exception:
                continue

        # Rutas convencionales.
        rutas = (
            "/contacto",
            "/contactanos",
            "/contactenos",
            "/contact",
            "/institucional",
            "/nosotros",
        )

        for ruta in rutas:
            try:
                target = urljoin(r.url, ruta)

                if target.split("/", 3)[2].lower() != base_host:
                    continue

                encontrados, final_url = _buscar_en_pagina(
                    target,
                    profundidad=1,
                )

                if encontrados:
                    return encontrados, final_url

            except Exception:
                continue

        return [], r.url

    except Exception:
        return [], url


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


def completar(c):
    # 1. Email publicado directamente en OpenStreetMap.
    email_original = _extraer_datos_osm(c)

    if email_original:
        c["email"] = email_original
        c["email_source"] = "OpenStreetMap"
        return c

    c["email"] = ""

    # 2. Sitio web conocido por OSM.
    url = str(
        c.get("website")
        or c.get("contact:website")
        or ""
    ).strip()

    if re.match(r"^https?://", url, re.I):
        emails, final_url = _buscar_en_pagina(url)

        c["website_final"] = final_url

        if emails:
            c["email"] = emails[0]
            c["email_source"] = "sitio_web"
            return c

    # No hacer búsquedas masivas en buscadores externos.
    # Evitamos demoras enormes y asociaciones incorrectas.
    return c
