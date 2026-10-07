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
    e = normalizar_email(c.get("email"))
    if e:
        return "email:" + e

    w = str(
        c.get("website_final")
        or c.get("website")
        or ""
    ).lower().strip().rstrip("/")

    if w:
        return "web:" + w

    return "name:" + normalizar_texto(c.get("name"))


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

    campos = list(campos_base)

    for row in rows:
        for campo in row.keys():
            if campo not in campos:
                campos.append(campo)

    return campos


def _clasificar(c):
    """
    Clasifica primero al candidato.

    La búsqueda/enriquecimiento web NO se realiza aquí.
    Eso se hace solamente después de obtener una clasificación
    válida de comercio o generador.
    """

    tipo, motivo = clasificador.clasificar(c)

    c["tipo"] = tipo
    c["clasificacion_motivo"] = motivo

    # Si la clasificación es dudosa, intentar resolverla mediante IA.
    if tipo == "dudoso" and ia.disponible():
        try:
            ai = ia.revisar(c)

            ai_tipo = ai.get("tipo")
            ai_confianza = float(
                ai.get("confianza", 0)
            )

            if (
                ai_tipo
                in {
                    "comercio",
                    "generador",
                    "descartado",
                }
                and ai_confianza >= 0.80
            ):
                c["tipo"] = ai_tipo
                c["clasificacion_motivo"] = (
                    "IA: "
                    + str(
                        ai.get(
                            "motivo",
                            "",
                        )
                    )
                )

        except Exception as e:
            # Si la IA falla, conservamos la clasificación
            # original. Nunca convertimos un candidato por
            # error técnico en comercio o generador.
            c["clasificacion_motivo"] = (
                str(c.get("clasificacion_motivo", ""))
                + " | IA no disponible: "
                + str(e)
            )

    return c


def _enriquecer_email(c):
    """
    Busca/completa email únicamente para candidatos que ya
    fueron clasificados como comercio o generador.

    Esto evita gastar consultas web en descartados o dudosos.
    """

    if c.get("tipo") not in {
        "comercio",
        "generador",
    }:
        return c

    try:
        c = web.completar(c)
    except Exception as e:
        # Un error de enriquecimiento nunca debe romper
        # la captación completa.
        c["email_enrichment_error"] = str(e)

    c["email"] = normalizar_email(
        c.get("email")
    )

    return c


