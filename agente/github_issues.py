import os
import requests

def crear_pregunta(c, motivo):
    token = os.getenv("GITHUB_TOKEN","")
    repo = os.getenv("GITHUB_REPOSITORY","")
    if not token or not repo:
        return {"ok":False,"motivo":"faltan GITHUB_TOKEN/GITHUB_REPOSITORY"}
    body = (
        "### El agente necesita una decisión humana\n\n"
        f"**Prospecto:** {c.get('name','')}\n\n"
        f"**Tipo propuesto:** {c.get('tipo','dudoso')}\n\n"
        f"**Email:** {c.get('email','')}\n\n"
        f"**Website:** {c.get('website','')}\n\n"
        f"**Motivo:** {motivo}\n\n"
        "Respondé con `APROBAR COMERCIO`, `APROBAR GENERADOR` o `DESCARTAR`."
    )
    r = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"},
        json={"title":f"Decisión requerida: {c.get('name','sin nombre')}","body":body},
        timeout=20
    )
    r.raise_for_status()
    return {"ok":True,"url":r.json().get("html_url")}
