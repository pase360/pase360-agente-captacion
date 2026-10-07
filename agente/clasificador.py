from .util import normalizar_texto


# ============================================================
# PASE 360 — CLASIFICADOR DE CANDIDATOS
# ============================================================
#
# Objetivo:
#   - comercio  -> empresa/local que puede ofrecer beneficios
#   - generador -> organización que puede distribuir beneficios
#   - dudoso    -> no hay evidencia suficiente
#   - descartado -> claramente no corresponde
#
# Reglas importantes:
#   - "colegio" significa colegio profesional, NO escuela.
#   - Las cámaras NO son generadores.
#   - Un gimnasio/estadio/centro deportivo por sí solo NO es generador.
#   - "gremio" solo no alcanza: debe existir contexto laboral/gremial.
# ============================================================


GENERADOR_FUERTE = (
    "sindicato",
    "sindicatos",
    "sindical",
    "gremio",
    "gremial",
    "mutual",
    "mutualidad",
    "federacion",
    "federaciones",
    "asociacion profesional",
    "asociacion de profesionales",
    "asociación profesional",
    "asociación de profesionales",
    "cooperativa",
    "cooperativas",
)


COLEGIOS_PROFESIONALES = (
    "colegio de abogados",
    "colegio de escribanos",
    "colegio de arquitectos",
    "colegio de ingenieros",
    "colegio de contadores",
    "colegio de medicos",
    "colegio de médicos",
    "colegio de odontologos",
    "colegio de odontólogos",
    "colegio de psicologos",
    "colegio de psicólogos",
    "colegio de veterinarios",
    "colegio de farmacéuticos",
    "colegio de farmaceuticos",
    "colegio profesional",
    "consejo profesional",
)


CONTEXTO_GREMIAL = (
    "trabajador",
    "trabajadores",
    "empleado",
    "empleados",
    "empleado publico",
    "empleados publicos",
    "docente",
    "docentes",
    "obreros",
    "laboral",
    "laborales",
    "personal",
    "afiliado",
    "afiliados",
    "afiliacion",
    "afiliación",
    "delegados",
    "delegacion",
    "delegación",
)


CONTEXTO_MIEMBROS = (
    "afiliado",
    "afiliados",
    "asociados",
    "asociadas",
    "socios",
    "socias",
    "miembros",
    "beneficiarios",
    "profesionales",
    "matriculados",
    "matriculadas",
)


CENTROS_SOCIALES_VALIDOS = (
    "centro de jubilados",
    "centro de jubilados y pensionados",
    "centro de pensionados",
    "centro de trabajadores",
    "centro de empleados",
    "centro de profesionales",
    "centro vecinal",
)


CLUBES = (
    "club ",
    "club deportivo",
    "club social",
    "club atletico",
    "club atlético",
    "club de barrio",
    "club de futbol",
    "club de fútbol",
    "club de rugby",
    "club de hockey",
)


PALABRAS_COMERCIO = (
    "tienda",
    "local",
    "comercio",
    "negocio",
    "restaurant",
    "restaurante",
    "bar",
    "cafe",
    "cafeteria",
    "cafetería",
    "panaderia",
    "panadería",
    "pasteleria",
    "pastelería",
    "heladeria",
    "heladería",
    "farmacia",
    "veterinaria",
    "veterinario",
    "dentista",
    "odontologia",
    "odontología",
    "clinica",
    "clínica",
    "consultorio",
    "hotel",
    "hostel",
    "peluqueria",
    "peluquería",
    "barberia",
    "barbería",
    "gimnasio",
    "indumentaria",
    "zapateria",
    "zapatería",
    "libreria",
    "librería",
    "ferreteria",
    "ferretería",
    "panificacion",
    "panificación",
    "inmobiliaria",
    "concesionaria",
    "automotor",
    "taller",
    "empresa",
    "srl",
    "s.a.",
    "sa",
    "servicios",
    "estudio",
    "consultora",
    "consultoria",
    "consultoría",
)


