import re
import time
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

from . import config as C
from .util import normalizar_email, normalizar_texto


EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9-]+"
    r"(?:\.[A-Za-z0-9-]+)+\b"
)


# ============================================================
# DOMINIOS QUE NO SON EMAILS ÚTILES
# ============================================================

BAD_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "sentry.io",
    "wixpress.com",
    "schema.org",
    "wordpress.org",
    "wordpress.com",
    "googleapis.com",
    "gstatic.com",
    "jsdelivr.net",
    "cloudflare.com",
    "cloudflareinsights.com",
}

BAD_EMAIL_EXTENSIONS = (
    ".js",
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
)

SOCIAL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "tiktok.com",
    "tripadvisor.com",
    "google.com",
    "googleusercontent.com",
    "bing.com",
}


# ============================================================
# DIRECTORIOS PÚBLICOS
# ============================================================

DIRECTORIOS = (
    "guiacordoba.com.ar",
    "direccionario.com",
    "dir.ar",
)

BING_URL = "https://www.bing.com/search"

MAX_BUSQUEDAS_PUBLICAS = 1000
MAX_RESULTADOS_BING = 10
MAX_PAGINAS_POR_RESULTADO = 4

PAUSA_ENTRE_BUSQUEDAS = 0.45
PAUSA_ENTRE_PAGINAS = 0.25

_busquedas_realizadas = 0


# ============================================================
# EMAIL
# ============================================================

def _email_real(value):
    value = normalizar_email(value)

    if not value:
        return ""

    if "@" not in value:
        return ""

    local, domain = value.rsplit("@", 1)

    if not local or not domain:
        return ""

    domain = domain.lower().strip()

    if domain in BAD_EMAIL_DOMAINS:
        return ""

    if domain in SOCIAL_DOMAINS:
        return ""

    if ".." in domain:
        return ""

    if any(
        domain.endswith(ext)
        for ext in BAD_EMAIL_EXTENSIONS
    ):
        return ""

    if local.lower() in {
        "noreply",
        "no-reply",
        "donotreply",
        "no_reply",
        "example",
        "test",
        "testing",
    }:
        return ""

    return value


def _emails(texto):
    encontrados = []

    if not texto:
        return encontrados

    for valor in EMAIL_RE.findall(
        texto
    ):
        email = _email_real(valor)

        if (
            email
            and email not in encontrados
        ):
            encontrados.append(
                email
            )

    return encontrados


# ============================================================
# URL / DOMINIO
# ============================================================

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


def _es_directorio(url):
    dominio = _dominio(url)

    return any(
        dominio == d
        or dominio.endswith("." + d)
        for d in DIRECTORIOS
    )


def _es_social(url):
    dominio = _dominio(url)

    return any(
        dominio == d
        or dominio.endswith("." + d)
        for d in SOCIAL_DOMAINS
    )


# ============================================================
# IDENTIDAD
# ============================================================

