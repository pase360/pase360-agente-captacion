import re
import time
from urllib.parse import quote, urljoin

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

    # Quitar duplicados conservando orden.
    resultado = []
    vistos = set()

    for href in links:
        if href not in vistos:
            vistos.add(href)
            resultado.append(href)

    return resultado[:12]


def _buscar_en_pagina(url):
    emails = []

    try:
        r = _fetch(url)

        content_type = r.headers.get(
            "content-type", ""
        ).lower()

        if r.status_code >= 400:
            return emails, r.url

        if "text/html" not in content_type:
            return emails, r.url

        soup = BeautifulSoup(
            r.text,
            "html.parser",
        )

        # mailto:
        for a in soup.find_all("a", href=True):
            href = str(
                a.get("href") or ""
            ).strip()

            if href.lower().startswith("mailto:"):
                value = (
                    href[len("mailto:")]
                    .split("?", 1)[0]
                )

                email = _es_email_real(value)

                if email and email not in emails:
                    emails.append(email)

        # Texto visible / código HTML.
        for email in _emails(r.text):
            if email not in emails:
                emails.append(email)

        # Páginas internas de contacto.
        if not emails:
            for href in _links_relevantes(soup):
                try:
                    target = urljoin(
                        r.url,
                        href,
                    )

                    rr = _fetch(target)

                    rr_type = rr.headers.get(
                        "content-type",
                        "",
                    ).lower()

                    if rr.status_code >= 400:
                        continue

                    if "text/html" not in rr_type:
                        continue

                    for email in _emails(rr.text):
                        if email not in emails:
                            emails.append(email)

                    if emails:
                        break

                except Exception:
                    continue

        return emails, r.url

    except Exception:
        return emails, url


def _extraer_datos_osm(c):
    """
    Recupera emails que pueden venir en distintas etiquetas
    de OSM. Algunas fuentes usan email, otras contact:email.
    """
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


def _buscar_en_duckduckgo(c):
    """
    Búsqueda web complementaria.

    Se usa solamente cuando OSM y el sitio web no aportaron
    un email. Busca el nombre exacto + Córdoba y extrae
    emails publicados en los resultados.

    No clasifica al candidato ni convierte un resultado dudoso
    en contacto: solamente aporta un posible email.
    """
    nombre = str(c.get("name") or "").strip()

    if not nombre:
        return ""

    consultas = [
        f'"{nombre}" Córdoba email',
        f'"{nombre}" Córdoba contacto',
    ]

    for consulta in consultas:
        try:
            url = (
                "https://html.duckduckgo.com/html/?q="
                + quote(consulta)
            )

            r = requests.get(
                url,
                headers={
                    "User-Agent": C.USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "es-AR,es;q=0.9",
                },
                timeout=C.WEB_TIMEOUT,
            )

            if r.status_code >= 400:
                continue

            soup = BeautifulSoup(
                r.text,
                "html.parser",
            )

            # Revisamos solamente resultados orgánicos.
            resultados = soup.select(
                ".result, .results_links"
            )

            textos = []

            if resultados:
                for resultado in resultados[:8]:
                    textos.append(
                        resultado.get_text(
                            " ",
                            strip=True,
                        )
                    )
            else:
                textos.append(
                    soup.get_text(
                        " ",
                        strip=True,
                    )
                )

            for texto in textos:
                for email in _emails(texto):
                    dominio = email.rsplit("@", 1)[1]

                    # Evitar correos genéricos de la plataforma
                    # de búsqueda o basura.
                    if dominio in SEARCH_DOMAINS:
                        continue

                    return email

            # Pequeña pausa para no bombardear el buscador.
            time.sleep(1)

        except Exception:
            continue

    return ""


def completar(c):
    # 1. Primero: email existente en OSM.
    email_original = _extraer_datos_osm(c)

    if email_original:
        c["email"] = email_original
        c["email_source"] = "OpenStreetMap"
        return c

    c["email"] = ""

    # 2. Buscar el sitio web conocido por OSM.
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

    # 3. Último recurso: búsqueda web por nombre.
    email_busqueda = _buscar_en_duckduckgo(c)

    if email_busqueda:
        c["email"] = email_busqueda
        c["email_source"] = "busqueda_web"

    return c