def capturar():
    s = _historial()
    rows = fuentes.buscar()

    nuevos = []
    seen = set()

    diagnostico = {
        # Clasificación exclusiva.
        # La suma de estos valores debe ser igual a
        # "clasificados".
        "por_tipo": {
            "comercio": 0,
            "generador": 0,
            "dudoso": 0,
            "descartado": 0,
            "otro": 0,
        },

        # Estado exclusivo.
        # La suma de estos valores debe ser igual a
        # "clasificados".
        "por_estado": {
            "listo_para_contactar": 0,
            "sin_email": 0,
            "requiere_decision": 0,
            "descartado": 0,
        },

        # Sin email por tipo.
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

    procesados = rows[: C.MAX_CANDIDATOS_SCAN]

    for c in procesados:
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

        # ---------------------------------------------------------
        # 1. CLASIFICAR PRIMERO
        # ---------------------------------------------------------
        #
        # IMPORTANTE:
        # Todavía NO buscamos email.
        #

        c = _clasificar(c)

        tipo_final = c.get("tipo", "otro")

        if tipo_final not in diagnostico["por_tipo"]:
            tipo_final = "otro"
            c["tipo"] = "otro"

        diagnostico["por_tipo"][tipo_final] += 1

        # ---------------------------------------------------------
        # 2. DESCARTADOS
        # ---------------------------------------------------------

        if tipo_final == "descartado":
            c["estado"] = "descartado"

            diagnostico["por_estado"]["descartado"] += 1

            motivo_desc = c.get(
                "clasificacion_motivo",
                "",
            )

            diagnostico["descartados_por_motivo"][
                motivo_desc
            ] = (
                diagnostico["descartados_por_motivo"].get(
                    motivo_desc,
                    0,
                )
                + 1
            )

            s["descartados"][k] = motivo_desc

            # No busca email.
            # No entra como candidato utilizable.
            continue

        # ---------------------------------------------------------
        # 3. DUDOSOS
        # ---------------------------------------------------------

        if tipo_final == "dudoso":
            c["estado"] = "requiere_decision"

            diagnostico["por_estado"][
                "requiere_decision"
            ] += 1

            if len(
                diagnostico["dudosos_muestra"]
            ) < 20:
                diagnostico["dudosos_muestra"].append(
                    {
                        "name": c.get("name"),
                        "email": c.get("email"),
                        "motivo": c.get(
                            "clasificacion_motivo"
                        ),
                    }
                )

            # MUY IMPORTANTE:
            # No hacemos búsqueda web de email para dudosos.
            nuevos.append(c)
            continue

        # ---------------------------------------------------------
        # 4. COMERCIO / GENERADOR
        # ---------------------------------------------------------
        #
        # Recién ahora se permite el enriquecimiento web.
        #

        c = _enriquecer_email(c)

        # ---------------------------------------------------------
        # 5. MUESTRAS
        # ---------------------------------------------------------

        if (
            tipo_final == "generador"
            and len(
                diagnostico["generadores_muestra"]
            ) < 30
        ):
            diagnostico["generadores_muestra"].append(
                {
                    "name": c.get("name"),
                    "email": c.get("email"),
                    "motivo": c.get(
                        "clasificacion_motivo"
                    ),
                }
            )

        if (
            tipo_final == "comercio"
            and len(
                diagnostico["comercios_muestra"]
            ) < 20
        ):
            diagnostico["comercios_muestra"].append(
                {
                    "name": c.get("name"),
                    "email": c.get("email"),
                    "motivo": c.get(
                        "clasificacion_motivo"
                    ),
                }
            )

        # ---------------------------------------------------------
        # 6. ESTADO
        # ---------------------------------------------------------

        if not c.get("email"):
            c["estado"] = "sin_email"

            diagnostico["por_estado"][
                "sin_email"
            ] += 1

            if tipo_final in {
                "comercio",
                "generador",
            }:
                diagnostico["sin_email_por_tipo"][
                    tipo_final
                ] += 1

            if len(
                diagnostico["sin_email_muestra"]
            ) < 20:
                diagnostico["sin_email_muestra"].append(
                    {
                        "name": c.get("name"),
                        "tipo": c.get("tipo"),
                        "website": (
                            c.get("website_final")
                            or c.get("website")
                        ),
                    }
                )

        else:
            c["estado"] = "listo_para_contactar"

            diagnostico["por_estado"][
                "listo_para_contactar"
            ] += 1

        nuevos.append(c)

    # -------------------------------------------------------------
    # CUADRE DE CLASIFICACIÓN
    # -------------------------------------------------------------

    clasificados = sum(
        diagnostico["por_tipo"].values()
    )

    estados_clasificados = sum(
        diagnostico["por_estado"].values()
    )

    diagnostico["clasificados"] = clasificados

    diagnostico["cuadre"] = {
        "clasificacion_total": clasificados,
        "estado_total": estados_clasificados,
        "cuadra": (
            clasificados
            == estados_clasificados
        ),
    }

    # -------------------------------------------------------------
    # ORDEN DE LOS CANDIDATOS
    # -------------------------------------------------------------

    nuevos.sort(
        key=lambda x: (
            x.get("estado")
            != "listo_para_contactar",
            x.get("tipo") != "generador",
            x.get("name", "").lower(),
        )
    )

    # Todos los listos detectados.
    todos_los_listos = [
        x
        for x in nuevos
        if x.get("estado")
        == "listo_para_contactar"
    ]

    diagnostico["listos_detectados"] = len(
        todos_los_listos
    )

    # Máximo de contactos que se seleccionan para
    # esta ejecución.
    listos = todos_los_listos[
        : C.META_CONTACTOS
    ]

    diagnostico["listos_seleccionados"] = len(
        listos
    )

    diagnostico["listos_comercio"] = sum(
        x.get("tipo") == "comercio"
        for x in listos
    )

    diagnostico["listos_generador"] = sum(
        x.get("tipo") == "generador"
        for x in listos
    )

    # -------------------------------------------------------------
    # REPORTES
    # -------------------------------------------------------------

    report_rows = (
        listos
        + [
            x
            for x in nuevos
            if x not in listos
        ][:300]
    )

    append_csv(
        "captacion.csv",
        report_rows,
        _campos_csv(report_rows),
    )

    guardar(
        "candidatos.json",
        report_rows,
    )

    # -------------------------------------------------------------
    # ENVÍO
    # -------------------------------------------------------------

    if not C.MODO_PRUEBA:
        odoo = Odoo()

        for c in listos:
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
                    "name": c["name"],
                    "tipo": c["tipo"],
                    "email": c["email"],
                }
                for c in listos
            ],
        )

    # -------------------------------------------------------------
    # CONTADORES GENERALES
    # -------------------------------------------------------------

    diagnostico["encontrados"] = len(rows)

    diagnostico["procesados"] = len(
        procesados
    )

    diagnostico["nuevos"] = len(nuevos)

    diagnostico["descartados"] = (
        diagnostico["por_tipo"]["descartado"]
    )

    diagnostico["excluidos"] = (
        diagnostico["duplicados"]
        + diagnostico["ya_contactados"]
        + diagnostico["sin_nombre"]
    )

    # -------------------------------------------------------------
    # GUARDADO
    # -------------------------------------------------------------

    guardar(
        "diagnostico_captacion.json",
        diagnostico,
    )

    _guardar_hist(s)

    actividad(
        "captacion",
        encontrados=len(rows),
        listos=len(listos),
        nuevos=len(nuevos),
    )

    # -------------------------------------------------------------
    # RESULTADO
    # -------------------------------------------------------------

    return {
        "encontrados": len(rows),
        "procesados": len(procesados),

        "clasificados": diagnostico[
            "clasificados"
        ],

        "nuevos": len(nuevos),

        "listos": len(listos),

        "listos_detectados": diagnostico[
            "listos_detectados"
        ],

        "listos_seleccionados": diagnostico[
            "listos_seleccionados"
        ],

        "listos_comercio": diagnostico[
            "listos_comercio"
        ],

        "listos_generador": diagnostico[
            "listos_generador"
        ],

        "sin_email": diagnostico[
            "por_estado"
        ]["sin_email"],

        "sin_email_por_tipo": diagnostico[
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

        "generadores_muestra": diagnostico[
            "generadores_muestra"
        ],

        "sin_email_muestra": diagnostico[
            "sin_email_muestra"
        ],

        "dudosos_muestra": diagnostico[
            "dudosos_muestra"
        ],

        "modo_prueba": C.MODO_PRUEBA,
    }


def enviar_prospecto(odoo, c, s):
    lead_id = odoo.buscar_lead_email(
        c["email"]
    )

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


def preguntas():
    if C.MODO_PRUEBA:
        return {
            "creadas": 0,
            "modo_prueba": True,
        }

    s = _historial()
    created = []

    for c in cargar(
        "candidatos.json",
        [],
    ):
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
            created.append(
                result.get("url")
            )

    _guardar_hist(s)

    return {
        "creadas": len(created),
        "urls": created,
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
        info = s["contactados"].get(k)

        if (
            not info
            or int(
                info.get(
                    "seguimiento",
                    0,
                )
            )
            >= 2
        ):
            continue

        try:
            dias = (
                datetime.now()
                - datetime.fromisoformat(
                    info["fecha"]
                )
            ).days
        except Exception:
            dias = 999

        n = int(
            info.get(
                "seguimiento",
                0,
            )
        )

        if (
            n == 0
            and dias < 4
        ) or (
            n == 1
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
            int(
                info.get(
                    "seguimiento",
                    0,
                )
            )
            + 1
        )

        enviados += 1

    _guardar_hist(s)

    return {
        "enviados": enviados,
    }


def reporte():
    s = _historial()

    candidates = cargar(
        "candidatos.json",
        [],
    )

    result = {
        "modo_prueba": C.MODO_PRUEBA,

        "candidatos_guardados": len(
            candidates
        ),

        "contactados_historicos": len(
            s["contactados"]
        ),

        "preguntas_creadas": len(
            s["preguntas"]
        ),

        "listos_ultimo_scan": sum(
            x.get("estado")
            == "listo_para_contactar"
            for x in candidates
        ),

        "sin_email_ultimo_scan": sum(
            x.get("estado")
            == "sin_email"
            for x in candidates
        ),

        "dudosos_ultimo_scan": sum(
            x.get("estado")
            == "requiere_decision"
            for x in candidates
        ),

        "descartados_ultimo_scan": sum(
            x.get("estado")
            == "descartado"
            for x in candidates
        ),
    }

    guardar(
        "reporte.json",
        result,
    )

    return result


def diagnostico():
    out = {}

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

    guardar(
        "diagnostico.json",
        out,
    )

    return out
