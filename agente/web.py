# agente/web.py

import re
import time
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

from . import config as C


BING_URL = "https://www.bing.com/search"

MAX_BUSQUEDAS_PUBLICAS = 1000
MAX_RESULTADOS_BING = 8
MAX_PAGINAS_POR_RESULTADO = 3

PAUSA_ENTRE_BUSQUEDAS = 0.35
PAUSA_ENTRE_PAGINAS = 0.20

_busquedas_realizadas = 0


# ============================================================
# EMAIL
# ============================================================

# IMPORTANTE:
# No se permite "/" en la parte local.
# Esto evita falsos positivos como:
#
# cdn.jsdelivr.net/npm/photoswipe@5.4...
#
# que NO es un email.
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9.!#$%&'*+=?^_`{|}~-]+"
    r"@"
    r"[A-Za-z0-9-]+"
    r"(?:\.[A-Za-z0-9-]+)+\b"
)


DOMINIOS_EMAIL_DESCARTADOS = {
    "example.com",
    "example.org",
    "example.net",
    "email.com",
    "domain.com",
    "test.com",
    "test.org",
    "localhost",
}


EXTENSIONES_DESCARTADAS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".css",
    ".js",
    ".json",
    ".xml",
    ".woff",
    ".woff2",
    ".ttf",
    ".ico",
}


DOMINIOS_SOCIALES = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "tiktok.com",
    "pinterest.com",
    "threads.net",
}


DOMINIOS_DIRECTORIOS = {
    "google.com",
    "googleusercontent.com",
    "maps.google.com",
    "bing.com",
    "yahoo.com",
    "tripadvisor.com",
    "yelp.com",
    "foursquare.com",
    "yellowpages.com",
    "paginasamarillas.com.ar",
    "guiaoleo.com.ar",
    "argentina.gob.ar",
}


# ============================================================
# UTILIDADES
# ============================================================

def _texto(c):
    partes = []

    for clave in (
        "name",
        "nombre",
        "display_name",
        "direccion",
        "address",
        "descripcion",
        "description",
        "telefono",
        "phone",
        "website",
        "url",
    ):
        valor = c.get(clave)

        if valor:
            partes.append(str(valor))

    tags = c.get("tags") or {}

    if isinstance(tags, dict):
        for clave in (
            "name",
            "official_name",
            "short_name",
            "description",
            "operator",
            "brand",
            "website",
            "contact:website",
            "contact:email",
            "email",
            "phone",
            "contact:phone",
        ):
            valor = tags.get(clave)

            if valor:
                partes.append(str(valor))

    return " ".join(partes)


def _normalizar(texto):
    texto = str(texto or "").lower()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
    }

    for viejo, nuevo in reemplazos.items():
        texto = texto.replace(viejo, nuevo)

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def _dominio(url):
    try:
        host = urlparse(url).netloc.lower().strip()

        if host.startswith("www."):
            host = host[4:]

        return host
    except Exception:
        return ""


def _dominio_base(email):
    try:
        return email.rsplit("@", 1)[1].lower().strip()
    except Exception:
        return ""


def _email_valido(email):
    if not email:
        return False

    email = str(email).strip().lower()

    # Nunca aceptar espacios.
    if any(ch.isspace() for ch in email):
        return False

    # Nunca aceptar barras.
    if "/" in email or "\\" in email:
        return False

    # Nunca aceptar query strings o fragmentos.
    if "?" in email or "#" in email:
        return False

    # Validación estructural.
    if not EMAIL_RE.fullmatch(email):
        return False

    try:
        local, dominio = email.rsplit("@", 1)
    except ValueError:
        return False

    if not local or not dominio:
        return False

    # Límites razonables.
    if len(email) > 254:
        return False

    if len(local) > 64:
        return False

    # El dominio debe tener al menos un punto.
    if "." not in dominio:
        return False

    # No permitir puntos consecutivos.
    if ".." in email:
        return False

    # No permitir dominio con guiones incorrectos.
    partes = dominio.split(".")

    for parte in partes:
        if not parte:
            return False

        if parte.startswith("-") or parte.endswith("-"):
            return False

    # No aceptar dominios de prueba.
    if dominio in DOMINIOS_EMAIL_DESCARTADOS:
        return False

    # No aceptar extensiones de recursos web.
    if any(dominio.endswith(ext) for ext in EXTENSIONES_DESCARTADAS):
        return False

    return True


