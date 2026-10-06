from datetime import datetime
from . import config as C
from . import fuentes, web, clasificador, ia, correos, github_issues
from .util import cargar, guardar, append_csv, actividad, normalizar_email, normalizar_texto
from .odoo import Odoo

def _key(c):
e = normalizar_email(c.get("email"))
if e:
return "email:" + e
w = str(c.get("website_final") or c.get("website") or "").lower().strip().rstrip("/")
if w:
return "web:" + w
return "name:" + normalizar_texto(c.get("name"))

def _historial():
return cargar(
"state.json",
{"contactados": {}, "descartados": {}, "preguntas": {}, "seguimientos": {}},
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

def capturar():
s = _historial()
rows = fuentes.buscar()
nuevos, seen = [], set()

```
for c in rows[:C.MAX_CANDIDATOS_SCAN]:
    k = _key(c)

    if not c.get("name") or k in seen or k in s["contactados"]:
        continue

    seen.add(k)

    c = web.completar(c)

    tipo, motivo = clasificador.clasificar(c)
    c["tipo"], c["clasificacion_motivo"] = tipo, motivo

    if tipo == "dudoso" and ia.disponible():
        ai = ia.revisar(c)

        if (
            ai.get("tipo") in {"comercio", "generador", "descartado"}
            and float(ai.get("confianza", 0)) >= 0.80
        ):
            c["tipo"] = ai["tipo"]
            c["clasificacion_motivo"] = (
                "IA: " + str(ai.get("motivo", ""))
            )

    c["email"] = normalizar_email(c.get("email"))

    if c["tipo"] == "descartado":
        s["descartados"][k] = c.get(
            "clasificacion_motivo", ""
        )
        continue

    if not c["email"]:
        c["estado"] = "sin_email"
    elif c["tipo"] == "dudoso":
        c["estado"] = "requiere_decision"
    else:
        c["estado"] = "listo_para_contactar"

    nuevos.append(c)

nuevos.sort(
    key=lambda x: (
        x.get("estado") != "listo_para_contactar",
        x.get("tipo") != "generador",
        x.get("name", "").lower(),
    )
)

listos = [
    x
    for x in nuevos
    if x["estado"] == "listo_para_contactar"
][: C.META_CONTACTOS]

report_rows = (
    listos
    + [x for x in nuevos if x not in listos][:300]
)

append_csv(
    "captacion.csv",
    report_rows,
    _campos_csv(report_rows),
)

guardar("candidatos.json", report_rows)

if not C.MODO_PRUEBA:
    odoo = Odoo()

    for c in listos:
        enviar_prospecto(odoo, c, s)
else:
    guardar(
        "simulacion_contactos.json",
        [
            {
                "name": c["name"],
                "tipo": c["tipo"],
                "email": c["email"],
            }
            for c in listos
        ],
    )

_guardar_hist(s)

actividad(
    "captacion",
    encontrados=len(rows),
    listos=len(listos),
    nuevos=len(nuevos),
)

return {
    "encontrados": len(rows),
    "nuevos": len(nuevos),
    "listos": len(listos),
    "sin_email": sum(
        x["estado"] == "sin_email" for x in nuevos
    ),
    "dudosos": sum(
        x["estado"] == "requiere_decision" for x in nuevos
    ),
    "modo_prueba": C.MODO_PRUEBA,
}
```

def enviar_prospecto(odoo, c, s):
lead_id = odoo.buscar_lead_email(c["email"])

```
if not lead_id:
    lead_id = odoo.crear_lead(c)

asunto, cuerpo = correos.invitacion(c)

result = odoo.enviar(
    c["email"],
    asunto,
    cuerpo,
    lead_id,
)

s["contactados"][_key(c)] = {
    "fecha": datetime.now().isoformat(),
    "tipo": c["tipo"],
    "lead_id": lead_id,
    "mail": result,
}
```

def preguntas():
if C.MODO_PRUEBA:
return {
"creadas": 0,
"modo_prueba": True,
}

```
s = _historial()
created = []

for c in cargar("candidatos.json", []):
    if c.get("estado") != "requiere_decision":
        continue

    k = _key(c)

    if k in s["preguntas"]:
        continue

    result = github_issues.crear_pregunta(
        c,
        c.get(
            "clasificacion_motivo",
            "clasificación dudosa",
        ),
    )

    if result.get("ok"):
        s["preguntas"][k] = result.get("url")
        created.append(result.get("url"))

_guardar_hist(s)

return {
    "creadas": len(created),
    "urls": created,
}
```

def seguimiento():
if C.MODO_PRUEBA:
return {
"enviados": 0,
"modo_prueba": True,
}

```
s = _historial()
odoo = Odoo()
enviados = 0

for c in cargar("candidatos.json", []):
    k = _key(c)
    info = s["contactados"].get(k)

    if not info or int(info.get("seguimiento", 0)) >= 2:
        continue

    try:
        dias = (
            datetime.now()
            - datetime.fromisoformat(info["fecha"])
        ).days
    except Exception:
        dias = 999

    n = int(info.get("seguimiento", 0))

    if (n == 0 and dias < 4) or (
        n == 1 and dias < 8
    ):
        continue

    lead_id = info.get("lead_id") or odoo.buscar_lead_email(
        c.get("email")
    )

    if not lead_id:
        continue

    asunto, cuerpo = correos.seguimiento(
        c,
        n + 1,
    )

    odoo.enviar(
        c["email"],
        asunto,
        cuerpo,
        lead_id,
    )

    info["seguimiento"] = (
        int(info.get("seguimiento", 0)) + 1
    )

    enviados += 1

_guardar_hist(s)

return {
    "enviados": enviados,
}
```

def reporte():
s = _historial()
candidates = cargar("candidatos.json", [])

```
result = {
    "modo_prueba": C.MODO_PRUEBA,
    "candidatos_guardados": len(candidates),
    "contactados_historicos": len(s["contactados"]),
    "preguntas_creadas": len(s["preguntas"]),
    "listos_ultimo_scan": sum(
        x.get("estado") == "listo_para_contactar"
        for x in candidates
    ),
    "sin_email_ultimo_scan": sum(
        x.get("estado") == "sin_email"
        for x in candidates
    ),
    "dudosos_ultimo_scan": sum(
        x.get("estado") == "requiere_decision"
        for x in candidates
    ),
}

guardar("reporte.json", result)

return result
```

def diagnostico():
out = {}

```
try:
    rows = fuentes.buscar()
    out["osm"] = {
        "ok": True,
        "lugares": len(rows),
    }
except Exception as e:
    out["osm"] = {
        "ok": False,
        "error": str(e),
    }

out["gemini"] = {
    "ok": ia.disponible(),
    "configurado": bool(C.GEMINI_API_KEY),
}

if all(
    [
        C.ODOO_URL,
        C.ODOO_DB,
        C.ODOO_USER,
        C.ODOO_API_KEY,
    ]
):
    try:
        out["odoo"] = {
            "ok": True,
            "usuario": Odoo().test(),
        }
    except Exception as e:
        out["odoo"] = {
            "ok": False,
            "error": str(e),
        }
else:
    out["odoo"] = {
        "ok": False,
        "error": "faltan secrets de Odoo",
    }

out["modo_prueba"] = C.MODO_PRUEBA

out["web"] = {
    "comercio": C.WEB_COMERCIO,
    "generador": C.WEB_GENERADOR,
}

guardar("diagnostico.json", out)

return out
```