GENERICOS = {
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


def _tokens(nombre):
    texto = normalizar_texto(
        nombre
    )

    return [
        token
        for token in re.findall(
            r"[a-z0-9]+",
            texto,
        )
        if len(token) >= 3
        and token not in GENERICOS
    ]


def _identidad_score(c, texto):
    nombre = normalizar_texto(
        c.get("name")
    )

    texto_normalizado = normalizar_texto(
        texto
    )

    tokens = _tokens(
        c.get("name")
    )

    if not tokens:
        return 0.0

    coincidencias = sum(
        token in texto_normalizado
        for token in tokens
    )

    cobertura = (
        coincidencias / len(tokens)
    )

    score = cobertura * 0.75

    if (
        nombre
        and nombre in texto_normalizado
    ):
        score += 0.20

    if (
        "cordoba" in texto_normalizado
        or "córdoba" in texto_normalizado
    ):
        score += 0.05

    return min(
        score,
        1.0,
    )


def _identidad_fuerte(c, texto):
    score = _identidad_score(
        c,
        texto,
    )

    tokens = _tokens(
        c.get("name")
    )

    if not tokens:
        return False

    texto_n = normalizar_texto(
        texto
    )

    coincidencias = sum(
        token in texto_n
        for token in tokens
    )

    if len(tokens) == 1:
        return (
            coincidencias >= 1
            and score >= 0.65
        )

    nombre = normalizar_texto(
        c.get("name")
    )

    if nombre in texto_n:
        return True

    return (
        coincidencias >= 2
        and score >= 0.55
    )


# ============================================================
# HTTP
# ============================================================

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


# ============================================================
# EMAIL DESDE PÁGINA
# ============================================================

def _emails_de_pagina(
    c,
    response,
):
    if not response:
        return []

    if response.status_code >= 400:
        return []

    html = response.text or ""

    encontrados = []

    # --------------------------------------------------------
    # HTML COMPLETO
    # --------------------------------------------------------

    for email in _emails(html):
        if email not in encontrados:
            encontrados.append(
                email
            )

    # --------------------------------------------------------
    # TEXTO VISIBLE + MAILTO
    # --------------------------------------------------------

    try:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        for tag in soup(
            [
                "script",
                "style",
                "noscript",
            ]
        ):
            tag.extract()

        texto = soup.get_text(
            " ",
            strip=True,
        )

        for email in _emails(
            texto
        ):
            if email not in encontrados:
                encontrados.append(
                    email
                )

        for enlace in soup.find_all(
            "a",
            href=True,
        ):
            href = str(
                enlace.get("href") or ""
            ).strip()

            if not href.lower().startswith(
                "mailto:"
            ):
                continue

            valor = unquote(
                href[7:]
            ).split(
                "?",
                1,
            )[0]

            email = _email_real(
                valor
            )

            if (
                email
                and email not in encontrados
            ):
                encontrados.append(
                    email
                )

    except Exception:
        pass

    return encontrados


# ============================================================
# ENLACES DE CONTACTO
# ============================================================

CONTACT_WORDS = (
    "contact",
    "contacto",
    "contactanos",
    "contactenos",
    "contactá",
    "contacta",
    "correo",
    "email",
    "mail",
    "nosotros",
    "institucional",
    "quienes somos",
    "quienes-somos",
    "ubicacion",
    "ubicación",
)


def _enlaces_contacto(response):
    if not response:
        return []

    try:
        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

    except Exception:
        return []

    resultado = []
    vistos = set()

    for a in soup.find_all(
        "a",
        href=True,
    ):
        href = str(
            a.get("href") or ""
        ).strip()

        if not href:
            continue

        texto = normalizar_texto(
            a.get_text(
                " ",
                strip=True,
            )
        )

        href_n = normalizar_texto(
            href
        )

        if not any(
            palabra in texto
            or palabra in href_n
            for palabra in CONTACT_WORDS
        ):
            continue

        url = urljoin(
            response.url,
            href,
        )

        if url in vistos:
            continue

        vistos.add(url)
        resultado.append(url)

    return resultado


# ============================================================
# ANALIZAR WEB
# ============================================================

def _analizar_web(
    c,
    url,
):
    if not url:
        return []

    if not url.startswith(
        (
            "http://",
            "https://",
        )
    ):
        url = (
            "https://"
            + url
        )

    response = _get(url)

    if not response:
        return []

    if response.status_code >= 400:
        return []

    contenido = (
        response.url
        + " "
        + response.text
    )

    identidad = _identidad_score(
        c,
        contenido,
    )

    es_directorio = _es_directorio(
        response.url
    )

    if not es_directorio:
        if identidad < 0.45:
            return []

    resultados = []

    for email in _emails_de_pagina(
        c,
        response,
    ):
        resultados.append(
            (
                email,
                response.url,
                identidad,
            )
        )

    # --------------------------------------------------------
    # PÁGINAS DE CONTACTO
    # --------------------------------------------------------

    if not resultados:
        enlaces = _enlaces_contacto(
            response
        )

        for enlace in enlaces[
            :MAX_PAGINAS_POR_RESULTADO
        ]:
            time.sleep(
                PAUSA_ENTRE_PAGINAS
            )

            pagina = _get(
                enlace
            )

            if not pagina:
                continue

            if pagina.status_code >= 400:
                continue

            contenido_pagina = (
                pagina.url
                + " "
                + pagina.text
            )

            identidad_pagina = (
                _identidad_score(
                    c,
                    contenido_pagina,
                )
            )

            if (
                not es_directorio
                and identidad_pagina < 0.45
            ):
                continue

            for email in _emails_de_pagina(
                c,
                pagina,
            ):
                resultados.append(
                    (
                        email,
                        pagina.url,
                        max(
                            identidad,
                            identidad_pagina,
                        ),
                    )
                )

            if resultados:
                break

    return resultados


# ============================================================
# CONSULTAS PÚBLICAS
# ============================================================

def _consultas(c):
    nombre = str(
        c.get("name") or ""
    ).strip()

    direccion = str(
        c.get("direccion") or ""
    ).strip()

    telefono = str(
        c.get("phone") or ""
    ).strip()

    consultas = []

    # --------------------------------------------------------
    # NEGOCIO / ORGANIZACIÓN
    # --------------------------------------------------------

    consultas.append(
        f'"{nombre}" Córdoba email'
    )

    consultas.append(
        f'"{nombre}" Córdoba contacto email'
    )

    # --------------------------------------------------------
    # DIRECCIÓN
    # --------------------------------------------------------

    if direccion:
        consultas.append(
            f'"{nombre}" "{direccion}" email'
        )

    # --------------------------------------------------------
    # TELÉFONO
    # --------------------------------------------------------

    if telefono:
        consultas.append(
            f'"{nombre}" "{telefono}" email'
        )

    # --------------------------------------------------------
    # DIRECTORIOS
    # --------------------------------------------------------

    for dominio in DIRECTORIOS:
        consultas.append(
            f'"{nombre}" Córdoba '
            f'email site:{dominio}'
        )

    # --------------------------------------------------------
    # PERSONAS VINCULADAS
    #
    # Buscamos solamente asociaciones públicas.
    # Nunca generamos una dirección por nuestra cuenta.
    # --------------------------------------------------------

    roles = (
        "dueño",
        "dueña",
        "propietario",
        "propietaria",
        "responsable",
        "encargado",
        "encargada",
        "titular",
        "director",
        "directora",
        "administrador",
        "administradora",
        "contacto",
    )

    for rol in roles:
        consultas.append(
            f'"{nombre}" Córdoba "{rol}" email'
        )

    # --------------------------------------------------------
    # TELÉFONO + PERSONA
    # --------------------------------------------------------

    if telefono:
        for rol in (
            "dueño",
            "propietario",
            "responsable",
            "titular",
            "director",
        ):
            consultas.append(
                f'"{telefono}" "{rol}" email'
            )

    # --------------------------------------------------------
    # DIRECCIÓN + PERSONA
    # --------------------------------------------------------

    if direccion:
        for rol in (
            "dueño",
            "propietario",
            "responsable",
            "titular",
            "director",
        ):
            consultas.append(
                f'"{direccion}" "{rol}" email'
            )

    return consultas


# ============================================================
# BÚSQUEDA BING
# ============================================================

def _buscar_bing(c):
    global _busquedas_realizadas

    if (
        _busquedas_realizadas
        >= MAX_BUSQUEDAS_PUBLICAS
    ):
        return []

    resultados = []
    vistos = set()

    consultas = _consultas(c)

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
                    min(C.WEB_TIMEOUT, 10),
                    7,
                ),
            )

            if response.status_code >= 400:
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            items = soup.select(
                "li.b_algo"
            )

            for item in items:

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

                if href in vistos:
                    continue

                vistos.add(href)

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

                contenido = (
                    title
                    + " "
                    + snippet
                    + " "
                    + href
                )

                score = _identidad_score(
                    c,
                    contenido,
                )

                resultados.append(
                    {
                        "url": href,
                        "title": title,
                        "snippet": snippet,
                        "score": score,
                        "emails": _emails(
                            contenido
                        ),
                    }
                )

        except Exception:
            pass

        time.sleep(
            PAUSA_ENTRE_BUSQUEDAS
        )

    resultados.sort(
        key=lambda x: (
            bool(
                x.get("emails")
            ),
            _es_directorio(
                x.get(
                    "url",
                    "",
                )
            ),
            x.get(
                "score",
                0,
            ),
        ),
        reverse=True,
    )

    return resultados