def _limpiar_email(email):
    if not email:
        return ""

    email = unquote(str(email)).strip().lower()

    # Quitar envolturas habituales.
    email = email.strip(" <>[](){}'\".,;:")

    # Nunca transformar una ruta en email.
    if "/" in email or "\\" in email:
        return ""

    if _email_valido(email):
        return email

    return ""


def _extraer_emails(texto):
    if not texto:
        return []

    encontrados = []

    # Primero decodificamos entidades HTML.
    texto = unquote(str(texto))

    for match in EMAIL_RE.findall(texto):
        email = _limpiar_email(match)

        if email and email not in encontrados:
            encontrados.append(email)

    return encontrados


def _emails_de_pagina(soup):
    encontrados = []

    if not soup:
        return encontrados

    # Texto visible.
    texto = soup.get_text(" ", strip=True)

    for email in _extraer_emails(texto):
        if email not in encontrados:
            encontrados.append(email)

    # mailto:
    for enlace in soup.find_all("a", href=True):
        href = str(enlace.get("href") or "").strip()

        if href.lower().startswith("mailto:"):
            valor = href[7:]

            # El mailto puede contener ?subject=...
            valor = valor.split("?", 1)[0]

            for email in _extraer_emails(valor):
                if email not in encontrados:
                    encontrados.append(email)

    return encontrados


# ============================================================
# IDENTIDAD
# ============================================================

def _tokens(texto):
    texto = _normalizar(texto)

    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", texto)
        if token not in {
            "www",
            "com",
            "org",
            "net",
            "argentina",
            "cordoba",
            "córdoba",
        }
    }


def _identidad_score(c, texto):
    base = " ".join(
        [
            str(c.get("name", "")),
            str(c.get("nombre", "")),
            str(c.get("display_name", "")),
        ]
    )

    tokens_base = _tokens(base)
    tokens_texto = _tokens(texto)

    if not tokens_base or not tokens_texto:
        return 0

    interseccion = tokens_base & tokens_texto

    if not interseccion:
        return 0

    return len(interseccion) / max(1, len(tokens_base))


def _identidad_fuerte(c, texto):
    score = _identidad_score(c, texto)

    if score >= 0.35:
        return True

    # Si aparece el nombre completo, es una señal fuerte.
    nombre = str(
        c.get("name")
        or c.get("nombre")
        or ""
    ).strip()

    if nombre:
        nombre_n = _normalizar(nombre)

        if len(nombre_n) >= 5 and nombre_n in _normalizar(texto):
            return True

    return False


# ============================================================
# HTTP
# ============================================================

def _get(url, headers=None):
    try:
        response = requests.get(
            url,
            headers=headers or {
                "User-Agent": C.USER_AGENT,
                "Accept-Language": "es-AR,es;q=0.9,en;q=0.7",
            },
            timeout=C.WEB_TIMEOUT,
            allow_redirects=True,
        )

        if response.status_code >= 400:
            return None

        return response

    except Exception:
        return None


# ============================================================
# PÁGINA WEB
# ============================================================

def _enlaces_contacto(soup, base_url):
    resultados = []

    if not soup:
        return resultados

    palabras = (
        "contact",
        "contacto",
        "about",
        "nosotros",
        "quienes",
        "empresa",
        "institucional",
        "info",
        "informacion",
        "información",
    )

    for enlace in soup.find_all("a", href=True):
        href = str(enlace.get("href") or "").strip()
        texto = _normalizar(enlace.get_text(" ", strip=True))

        combinado = f"{texto} {href.lower()}"

        if any(palabra in combinado for palabra in palabras):
            try:
                url = urljoin(base_url, href)

                if url.startswith("http"):
                    if url not in resultados:
                        resultados.append(url)
            except Exception:
                pass

    return resultados[:MAX_PAGINAS_POR_RESULTADO]


def _analizar_web(c, url):
    if not url:
        return []

    if not str(url).startswith(("http://", "https://")):
        url = "https://" + str(url).lstrip("/")

    response = _get(url)

    if not response:
        return []

    final_url = response.url or url

    try:
        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )
    except Exception:
        return []

    texto = soup.get_text(" ", strip=True)

    # La página debe guardar relación con el candidato.
    if not _identidad_fuerte(c, texto):
        # Algunas páginas institucionales tienen poco texto visible.
        # En ese caso aceptamos solamente si el dominio coincide con
        # el website declarado por el candidato.
        declarado = str(
            c.get("website")
            or (c.get("tags") or {}).get("website")
            or ""
        )

        if declarado:
            if _dominio(declarado) != _dominio(final_url):
                return []

    encontrados = []

    for email in _emails_de_pagina(soup):
        if email not in encontrados:
            encontrados.append(email)

    # Buscar páginas de contacto si todavía no apareció email.
    if not encontrados:
        for contacto_url in _enlaces_contacto(
            soup,
            final_url,
        ):
            time.sleep(PAUSA_ENTRE_PAGINAS)

            response_contacto = _get(contacto_url)

            if not response_contacto:
                continue

            try:
                soup_contacto = BeautifulSoup(
                    response_contacto.text,
                    "html.parser",
                )
            except Exception:
                continue

            for email in _emails_de_pagina(
                soup_contacto
            ):
                if email not in encontrados:
                    encontrados.append(email)

            if encontrados:
                break

    return encontrados


