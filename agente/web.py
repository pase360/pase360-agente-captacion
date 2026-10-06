import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from . import config as C
from .util import normalizar_email

EMAIL_RE = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
HINTS = ("contacto", "contact", "contactanos", "contactenos", "nosotros", "institucional", "empresa")

def _emails(text):
    return [normalizar_email(x) for x in EMAIL_RE.findall(text or "") if normalizar_email(x)]

def _fetch(url):
    return requests.get(url, headers={"User-Agent": C.USER_AGENT}, timeout=C.WEB_TIMEOUT, allow_redirects=True)

def completar(c):
    if normalizar_email(c.get("email")):
        c["email_source"] = "OpenStreetMap"
        return c
    url = str(c.get("website") or "").strip()
    if not re.match(r"^https?://", url, re.I):
        return c
    try:
        r = _fetch(url)
        if r.status_code >= 400 or "text/html" not in r.headers.get("content-type", ""):
            return c
        soup = BeautifulSoup(r.text, "html.parser")
        emails = _emails(r.text)
        for a in soup.find_all("a", href=True):
            label = (a.get_text(" ", strip=True) + " " + a["href"]).lower()
            if any(h in label for h in HINTS):
                try:
                    rr = _fetch(urljoin(r.url, a["href"]))
                    emails += _emails(rr.text)
                except Exception:
                    pass
                if emails:
                    break
        if emails:
            c["email"] = emails[0]
            c["email_source"] = "sitio_web"
        c["website_final"] = r.url
    except Exception as exc:
        c["web_error"] = str(exc)[:180]
    return c