# ============================================================
# VALIDACIÓN
# ============================================================

def _resultado_valido(
    c,
    resultado,
):
    url = resultado.get(
        "url",
        "",
    )

    title = resultado.get(
        "title",
        "",
    )

    snippet = resultado.get(
        "snippet",
        "",
    )

    contenido = " ".join(
        [
            title,
            snippet,
            url,
        ]
    )

    score = _identidad_score(
        c,
        contenido,
    )

    if _es_directorio(url):
        return (
            score >= 0.45
            or normalizar_texto(
                c.get("name")
            )
            in normalizar_texto(
                contenido
            )
        )

    return score >= 0.55


# ============================================================
# DESCUBRIMIENTO
# ============================================================

def _descubrir(c):
    resultados = _buscar_bing(c)

    # --------------------------------------------------------
    # EMAIL YA VISIBLE EN LOS RESULTADOS
    # --------------------------------------------------------

    candidatos_email = []

    for resultado in resultados:

        if not _resultado_valido(
            c,
            resultado,
        ):
            continue

        for email in resultado.get(
            "emails",
            [],
        ):
            candidatos_email.append(
                (
                    email,
                    resultado.get(
                        "url",
                        "",
                    ),
                    resultado.get(
                        "score",
                        0,
                    ),
                )
            )

    if candidatos_email:
        candidatos_email.sort(
            key=lambda x: (
                x[2],
                _es_directorio(
                    x[1]
                ),
            ),
            reverse=True,
        )

        email, origen, score = (
            candidatos_email[0]
        )

        c["email"] = email
        c["email_source"] = (
            "busqueda_publica"
        )
        c["email_source_url"] = (
            origen
        )
        c["email_confidence"] = round(
            max(
                score,
                0.60,
            ),
            2,
        )

        return c

    # --------------------------------------------------------
    # VISITAR RESULTADOS RELEVANTES
    # --------------------------------------------------------

    mejores = [
        r
        for r in resultados
        if _resultado_valido(
            c,
            r,
        )
    ]

    mejores.sort(
        key=lambda r: (
            not _es_social(
                r.get(
                    "url",
                    "",
                )
            ),
            _es_directorio(
                r.get(
                    "url",
                    "",
                )
            ),
            r.get(
                "score",
                0,
            ),
        ),
        reverse=True,
    )

    vistos = set()

    for resultado in mejores[
        :MAX_RESULTADOS_BING
    ]:

        url = resultado.get(
            "url",
            "",
        )

        if not url:
            continue

        if url in vistos:
            continue

        vistos.add(url)

        if _es_social(url):
            continue

        encontrados = _analizar_web(
            c,
            url,
        )

        if not encontrados:
            continue

        encontrados.sort(
            key=lambda x: (
                x[2],
                x[0].startswith(
                    "info@"
                ),
                x[0].startswith(
                    "contact"
                ),
            ),
            reverse=True,
        )

        email, origen, identidad = (
            encontrados[0]
        )

        c["email"] = email

        c["email_source"] = (
            "directorio_publico"
            if _es_directorio(
                origen
            )
            else "web_publica"
        )

        c["email_source_url"] = (
            origen
        )

        c["email_confidence"] = round(
            max(
                identidad,
                0.60,
            ),
            2,
        )

        return c

    return c