PALABRAS_DESCARTAR = (
    "escuela",
    "escuelas",
    "colegio secundario",
    "colegio primario",
    "jardin de infantes",
    "jardín de infantes",
    "universidad",
    "facultad",
    "instituto educativo",
    "instituto educacional",
)


def _texto(c):
    tags = c.get("tags") or {}

    partes = [
        c.get("name", ""),
        c.get("website", ""),
        c.get("website_final", ""),
        c.get("direccion", ""),
        c.get("phone", ""),
        " ".join(str(v) for v in tags.values()),
    ]

    return normalizar_texto(" ".join(str(x) for x in partes if x))


def _tags(c):
    return c.get("tags") or {}


def _es_camara(texto):
    return (
        "camara de comercio" in texto
        or "camara empresarial" in texto
        or "camara empresaria" in texto
        or "camara industrial" in texto
        or "camara de industriales" in texto
        or "camara de comerciantes" in texto
        or "camara de comercio e industria" in texto
        or "cámara de comercio" in texto
        or "cámara empresarial" in texto
        or "cámara empresaria" in texto
        or "cámara industrial" in texto
    )


def _es_educativo(texto):
    return any(palabra in texto for palabra in PALABRAS_DESCARTAR)


def _es_colegio_profesional(texto):
    return any(palabra in texto for palabra in COLEGIOS_PROFESIONALES)


def _es_generador_fuerte(texto):
    return any(palabra in texto for palabra in GENERADOR_FUERTE)


def _es_contexto_gremial(texto):
    return any(palabra in texto for palabra in CONTEXTO_GREMIAL)


def _es_contexto_miembros(texto):
    return any(palabra in texto for palabra in CONTEXTO_MIEMBROS)


def _es_centro_social_valido(texto):
    return any(palabra in texto for palabra in CENTROS_SOCIALES_VALIDOS)


def _es_club(texto):
    if any(palabra in texto for palabra in CLUBES):
        return True

    return (
        "club" in texto
        and any(
            palabra in texto
            for palabra in (
                "atletico",
                "atlético",
                "deportivo",
                "social",
                "rugby",
                "futbol",
                "fútbol",
                "hockey",
                "basquet",
                "básquet",
                "sport",
            )
        )
    )


def _tipo_por_tags(c):
    tags = _tags(c)

    amenity = normalizar_texto(tags.get("amenity", ""))
    shop = normalizar_texto(tags.get("shop", ""))
    craft = normalizar_texto(tags.get("craft", ""))
    office = normalizar_texto(tags.get("office", ""))
    leisure = normalizar_texto(tags.get("leisure", ""))
    healthcare = normalizar_texto(tags.get("healthcare", ""))

    if shop:
        return "comercio", "OSM: etiqueta shop"

    if craft:
        return "comercio", "OSM: etiqueta craft"

    if office in {
        "company",
        "commercial",
        "estate_agent",
        "insurance",
        "lawyer",
        "accountant",
    }:
        return "comercio", "OSM: oficina comercial/profesional"

    if amenity in {
        "restaurant",
        "cafe",
        "fast_food",
        "bar",
        "pub",
        "food_court",
        "pharmacy",
        "clinic",
        "doctors",
        "dentist",
        "veterinary",
    }:
        return "comercio", "OSM: servicio/comercio"

    if healthcare:
        return "comercio", "OSM: healthcare"

    if leisure in {
        "sports_centre",
        "sports_hall",
        "stadium",
        "pitch",
    }:
        return "dudoso", "OSM: instalación deportiva, no demuestra que sea generador"

    if amenity in {
        "community_centre",
        "social_centre",
        "association",
    }:
        return "dudoso", "OSM: organización social, falta evidencia de miembros/beneficiarios"

    return "", ""


