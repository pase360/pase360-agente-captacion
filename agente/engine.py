from datetime import datetime

from . import config as C
from . import fuentes, web, clasificador, ia, correos, github_issues
from .util import (
    cargar,
    guardar,
    append_csv,
    actividad,
    normalizar_email,
    normalizar_texto,
)
from .odoo import Odoo


def _key(c):
    email = normalizar_email(
        c.get("email")
    )

    if email:
        return "email:" + email

    website = str(
        c.get("website_final")
        or c.get("website")
        or ""
    ).strip().lower().rstrip("/")

    if website:
        return "web:" + website

    nombre = normalizar_texto(
        c.get("name")
    )

    telefono = normalizar_texto(
        c.get("phone")
    )

    direccion = normalizar_texto(
        c.get("direccion")
    )

    return (
        "identidad:"
        + "|".join(
            [
                nombre,
                telefono,
                direccion,
            ]
        )
    )


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
    guardar(
        "state.json",
        s,
    )


def _campos_csv(rows):
    campos = [
        "name",
        "tipo",
        "email",
        "email_source",
        "email_source_url",
        "email_confidence",
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

    for row in rows:
        for campo in row.keys():
            if campo not in campos:
                campos.append(campo)

    return campos


def _clasificar(c):
    tipo, motivo = (
        clasificador.clasificar(c)
    )

    c["tipo"] = tipo
    c["clasificacion_motivo"] = motivo

    if (
        tipo == "dudoso"
        and ia.disponible()
    ):
        try:
            resultado = ia.revisar(c)

            ai_tipo = resultado.get(
                "tipo"
            )

            confianza = float(
                resultado.get(
                    "confianza",
                    0,
                )
            )

            # La IA puede resolver casos dudosos de comercio o descarte,
            # pero NO puede convertir una organización dudosa en generador
            # sin evidencia determinística suficiente. Esto evita falsos
            # generadores como fundaciones, capillas, organismos públicos,
            # asociaciones genéricas o similares.
            if (
                ai_tipo
                in {
                    "comercio",
                    "descartado",
                }
                and confianza >= 0.85
            ):
                c["tipo"] = ai_tipo
                c["clasificacion_motivo"] = (
                    "IA: "
                    + str(
                        resultado.get(
                            "motivo",
                            "",
                        )
                    )
                )

        except Exception as exc:
            c["clasificacion_motivo"] = (
                str(
                    c.get(
                        "clasificacion_motivo",
                        "",
                    )
                )
                + " | IA no disponible: "
                + str(exc)
            )

    return c


def _enriquecer_email(c):
    if c.get("tipo") not in {
        "comercio",
        "generador",
    }:
        return c

    try:
        c = web.completar(c)

    except Exception as exc:
        c["email_enrichment_error"] = str(
            exc
        )

    c["email"] = normalizar_email(
        c.get("email")
    )

    return c


def _nuevo_diagnostico():
    return {
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
            "descartado": 0,
        },
        "sin_email_por_tipo": {
            "comercio": 0,
            "generador": 0,
            "otro": 0,
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


def capturar():
    s = _historial()

    rows = fuentes.buscar()

    diagnostico = _nuevo_diagnostico()

    candidatos = []
    seen = set()

    # Primero clasificamos todos.
    for original in rows[
        : C.MAX_CANDIDATOS_SCAN
    ]:
        c = dict(original)

        if not c.get("name"):
            diagnostico[
                "sin_nombre"
            ] += 1
            continue

        k = _key(c)

        if k in seen:
            diagnostico[
                "duplicados"
            ] += 1
            continue

        if k in s["contactados"]:
            diagnostico[
                "ya_contactados"
            ] += 1
            continue

        seen.add(k)

        c = _clasificar(c)

        tipo = c.get(
            "tipo",
            "otro",
        )

        if tipo not in diagnostico[
            "por_tipo"
        ]:
            tipo = "otro"
            c["tipo"] = tipo

        diagnostico[
            "por_tipo"
        ][tipo] += 1

        if tipo == "descartado":
            c["estado"] = "descartado"

            diagnostico[
                "por_estado"
            ]["descartado"] += 1

            motivo = c.get(
                "clasificacion_motivo",
                "",
            )

            diagnostico[
                "descartados_por_motivo"
            ][motivo] = (
                diagnostico[
                    "descartados_por_motivo"
                ].get(
                    motivo,
                    0,
                )
                + 1
            )

            s["descartados"][k] = motivo

            continue

        if tipo == "dudoso":
            c["estado"] = (
                "requiere_decision"
            )

            diagnostico[
                "por_estado"
            ]["requiere_decision"] += 1

            if len(
                diagnostico[
                    "dudosos_muestra"
                ]
            ) < 30:
                diagnostico[
                    "dudosos_muestra"
                ].append(
                    {
                        "name": c.get(
                            "name"
                        ),
                        "motivo": c.get(
                            "clasificacion_motivo"
                        ),
                    }
                )

            candidatos.append(c)
            continue

        candidatos.append(c)

    # ---------------------------------------------------------
    # AHORA buscamos emails.
    # ---------------------------------------------------------

    for c in candidatos:
        if c.get("tipo") not in {
            "comercio",
            "generador",
        }:
            continue

        c = _enriquecer_email(c)

        if c.get("email"):
            c["estado"] = (
                "listo_para_contactar"
            )

            diagnostico[
                "por_estado"
            ]["listo_para_contactar"] += 1

        else:
            c["estado"] = "sin_email"

            diagnostico[
                "por_estado"
            ]["sin_email"] += 1

            tipo = c.get(
                "tipo",
                "otro",
            )

            if tipo in {
                "comercio",
                "generador",
            }:
                diagnostico[
                    "sin_email_por_tipo"
                ][tipo] += 1

            if len(
                diagnostico[
                    "sin_email_muestra"
                ]
            ) < 30:
                diagnostico[
                    "sin_email_muestra"
                ].append(
                    {
                        "name": c.get(
                            "name"
                        ),
                        "tipo": tipo,
                        "website": (
                            c.get(
                                "website_final"
                            )
                            or c.get(
                                "website"
                            )
                        ),
                    }
                )

        tipo = c.get("tipo")

        if (
            tipo == "generador"
            and len(
                diagnostico[
                    "generadores_muestra"
                ]
            ) < 30
        ):
            diagnostico[
                "generadores_muestra"
            ].append(
                {
                    "name": c.get(
                        "name"
                    ),
                    "email": c.get(
                        "email"
                    ),
                    "motivo": c.get(
                        "clasificacion_motivo"
                    ),
                }
            )

        if (
            tipo == "comercio"
            and len(
                diagnostico[
                    "comercios_muestra"
                ]
            ) < 30
        ):
            diagnostico[
                "comercios_muestra"
            ].append(
                {
                    "name": c.get(
                        "name"
                    ),
                    "email": c.get(
                        "email"
                    ),
                    "motivo": c.get(
                        "clasificacion_motivo"
                    ),
                }
            )

    # ---------------------------------------------------------
    # ORDENAR: primero generadores y comercios listos.
    # ---------------------------------------------------------

    listos = [
        c
        for c in candidatos
        if c.get("estado")
        == "listo_para_contactar"
    ]

    listos.sort(
        key=lambda c: (
            c.get("tipo")
            != "generador",
            c.get(
                "email_confidence",
                0,
            ) * -1,
            normalizar_texto(
                c.get("name")
            ),
        )
    )

    seleccionados = listos[
        : C.META_CONTACTOS
    ]

    diagnostico[
        "listos_detectados"
    ] = len(listos)

    diagnostico[
        "listos_seleccionados"
    ] = len(seleccionados)

    diagnostico[
        "listos_comercio"
    ] = sum(
        c.get("tipo") == "comercio"
        for c in seleccionados
    )

    diagnostico[
        "listos_generador"
    ] = sum(
        c.get("tipo") == "generador"
        for c in seleccionados
    )

    diagnostico[
        "clasificados"
    ] = sum(
        diagnostico["por_tipo"].values()
    )

    estados = sum(
        diagnostico["por_estado"].values()
    )

    diagnostico["cuadre"] = {
        "clasificacion_total":
            diagnostico["clasificados"],
        "estado_total":
            estados,
        "cuadra":
            diagnostico["clasificados"]
            == estados,
    }

    # ---------------------------------------------------------
    # REPORTES
    # ---------------------------------------------------------

    todos_reportar = (
        seleccionados
        + [
            c
            for c in candidatos
            if c not in seleccionados
        ][:500]
    )

    append_csv(
        "captacion.csv",
        todos_reportar,
        _campos_csv(
            todos_reportar
        ),
    )

    guardar(
        "candidatos.json",
        todos_reportar,
    )

    # ---------------------------------------------------------
    # ENVÍO
    # ---------------------------------------------------------

    if not C.MODO_PRUEBA:
        odoo = Odoo()

        for c in seleccionados:
            enviar_prospecto(
                odoo,
                c,
                s,
            )

    else:
        guardar(
            "simulacion_contactos.json",
            [
                {
                    "name": c.get(
                        "name"
                    ),
                    "tipo": c.get(
                        "tipo"
                    ),
                    "email": c.get(
                        "email"
                    ),
                }
                for c in seleccionados
            ],
        )

    diagnostico[
        "encontrados"
    ] = len(rows)

    diagnostico[
        "procesados"
    ] = min(
        len(rows),
        C.MAX_CANDIDATOS_SCAN,
    )

    diagnostico[
        "nuevos"
    ] = len(candidatos)

    diagnostico[
        "descartados"
    ] = diagnostico[
        "por_tipo"
    ]["descartado"]

    diagnostico[
        "excluidos"
    ] = (
        diagnostico["duplicados"]
        + diagnostico["ya_contactados"]
        + diagnostico["sin_nombre"]
    )

    guardar(
        "diagnostico_captacion.json",
        diagnostico,
    )

    _guardar_hist(s)

    actividad(
        "captacion",
        encontrados=len(rows),
        listos=len(seleccionados),
        nuevos=len(candidatos),
    )

    return {
        "encontrados": len(rows),
        "procesados": diagnostico[
            "procesados"
        ],
        "clasificados": diagnostico[
            "clasificados"
        ],
        "nuevos": len(candidatos),
        "listos": len(seleccionados),
        "listos_detectados": len(listos),
        "listos_seleccionados": len(
            seleccionados
        ),
        "listos_comercio": diagnostico[
            "listos_comercio"
        ],
        "listos_generador": diagnostico[
            "listos_generador"
        ],
        "sin_email": diagnostico[
            "por_estado"
        ]["sin_email"],
        "sin_email_por_tipo":
            diagnostico[
                "sin_email_por_tipo"
            ],
        "dudosos": diagnostico[
            "por_estado"
        ]["requiere_decision"],
        "descartados": diagnostico[
            "por_tipo"
        ]["descartado"],
        "duplicados": diagnostico[
            "duplicados"
        ],
        "ya_contactados": diagnostico[
            "ya_contactados"
        ],
        "sin_nombre": diagnostico[
            "sin_nombre"
        ],
        "excluidos": diagnostico[
            "excluidos"
        ],
        "por_tipo": diagnostico[
            "por_tipo"
        ],
        "por_estado": diagnostico[
            "por_estado"
        ],
        "cuadre": diagnostico[
            "cuadre"
        ],
        "generadores_muestra":
            diagnostico[
                "generadores_muestra"
            ],
        "sin_email_muestra":
            diagnostico[
                "sin_email_muestra"
            ],
        "dudosos_muestra":
            diagnostico[
                "dudosos_muestra"
            ],
        "modo_prueba":
            C.MODO_PRUEBA,
    }


def enviar_prospecto(
    odoo,
    c,
    s,
):
    lead_id = odoo.buscar_lead_email(
        c["email"]
    )

    if not lead_id:
        lead_id = odoo.crear_lead(c)

    asunto, cuerpo = correos.invitacion(
        c
    )

    resultado = odoo.enviar(
        c["email"],
        asunto,
        cuerpo,
        lead_id,
    )

    s["contactados"][
        _key(c)
    ] = {
        "fecha": datetime.now().isoformat(),
        "tipo": c["tipo"],
        "lead_id": lead_id,
        "mail": resultado,
        "seguimiento": 0,
    }


def preguntas():
    s = _historial()
    creadas = []

    for c in cargar(
        "candidatos.json",
        [],
    ):
        if c.get(
            "estado"
        ) != "requiere_decision":
            continue

        k = _key(c)

        if k in s["preguntas"]:
            continue

        resultado = (
            github_issues.crear_pregunta(
                c,
                c.get(
                    "clasificacion_motivo",
                    "clasificación dudosa",
                ),
            )
        )

        if resultado.get("ok"):
            s["preguntas"][k] = (
                resultado.get(
                    "url"
                )
            )

            creadas.append(
                resultado.get(
                    "url"
                )
            )

    _guardar_hist(s)

    return {
        "creadas": len(creadas),
        "urls": creadas,
        "modo_prueba": C.MODO_PRUEBA,
    }


def seguimiento():
    if C.MODO_PRUEBA:
        return {
            "enviados": 0,
            "modo_prueba": True,
        }

    s = _historial()
    odoo = Odoo()

    enviados = 0

    for c in cargar(
        "candidatos.json",
        [],
    ):
        k = _key(c)

        info = s[
            "contactados"
        ].get(k)

        if not info:
            continue

        numero = int(
            info.get(
                "seguimiento",
                0,
            )
        )

        if numero >= 2:
            continue

        try:
            fecha = datetime.fromisoformat(
                info["fecha"]
            )

            dias = (
                datetime.now()
                - fecha
            ).days

        except Exception:
            dias = 999

        if (
            numero == 0
            and dias < 4
        ):
            continue

        if (
            numero == 1
            and dias < 8
        ):
            continue

        lead_id = (
            info.get("lead_id")
            or odoo.buscar_lead_email(
                c.get("email")
            )
        )

        if not lead_id:
            continue

        asunto, cuerpo = (
            correos.seguimiento(
                c,
                numero + 1,
            )
        )

        odoo.enviar(
            c["email"],
            asunto,
            cuerpo,
            lead_id,
        )

        info["seguimiento"] = (
            numero + 1
        )

        enviados += 1

    _guardar_hist(s)

    return {
        "enviados": enviados,
    }


def reporte():
    s = _historial()

    candidatos = cargar(
        "candidatos.json",
        [],
    )

    resultado = {
        "modo_prueba":
            C.MODO_PRUEBA,
        "candidatos_guardados":
            len(candidatos),
        "contactados_historicos":
            len(
                s["contactados"]
            ),
        "preguntas_creadas":
            len(
                s["preguntas"]
            ),
        "listos_ultimo_scan":
            sum(
                c.get("estado")
                == "listo_para_contactar"
                for c in candidatos
            ),
        "sin_email_ultimo_scan":
            sum(
                c.get("estado")
                == "sin_email"
                for c in candidatos
            ),
        "dudosos_ultimo_scan":
            sum(
                c.get("estado")
                == "requiere_decision"
                for c in candidatos
            ),
        "descartados_ultimo_scan":
            sum(
                c.get("estado")
                == "descartado"
                for c in candidatos
            ),
    }

    guardar(
        "reporte.json",
        resultado,
    )

    return resultado


def diagnostico():
    resultado = {}

    try:
        rows = fuentes.buscar()

        resultado["osm"] = {
            "ok": True,
            "lugares": len(rows),
        }

    except Exception as exc:
        resultado["osm"] = {
            "ok": False,
            "error": str(exc),
        }

    resultado["gemini"] = {
        "ok": ia.disponible(),
        "configurado": bool(
            C.GEMINI_API_KEY
        ),
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
            resultado["odoo"] = {
                "ok": True,
                "usuario": Odoo().test(),
            }

        except Exception as exc:
            resultado["odoo"] = {
                "ok": False,
                "error": str(exc),
            }

    else:
        resultado["odoo"] = {
            "ok": False,
            "configurado": False,
        }

    resultado["modo_prueba"] = (
        C.MODO_PRUEBA
    )

    resultado["meta_contactos"] = (
        C.META_CONTACTOS
    )

    resultado["url_comercio"] = (
        C.WEB_COMERCIO
    )

    resultado["url_generador"] = (
        C.WEB_GENERADOR
    )

    return resultado
