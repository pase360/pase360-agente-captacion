# agente/github_issues.py

import os
import hashlib
import requests


API_BASE = "https://api.github.com"


def _config():
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repo = os.getenv("GITHUB_REPOSITORY", "").strip()
    return token, repo


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _clave(c):
    """
    Genera una identificación estable para el candidato.
    No modifica ni reemplaza la clave usada por Captación.
    """

    partes = [
        str(c.get("name") or "").strip().lower(),
        str(c.get("email") or "").strip().lower(),
        str(c.get("phone") or "").strip().lower(),
        str(c.get("direccion") or "").strip().lower(),
        str(c.get("website") or "").strip().lower(),
    ]

    texto = "|".join(partes)

    return hashlib.sha256(
        texto.encode("utf-8")
    ).hexdigest()[:16]


def crear_pregunta(c, motivo):
    """
    Crea un Issue de GitHub para una clasificación dudosa.

    Esta función NO envía correos.
    Por eso funciona también cuando MODO_PRUEBA está activo.
    """

    token, repo = _config()

    if not token or not repo:
        return {
            "ok": False,
            "motivo": (
                "faltan "
                "GITHUB_TOKEN/GITHUB_REPOSITORY"
            ),
        }

    nombre = str(
        c.get("name")
        or "sin nombre"
    ).strip()

    tipo = str(
        c.get("tipo")
        or "dudoso"
    ).strip()

    email = str(
        c.get("email")
        or ""
    ).strip()

    website = str(
        c.get("website")
        or c.get("website_final")
        or ""
    ).strip()

    telefono = str(
        c.get("phone")
        or ""
    ).strip()

    direccion = str(
        c.get("direccion")
        or ""
    ).strip()

    clave = _clave(c)

    body = (
        "### El agente necesita una decisión humana\n\n"
        f"**Prospecto:** {nombre}\n\n"
        f"**Tipo propuesto:** {tipo}\n\n"
        f"**Email:** {email}\n\n"
        f"**Website:** {website}\n\n"
        f"**Teléfono:** {telefono}\n\n"
        f"**Dirección:** {direccion}\n\n"
        f"**Motivo:** {motivo}\n\n"
        "### Respondé con una sola de estas opciones\n\n"
        "`APROBAR COMERCIO`\n\n"
        "`APROBAR GENERADOR`\n\n"
        "`DESCARTAR`\n\n"
        "<!-- "
        f"pase360-key:{clave}"
        " -->"
    )

    payload = {
        "title": (
            "Decisión requerida: "
            + nombre
        ),
        "body": body,
    }

    try:
        response = requests.post(
            f"{API_BASE}/repos/{repo}/issues",
            headers=_headers(token),
            json=payload,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        return {
            "ok": True,
            "url": data.get(
                "html_url",
                "",
            ),
            "number": data.get(
                "number"
            ),
            "clave": clave,
        }

    except Exception as exc:
        return {
            "ok": False,
            "motivo": str(exc),
        }