def _es_asociacion_con_miembros(texto):
    asociacion = (
        "asociacion civil" in texto
        or "asociacion civil sin fines de lucro" in texto
        or "asociación civil" in texto
        or "asociación civil sin fines de lucro" in texto
    )

    if asociacion and _es_contexto_miembros(texto):
        return True

    return False


def clasificar(c):
    texto = _texto(c)

    if not texto:
        return "dudoso", "sin información suficiente"

    # --------------------------------------------------------
    # 1. Educación: nunca convertir una escuela/colegio
    #    educativo en generador.
    # --------------------------------------------------------
    if _es_educativo(texto):
        return "descartado", "institución educativa"

    # --------------------------------------------------------
    # 2. Cámaras: son fuente potencial de comercios,
    #    pero NO son generadores.
    # --------------------------------------------------------
    if _es_camara(texto):
        return "dudoso", "cámara: puede ser fuente de comercios, no generador"

    # --------------------------------------------------------
    # 3. Colegios profesionales.
    # --------------------------------------------------------
    if _es_colegio_profesional(texto):
        return "generador", "colegio profesional"

    # --------------------------------------------------------
    # 4. Generadores inequívocos.
    # --------------------------------------------------------
    if _es_generador_fuerte(texto):
        # "gremio" solo puede producir falsos positivos.
        if (
            "gremio" in texto
            or "gremial" in texto
        ):
            if not _es_contexto_gremial(texto):
                # Excepción: si además hay una organización
                # claramente sindical/mutual, se conserva.
                if not any(
                    palabra in texto
                    for palabra in (
                        "sindicato",
                        "mutual",
                        "federacion",
                        "federación",
                    )
                ):
                    return "dudoso", "gremio sin contexto laboral suficiente"

        return "generador", "organización de afiliados/mutual/gremial/profesional"

    # --------------------------------------------------------
    # 5. Asociaciones profesionales.
    # --------------------------------------------------------
    if (
        "asociacion profesional" in texto
        or "asociacion de profesionales" in texto
        or "asociación profesional" in texto
        or "asociación de profesionales" in texto
        or "consejo profesional" in texto
    ):
        return "generador", "organización de profesionales"

    # --------------------------------------------------------
    # 6. Asociaciones civiles con miembros/beneficiarios.
    # --------------------------------------------------------
    if _es_asociacion_con_miembros(texto):
        return "generador", "asociación con miembros/beneficiarios"

    # --------------------------------------------------------
    # 7. Centros sociales que claramente agrupan personas.
    # --------------------------------------------------------
    if _es_centro_social_valido(texto):
        return "generador", "centro social de miembros"

    # --------------------------------------------------------
    # 8. Clubes.
    # --------------------------------------------------------
    if _es_club(texto):
        return "generador", "club/institución deportiva o social"

    # --------------------------------------------------------
    # 9. Tags estructurados de comercio.
    # --------------------------------------------------------
    tipo_tags, motivo_tags = _tipo_por_tags(c)

    if tipo_tags:
        return tipo_tags, motivo_tags

    # --------------------------------------------------------
    # 10. Evidencia comercial por nombre/texto.
    # --------------------------------------------------------
    if any(palabra in texto for palabra in PALABRAS_COMERCIO):
        return "comercio", "nombre/texto con actividad comercial"

    # --------------------------------------------------------
    # 11. Si parece organización pero no podemos determinar
    #     si realmente puede actuar como generador.
    # --------------------------------------------------------
    if any(
        palabra in texto
        for palabra in (
            "asociacion",
            "asociación",
            "union",
            "unión",
            "fundacion",
            "fundación",
            "centro",
            "institucion",
            "institución",
        )
    ):
        return "dudoso", "organización sin evidencia suficiente de capacidad de generación"

    # --------------------------------------------------------
    # 12. Sin evidencia suficiente.
    # --------------------------------------------------------
    return "dudoso", "sin evidencia suficiente para clasificar"