# ============================================================
# ENRIQUECIMIENTO PRINCIPAL
# ============================================================

def completar(c):

    # --------------------------------------------------------
    # 1. EMAIL YA PUBLICADO EN OSM
    # --------------------------------------------------------

    campos = (
        "email",
        "contact:email",
        "contact_email",
        "contacto",
    )

    for campo in campos:

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

    # --------------------------------------------------------
    # 2. SITIO WEB DEL NEGOCIO / ORGANIZACIÓN
    # --------------------------------------------------------

    website = str(
        c.get("website") or ""
    ).strip()

    if website:

        if not website.startswith(
            (
                "http://",
                "https://",
            )
        ):
            website = (
                "https://"
                + website
            )

        encontrados = _analizar_web(
            c,
            website,
        )

        if encontrados:

            encontrados.sort(
                key=lambda x: (
                    x[2],
                    x[0].startswith(
                        "info@"
                    ),
                ),
                reverse=True,
            )

            email, origen, identidad = (
                encontrados[0]
            )

            c["email"] = email

            c["email_source"] = (
                "web_publica"
            )

            c["email_source_url"] = (
                origen
            )

            c["email_confidence"] = round(
                max(
                    identidad,
                    0.75,
                ),
                2,
            )

            return c

    # --------------------------------------------------------
    # 3. BÚSQUEDA PÚBLICA PROFUNDA
    # --------------------------------------------------------

    return _descubrir(c)