# ============================================================
# BING
# ============================================================

def _consultas_base(c):
    nombre = str(
        c.get("name")
        or c.get("nombre")
        or ""
    ).strip()

    direccion = str(
        c.get("address")
        or c.get("direccion")
        or ""
    ).strip()

    telefono = str(
        c.get("phone")
        or c.get("telefono")
        or ""
    ).strip()

    consultas = []

    if nombre:
        consultas.extend(
            [
                f'"{nombre}" email',
                f'"{nombre}" contacto',
                f'"{nombre}" correo',
                f'"{nombre}" Córdoba email',
            ]
        )

    if nombre and direccion:
        consultas.append(
            f'"{nombre}" "{direccion}" email'
        )

    if nombre and telefono:
        consultas.append(
            f'"{nombre}" "{telefono}" email'
        )

    if nombre:
        consultas.extend(
            [
                f'"{nombre}" "@gmail.com"',
                f'"{nombre}" "@hotmail.com"',
                f'"{nombre}" "@outlook.com"',
            ]
        )

    return consultas


def _consultas_persona(c):
    nombre = str(
        c.get("name")
        or c.get("nombre")
        or ""
    ).strip()

    direccion = str(
        c.get("address")
        or c.get("direccion")
        or ""
    ).strip()

    telefono = str(
        c.get("phone")
        or c.get("telefono")
        or ""
    ).strip()

    if not nombre:
        return []

    roles = [
        "dueño",
        "propietario",
        "responsable",
        "encargado",
        "titular",
        "director",
        "administrador",
        "contacto",
    ]

    consultas = []

    # Agrupamos los roles para no disparar una consulta por cada uno.
    roles_texto = " OR ".join(
        f'"{rol}"'
        for rol in roles
    )

    consultas.append(
        f'"{nombre}" ({roles_texto}) email'
    )

    consultas.append(
        f'"{nombre}" ({roles_texto}) correo'
    )

    if direccion:
        consultas.append(
            f'"{nombre}" "{direccion}" ({roles_texto}) email'
        )

    if telefono:
        consultas.append(
            f'"{nombre}" "{telefono}" ({roles_texto}) email'
        )

    return consultas


def _ejecutar_busqueda(c, consulta):
    global _busquedas_realizadas

    if _busquedas_realizadas >= MAX_BUSQUEDAS_PUBLICAS:
        return []

    try:
        response = requests.get(
            BING_URL,
            params={
                "q": consulta,
                "count": MAX_RESULTADOS_BING,
                "setlang": "es-AR",
            },
            headers={
                "User-Agent": C.USER_AGENT,
                "Accept-Language": "es-AR,es;q=0.9,en;q=0.7",
            },
            timeout=C.WEB_TIMEOUT,
        )

        _busquedas_realizadas += 1

    except Exception:
        _busquedas_realizadas += 1
        return []

    if response.status_code >= 400:
        return []

    try:
        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )
    except Exception:
        return []

    resultados = []

    for item in soup.select("li.b_algo"):
        enlace = item.select_one("h2 a")

        if not enlace:
            continue

        href = enlace.get("href")

        if not href:
            continue

        titulo = enlace.get_text(" ", strip=True)

        descripcion = ""

        p = item.select_one(".b_caption p")

        if p:
            descripcion = p.get_text(
                " ",
                strip=True,
            )

        resultados.append(
            {
                "url": href,
                "title": titulo,
                "description": descripcion,
            }
        )

    time.sleep(PAUSA_ENTRE_BUSQUEDAS)

    return resultados


