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
)


BAD_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
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

    # Evita cadenas que en realidad son rutas, recursos o basura.
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
            "Accept": "text/html,application/xhtml+xml",
        },
        timeout=C.WEB_TIMEOUT,
        allow_redirects=True,
    )


def _links_relevantes(soup):
    links = []

    for a in soup.find_all("a", href=True):
        href = str(a.get("href") or "").strip()
        label = (
            a.get_text(" ", strip=True)
            + " "
            + href
        ).lower()

        if any(h in label for h in HINTS):
            links.append(href)

    return links[:8]


def completar(c):
    email_original = _es_email_real(
        c.get("email")
    )

    if email_original:
        c["email"] = email_original
        c["email_source"] = "OpenStreetMap"
        return c

    # Si OSM entregó algo que parece email pero no lo es,
    # lo eliminamos antes de continuar.
    c["email"] = ""

    url = str(
        c.get("website")
        or c.get("contact:website")
        or ""
    ).strip()

    if not re.match(
        r"^https?://",
        url,
        re.I,
    ):
        return c

    try:
        r = _fetch(url)

        content_type = (
            r.headers.get("content-type", "")
            .lower()
        )

        if (
            r.status_code >= 400
            or "text/html" not in content_type
        ):
            return c

        c["website_final"] = r.url

        soup = BeautifulSoup(
            r.text,
            "html.parser",
        )

        # ----------------------------------------------------
        # Primero buscamos correos visibles/enlaces mailto.
        # ----------------------------------------------------
        emails = []

        for a in soup.find_all(
            "a",
            href=True,
        ):
            href = str(
                a.get("href") or ""
            ).strip()

            if href.lower().startswith(
                "mailto:"
            ):
                value = href[
                    len("mailto:"):
                ].split("?", 1)[0]

                email = _es_email_real(
                    value
                )

                if (
                    email
                    and email not in emails
                ):
                    emails.append(email)

        # ----------------------------------------------------
        # Después buscamos correos en HTML.
        # ----------------------------------------------------
        for email in _emails(r.text):
            if email not in emails:
                emails.append(email)

        # ----------------------------------------------------
        # Finalmente revisamos páginas de contacto.
        # ----------------------------------------------------
        if not emails:
            for href in _links_relevantes(
                soup
            ):
                try:
                    target = urljoin(
                        r.url,
                        href,
                    )

                    rr = _fetch(target)

                    rr_type = (
                        rr.headers.get(
                            "content-type",
                            "",
                        ).lower()
                    )

                    if (
                        rr.status_code >= 400
                        or "text/html"
                        not in rr_type
                    ):
                        continue

                    for email in _emails(
                        rr.text
                    ):
                        if email not in emails:
                            emails.append(
                                email
                            )

                    if emails:
                        break

                except Exception:
                    continue

        if emails:
            c["email"] = emails[0]
            c["email_source"] = (
                "sitio_web"
            )

    except Exception as exc:
        c["web_error"] = str(exc)[:180]

    return c
