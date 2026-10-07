import re
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
    "bing.com",
}

NO_OFICIAL_DOMAINS = SEARCH_DOMAINS | {
    "pinterest.com",
    "yelp.com",
    "paginasamarillas.com.ar",
    "guia.clarin.com",
    "argentina.gob.ar",
    "wikipedia.org",
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
BING_TIMEOUT = min(max(C.WEB_TIMEOUT, 8), 12)


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


def _fetch(url, timeout=None):
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
        timeout=timeout or C.WEB_TIMEOUT,
        allow_redirects=True,
    )


def _dominio_base(url):
    try:
        host = urlparse(url).netloc.lower().split("@")[-1]

        if host.startswith("www."):
            host = host[4:]

        return host

    except Exception:
        return ""


def _es_dominio_no_oficial(url):
    host = _dominio_base(url)

    if not host:
        return True

    for blocked in NO_OFICIAL_DOMAINS:
        if host == blocked or host.endswith("." + blocked):
            return True

    return False


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

        for a in soup.find_all("a", href=True):
            href = str(a.get("href") or "").strip()

            if href.lower().startswith("mailto:"):
                value = href[len("mailto:")].split("?", 1)[0]

                email = _es_email_real(value)

                if email and email not in emails:
                    emails.append(email)

        for email in _emails(r.text):
            if email not in emails:
                emails.append(email)

        if emails:
            return emails, r.url

        if profundidad >= 1:
            return [], r.url

        base_host = _dominio_base(r.url)

        for href in _links_relevantes(soup):
            try:
                target = urljoin(r.url, href)

                if _dominio_base(target) != base_host:
                    continue

                encontrados, final_url = _buscar_en_pagina(
                    target,
                    profundidad=1,
                )

                if encontrados:
                    return encontrados, final_url

            except Exception:
                continue

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

                if _dominio_base(target) != base_host:
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


def _resultado_score(c, title, snippet, url):
    nombre = normalizar_texto(
        c.get("name")
    )

    texto = normalizar_texto(
        " ".join(
            [
                title or "",
                snippet or "",
                url or "",
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

    score = cobertura * 0.65

    if (
        nombre
        and nombre in normalizar_texto(title)
    ):
        score += 0.25

    if (
        "cordoba" in texto
        or "córdoba" in texto
    ):
        score += 0.10

    direccion = normalizar_texto(
        c.get("direccion")
    )

    if direccion:
        direccion_tokens = [
            x
            for x in re.findall(
                r"[a-z0-9]+",
                direccion,
            )
            if len(x) >= 4
        ]

        if any(
            x in texto
            for x in direccion_tokens[:4]
        ):
            score += 0.10

    return min(score, 1.0)


def _buscar_resultados_bing(c):
    nombre = str(
        c.get("name") or ""
    ).strip()

    if not nombre:
        return []

    direccion = str(
        c.get("direccion") or ""
    ).strip()

    consultas = [
        f'"{nombre}" Córdoba Argentina',
    ]

    if direccion:
        consultas.append(
            f'"{nombre}" "{direccion}" Córdoba'
        )
    else:
        consultas.append(
            f'"{nombre}" Córdoba contacto'
        )

    resultados = []

    for consulta in consultas:
        try:
            r = requests.get(
                BING_SEARCH_URL,
                params={
                    "q": consulta,
                    "count": 5,
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
                continue

            soup = BeautifulSoup(
                r.text,
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

                if not re.match(
                    r"^https?://",
                    href,
                    re.I,
                ):
                    continue

                if _es_dominio_no_oficial(
                    href
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

                score = _resultado_score(
                    c,
                    title,
                    snippet,
                    href,
                )

                resultados.append(
                    {
                        "url": href,
                        "title": title,
                        "snippet": snippet,
                        "score": score,
                    }
                )

        except Exception:
            continue

    unicos = {}

    for item in resultados:
        host = _dominio_base(
            item["url"]
        )

        if not host:
            continue

        anterior = unicos.get(host)

        if (
            not anterior
            or item["score"]
            > anterior["score"]
        ):
            unicos[host] = item

    return sorted(
        unicos.values(),
        key=lambda x: x["score"],
        reverse=True,
    )


def _descubrir_sitio(c):
    resultados = _buscar_resultados_bing(c)

    if not resultados:
        return c

    mejor = resultados[0]

    # Umbral alto para evitar asociar
    # una web de otra entidad.
    if mejor["score"] < 0.78:
        return c

    url = mejor["url"]

    c["website"] = url
    c["website_final"] = url
    c["website_source"] = "Bing"
    c["website_confidence"] = round(
        mejor["score"],
        2,
    )

    emails, final_url = _buscar_en_pagina(
        url
    )

    c["website_final"] = final_url

    if emails:
        c["email"] = emails[0]
        c["email_source"] = (
            "sitio_web_descubierto"
        )

    return c


def completar(c):
    # 1. Email publicado directamente
    # en OpenStreetMap.
    email_original = _extraer_datos_osm(c)

    if email_original:
        c["email"] = email_original
        c["email_source"] = (
            "OpenStreetMap"
        )
        return c

    c["email"] = ""

    # 2. Sitio web conocido por OSM.
    url = str(
        c.get("website")
        or c.get("contact:website")
        or ""
    ).strip()

    if re.match(
        r"^https?://",
        url,
        re.I,
    ):
        emails, final_url = (
            _buscar_en_pagina(url)
        )

        c["website_final"] = final_url

        if emails:
            c["email"] = emails[0]
            c["email_source"] = (
                "sitio_web"
            )
            return c

    # 3. Si OSM no tenía web,
    # descubrir sitio oficial.
    return _descubrir_sitio(c)
