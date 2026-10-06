from datetime import datetime
from . import config as C
from . import fuentes, web, clasificador, ia, correos, github_issues
from .util import cargar, guardar, append_csv, actividad, normalizar_email, normalizar_texto
from .odoo import Odoo

def _key(c):
e = normalizar_email(c.get("email"))
if e:
return "email:" + e

```
w = str(c.get("website_final") or c.get("website") or "").lower().strip().rstrip("/")
if w:
    return "web:" + w

return "name:" + normalizar_texto(c.get("name"))
```

def _historial():
return cargar(
"state.json",
{
"contactados": {},
"descartados": {},
"preguntas": {},
"seguimientos": {},
},
)

def _guardar_hist(s):
guardar("state.json", s)

def _campos_csv(rows):
campos_base = [
"name",
"tipo",
"email",
"email_source",
"phone",
"direccion",
"website",
"website_final",
"estado",
"clasificacion_motivo",
"source",
"source_id",
"tags",
"lat",
"lon",
]

```
campos = list(campos_base)

for row in rows:
    for campo in row.keys():
        if campo not in campos:
            campos.append(campo)

return campos
```

def _muestra_nombres(rows, limite=20):
return [
{
"name": c.get("name", ""),
"tipo": c.get("tipo", ""),
"estado": c.get("estado", ""),
"email": c.get("email", ""),
"motivo": c.get("clasificacion_motivo", ""),
}
for c in rows[:limite]
]

def capturar():
s = _historial()
rows = fuentes.buscar()

```
nuevos = []
seen = set()

diagnostico = {
    "por_tipo": {
        "comercio": 0,
        "generador": 0,
        "dudoso": 0,
        "descartado": 0,
        "otro": 0,
    },
    "por_estado": {
        "listo_para_contactar": 0,
        "sin_email": 0,
        "requiere_decision": 0,
    },
    "descartados_por_motivo": {},
    "generadores_muestra": [],
    "comercios_muestra": [],
    "sin_email_muestra": [],
    "dudosos_muestra": [],
    "duplicados": 0,
    "ya_contactados": 0,
    "sin_nombre": 0,
}

for c in rows[:C.MAX_CANDIDATOS_SCAN]:
    k = _key(c)

    if not c.get("name"):
        diagnostico["sin_nombre"] += 1
        continue

    if k in seen:
        diagnostico["duplicados"] += 1
        continue

    if k in s["contactados"]:
        diagnostico["ya_contactados"] += 1
        continue

    seen.add(k)

    c = web.completar(c)

    tipo, motivo = clasificador.clasificar(c)
    c["tipo"] = tipo
    c["clasificacion_motivo"] = motivo

    if tipo == "dudoso" and ia.disponible():
        ai = ia.revisar(c)

        if (
            ai.get("tipo")
            in {"comercio", "generador", "descartado"}
            and float(ai.get("confianza", 0)) >= 0.80
        ):
            c["tipo"] = ai["tipo"]
            c["clasificacion_motivo"] = (
                "IA: " + str(ai.get("motivo", ""))
            )

    tipo_final = c.get("tipo", "otro")

    if tipo_final in diagnostico["por_tipo"]:
        diagnostico["por_tipo"][tipo_final] += 1
    else:
        diagnostico["por_tipo"]["otro"] += 1

    c["email"] = normalizar_email(c.get("email"))

    if c["tipo"] == "descartado":
        motivo_descartado = c.get(
            "clasificacion_motivo",
            "sin motivo",
        )

        diagnostico["descartados_por_motivo"][motivo_descartado] = (
            diagnostico["descartados_por_motivo"].get(
                motivo_descartado,
                0,
            )
            \+ 1
        )

        s["descartados"][k] = motivo_descartado
        continue

    if not c["email"]:
        c["estado"] = "sin_email"
        diagnostico["por_estado"]["sin_email"] += 1

        if len(diagnostico["sin_email_muestra"]) < 20:
            diagnostico["sin_email_muestra"].append(
                {
                    "name": c.get("name", ""),
                    "tipo": c.get("tipo", ""),
                    "website": c.get("website_final")
                    or c.get("website", ""),
                    "motivo": c.get(
                        "clasificacion_motivo",
                        "",
                    ),
                }
            )

    elif c["tipo"] == "dudoso":
        c["estado"] = "requiere_decision"
        diagnostico["por_estado"]["requiere_decision"] += 1

        if len(diagnostico["dudosos_muestra"]) < 20:
            diagnostico["dudosos_muestra"].append(
                {
                    "name": c.get("name", ""),
                    "email": c.get("email", ""),
                    "motivo": c.get(
                        "clasificacion_motivo",
                        "",
                    ),
                }
            )

    else:
        c["estado"] = "listo_para_contactar"
        diagnostico["por_estado"]["listo_para_contactar"] += 1

    if (
        c.get("tipo") == "generador"
        and len(diagnostico["generadores_muestra"]) < 30
    ):
        diagnostico["generadores_muestra"].append(
            {
                "name": c.get("name", ""),
                "email": c.get("email", ""),
                "estado": c.get("estado", ""),
                "motivo": c.get(
                    "clasificacion_motivo",
```
