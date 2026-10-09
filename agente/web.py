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

    if any(ch.isspace() for ch in email):
        return False

    if "/" in email or "\\" in email:
        return False

    if "?" in email or "#" in email:
        return False

    if not EMAIL_RE.fullmatch(email):
        return False

    try:
        local, dominio = email.rsplit("@", 1)
    except ValueError:
        return False

    if not local or not dominio:
        return False

    if len(email) > 254:
        return False

    if len(local) > 64:
        return False

    if "." not in dominio:
        return False

    if ".." in email:
        return False

    partes = dominio.split(".")

    for parte in partes:
        if not parte:
            return False

        if parte.startswith("-") or parte.endswith("-"):
            return False

    if dominio in DOMINIOS_EMAIL_DESCARTADOS:
        return False

    if any(dominio.endswith(ext) for ext in EXTENSIONES_DESCARTADAS):
        return False

    return True


def _limpiar_email(email):
    if not email:
        return ""

    email = unquote(str(email)).strip().lower()

    email = email.strip(" <>[](){}'\".,;:")

    if "/" in email or "\\" in email:
        return ""

    if _email_valido(email):
        return email

    return ""


def _extraer_emails(texto):
    if not texto:
        return []

    encontrados = []

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

    texto = soup.get_text(" ", strip=True)

    for email in _extraer_emails(texto):
        if email not in encontrados:
            encontrados.append(email)

    for enlace in soup.find_all("a", href=True):
        href = str(enlace.get("href") or "").strip()

        if href.lower().startswith("mailto:"):
            valor = href[7:]

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
        "staff",
        "equipo",
        "autoridades",
    )

    for enlace in soup.find_all("a", href=True):
        href = str(enlace.get("href") or "").strip()

        texto = _normalizar(
            enlace.get_text(" ", strip=True)
        )

        combinado = f"{texto} {href.lower()}"

        if any(palabra in combinado for palabra in palabras):
            try:
                url = urljoin(base_url, href)

                if (
                    url.startswith(("http://", "https://"))
                    and _dominio(url) == _dominio(base_url)
                    and url not in resultados
                ):
                    resultados.append(url)

            except Exception:
                pass

    return resultados[:MAX_PAGINAS_POR_RESULTADO]


def _analizar_web(c, url):
    if not url:
        return []

    if not str(url).startswith(
        ("http://", "https://")
    ):
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

    if not _identidad_fuerte(c, texto):
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

    if encontrados:
        return encontrados

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
        "presidente",
        "secretario",
        "contacto",
    ]

    consultas = []

    for rol in roles:
        consultas.append(
            f'"{nombre}" "{rol}" email'
        )

    if direccion:
        consultas.extend(
            [
                f'"{nombre}" "{direccion}" responsable email',
                f'"{nombre}" "{direccion}" dueño email',
                f'"{nombre}" "{direccion}" propietario email',
            ]
        )

    if telefono:
        consultas.extend(
            [
                f'"{nombre}" "{telefono}" responsable email',
                f'"{nombre}" "{telefono}" dueño email',
            ]
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

        titulo = enlace.get_text(
            " ",
            strip=True,
        )

        descripcion = ""

        p = item.select_one(
            ".b_caption p"
        )

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
    url = str(
        resultado.get("url")
        or ""
    )

    titulo = str(
        resultado.get("title")
        or ""
    )

    descripcion = str(
        resultado.get("description")
        or ""
    )

    texto = f"{titulo} {descripcion}"

    dominio = _dominio(url)

    if not dominio:
        return False

    if dominio in DOMINIOS_SOCIALES:
        return False

    if dominio in DOMINIOS_DIRECTORIOS:
        return False

    if not _identidad_fuerte(
        c,
        texto,
    ):
        return False

    return True


def _extraer_de_resultados(c, resultados):
    """
    Revisa resultados públicos relevantes.

    Primero busca el email en el resultado.
    Si no aparece, entra a la página real y busca
    emails publicados en ella o en sus páginas de contacto.
    """

    for resultado in resultados:
        if not _resultado_valido(
            c,
            resultado,
        ):
            continue

        texto = " ".join(
            [
                str(
                    resultado.get("title")
                    or ""
                ),
                str(
                    resultado.get("description")
                    or ""
                ),
                str(
                    resultado.get("url")
                    or ""
                ),
            ]
        )

        # Email visible directamente en el resultado.
        emails = _extraer_emails(texto)

        if emails:
            return emails

        # Si no está en el resultado,
        # visitar la página encontrada.
        url = str(
            resultado.get("url")
            or ""
        ).strip()

        if not url:
            continue

        emails = _analizar_web(
            c,
            url,
        )

        if emails:
            return emails

    return []


def _buscar_bing(c):
    # --------------------------------------------------------
    # PRIMERA ETAPA:
    # NEGOCIO / ORGANIZACIÓN
    # --------------------------------------------------------

    # Tres consultas diferentes por candidato como máximo. Reduce redundancia
    # y permite que el presupuesto global alcance a más organizaciones.
    consultas = _consultas_base(c)[:3]

    for consulta in consultas:
        resultados = _ejecutar_busqueda(
            c,
            consulta,
        )

        emails = _extraer_de_resultados(
            c,
            resultados,
        )

        if emails:
            return emails

        if (
            _busquedas_realizadas
            >= MAX_BUSQUEDAS_PUBLICAS
        ):
            return []

    # Evitar decenas de consultas por candidato. La búsqueda se
    # mantiene acotada para que los generadores no queden sin turno.
    return []


# ============================================================
# DESCUBRIMIENTO
# ============================================================

def _descubrir(c):
    # Primero revisar la web oficial ya declarada: es más precisa
    # y evita gastar búsquedas públicas innecesarias.
    website = str(
        c.get("website")
        or ""
    ).strip()

    tags = c.get("tags") or {}
    if not website and isinstance(tags, dict):
        website = str(
            tags.get("website")
            or tags.get("contact:website")
            or ""
        ).strip()

    if website:
        emails = _analizar_web(c, website)
        if emails:
            return emails

    # Solo si la web oficial no aporta email, buscar en fuentes públicas.
    return _buscar_bing(c)


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
      4. búsqueda pública del negocio
      5. visita de páginas encontradas
      6. búsqueda pública de responsables/personas

    Nunca inventa ni construye emails.
    Solo acepta direcciones que aparecen públicamente.
    """

    # --------------------------------------------------------
    # 1. EMAIL YA PRESENTE
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
                _extraer_emails(
                    str(valor)
                )
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
                    _extraer_emails(
                        str(valor)
                    )
                )

    emails_validos = []

    for email in posibles:
        email = _limpiar_email(email)

        if (
            email
            and email not in emails_validos
        ):
            emails_validos.append(email)

    if emails_validos:
        c["email"] = emails_validos[0]
        c["email_fuente"] = "osm"
        c["contactable"] = True
        return c

    # --------------------------------------------------------
    # 2. WEBSITE DECLARADO
    # --------------------------------------------------------

    website = str(
        c.get("website")
        or ""
    ).strip()

    if not website and isinstance(
        tags,
        dict,
    ):
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