def _resultado_valido(c, resultado):
    url = str(resultado.get("url") or "")

    titulo = str(resultado.get("title") or "")

    descripcion = str(
        resultado.get("description")
        or ""
    )

    texto = f"{titulo} {descripcion}"

    dominio = _dominio(url)

    if not dominio:
        return False

    # No usamos resultados de redes sociales como fuente de email.
    if dominio in DOMINIOS_SOCIALES:
        return False

    # Tampoco confiamos en directorios genéricos como identidad final.
    if dominio in DOMINIOS_DIRECTORIOS:
        return False

    # Debe guardar relación con el candidato.
    if not _identidad_fuerte(c, texto):
        return False

    return True


def _buscar_bing(c):
    consultas = _consultas_base(c)

    # Primera etapa: buscar email institucional/comercial.
    for consulta in consultas:
        resultados = _ejecutar_busqueda(
            c,
            consulta,
        )

        for resultado in resultados:
            texto = " ".join(
                [
                    str(resultado.get("title") or ""),
                    str(resultado.get("description") or ""),
                    str(resultado.get("url") or ""),
                ]
            )

            if not _resultado_valido(
                c,
                resultado,
            ):
                continue

            emails = _extraer_emails(texto)

            if emails:
                return emails

    # Segunda etapa: buscar personas responsables.
    consultas_persona = _consultas_persona(c)

    for consulta in consultas_persona:
        resultados = _ejecutar_busqueda(
            c,
            consulta,
        )

        for resultado in resultados:
            texto = " ".join(
                [
                    str(resultado.get("title") or ""),
                    str(resultado.get("description") or ""),
                    str(resultado.get("url") or ""),
                ]
            )

            if not _resultado_valido(
                c,
                resultado,
            ):
                continue

            emails = _extraer_emails(texto)

            if emails:
                return emails

    return []


# ============================================================
# DESCUBRIMIENTO
# ============================================================

def _descubrir(c):
    # Primero buscar directamente en Bing.
    emails = _buscar_bing(c)

    if emails:
        return emails

    # Después visitar website declarado.
    website = str(
        c.get("website")
        or ""
    ).strip()

    if not website:
        tags = c.get("tags") or {}

        if isinstance(tags, dict):
            website = str(
                tags.get("website")
                or tags.get("contact:website")
                or ""
            ).strip()

    if website:
        emails = _analizar_web(
            c,
            website,
        )

        if emails:
            return emails

    return []


# ============================================================
# COMPLETAR CANDIDATO
# ============================================================

def completar(c):
    """
    Intenta completar el email público del candidato.

    Orden:
      1. email de OSM
      2. email de tags
      3. website declarado
      4. búsqueda pública web
      5. búsqueda de responsable/persona asociada
    """

    # --------------------------------------------------------
    # 1. EMAIL YA PRESENTE EN EL CANDIDATO
    # --------------------------------------------------------

    posibles = []

    for clave in (
        "email",
        "contact_email",
        "correo",
    ):
        valor = c.get(clave)

        if valor:
            posibles.extend(
                _extraer_emails(str(valor))
            )

    tags = c.get("tags") or {}

    if isinstance(tags, dict):
        for clave in (
            "email",
            "contact:email",
        ):
            valor = tags.get(clave)

            if valor:
                posibles.extend(
                    _extraer_emails(str(valor))
                )

    # Validar y deduplicar.
    emails_validos = []

    for email in posibles:
        email = _limpiar_email(email)

        if email and email not in emails_validos:
            emails_validos.append(email)

    if emails_validos:
        c["email"] = emails_validos[0]
        c["email_fuente"] = "osm"
        c["contactable"] = True
        return c

    # --------------------------------------------------------
    # 2. WEBSITE
    # --------------------------------------------------------

    website = str(
        c.get("website")
        or ""
    ).strip()

    if not website and isinstance(tags, dict):
        website = str(
            tags.get("website")
            or tags.get("contact:website")
            or ""
        ).strip()

    if website:
        emails = _analizar_web(
            c,
            website,
        )

        if emails:
            c["email"] = emails[0]
            c["email_fuente"] = "website"
            c["contactable"] = True
            c["website"] = website
            return c

    # --------------------------------------------------------
    # 3. BÚSQUEDA PÚBLICA
    # --------------------------------------------------------

    emails = _descubrir(c)

    if emails:
        c["email"] = emails[0]
        c["email_fuente"] = "busqueda_publica"
        c["contactable"] = True
        return c

    # --------------------------------------------------------
    # 4. SIN EMAIL PÚBLICO ENCONTRADO
    # --------------------------------------------------------

    c["email"] = ""
    c["contactable"] = False
    c["email_fuente"] = ""

    return c
