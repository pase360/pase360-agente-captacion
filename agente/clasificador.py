from .util import normalizar_texto


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
    "federación",
    "federaciones",
    "cooperativa",
    "cooperativas",
    "asociacion profesional",
    "asociacion de profesionales",
    "asociación profesional",
    "asociación de profesionales",
    "fundacion",
    "fundación",
)

COLEGIOS_PROFESIONALES = (
    "colegio de abogados",
    "colegio de escribanos",
    "colegio de arquitectos",
    "colegio de ingenieros",
    "colegio de contadores",
    "colegio de médicos",
    "colegio de medicos",
    "colegio de odontólogos",
    "colegio de odontologos",
    "colegio de psicólogos",
    "colegio de psicologos",
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
    "delegado",
    "delegados",
    "delegacion",
    "delegación",
)

CONTEXTO_MIEMBROS = (
    "afiliado",
    "afiliados",
    "asociado",
    "asociados",
    "asociadas",
    "socios",
    "socias",
    "miembro",
    "miembros",
    "beneficiario",
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
    "asociacion vecinal",
    "asociación vecinal",
)

INSTITUCIONES_DEPORTIVAS = (
    "club",
    "club atletico",
    "club atlético",
    "club deportivo",
    "club social",
    "club de barrio",
    "club de futbol",
    "club de fútbol",
    "club de rugby",
    "club de hockey",
    "club de basquet",
    "club de básquet",
    "club social y deportivo",
    "institucion deportiva",
    "institución deportiva",
    "asociacion deportiva",
    "asociación deportiva",
    "federacion deportiva",
    "federación deportiva",
    "liga deportiva",
    "liga de futbol",
    "liga de fútbol",
    "liga de basquet",
    "liga de básquet",
    "entidad deportiva",
    "entidad social y deportiva",
    "sociedad deportiva",
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
    "escuela primaria",
    "escuela secundaria",
    "colegio secundario",
    "colegio primario",
    "jardin de infantes",
    "jardín de infantes",
    "universidad",
    "facultad",
    "instituto educativo",
    "instituto educacional",
    "institucion educativa",
    "institución educativa",
)

INSTALACIONES_DEPORTIVAS = (
    "polideportivo",
    "polideportiva",
    "estadio municipal",
    "playon deportivo",
    "playón deportivo",
    "sports centre",
    "sports center",
    "gimnasio municipal",
    "cancha municipal",
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

    return normalizar_texto(
        " ".join(
            str(x)
            for x in partes
            if x
        )
    )


def _tags(c):
    return c.get("tags") or {}


def _contiene(texto, palabras):
    return any(
        palabra in texto
        for palabra in palabras
    )


def _es_camara(texto):
    return any(
        palabra in texto
        for palabra in (
            "camara de comercio",
            "camara empresarial",
            "camara empresaria",
            "camara industrial",
            "camara de industriales",
            "camara de comerciantes",
            "camara de comercio e industria",
            "cámara de comercio",
            "cámara empresarial",
            "cámara empresaria",
            "cámara industrial",
            "cámara de industriales",
            "cámara de comerciantes",
        )
    )


def _es_educativo(texto):
    return _contiene(
        texto,
        PALABRAS_DESCARTAR,
    )


def _es_colegio_profesional(texto):
    return _contiene(
        texto,
        COLEGIOS_PROFESIONALES,
    )


def _es_club_o_institucion_deportiva(texto):
    return _contiene(
        texto,
        INSTITUCIONES_DEPORTIVAS,
    )


def _es_instalacion_deportiva(texto):
    return _contiene(
        texto,
        INSTALACIONES_DEPORTIVAS,
    )


def _es_contexto_gremial(texto):
    return _contiene(
        texto,
        CONTEXTO_GREMIAL,
    )


def _es_contexto_miembros(texto):
    return _contiene(
        texto,
        CONTEXTO_MIEMBROS,
    )


def _es_centro_social_valido(texto):
    return _contiene(
        texto,
        CENTROS_SOCIALES_VALIDOS,
    )


def _tipo_por_tags(c):
    tags = _tags(c)

    amenity = normalizar_texto(
        tags.get("amenity", "")
    )
    shop = normalizar_texto(
        tags.get("shop", "")
    )
    craft = normalizar_texto(
        tags.get("craft", "")
    )
    office = normalizar_texto(
        tags.get("office", "")
    )
    leisure = normalizar_texto(
        tags.get("leisure", "")
    )
    healthcare = normalizar_texto(
        tags.get("healthcare", "")
    )
    sport = normalizar_texto(
        tags.get("sport", "")
    )

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

    if amenity in {
        "association",
        "social_centre",
        "community_centre",
    }:
        return "", ""

    if leisure in {
        "sports_centre",
        "stadium",
        "sports_hall",
    }:
        if sport:
            return (
                "generador",
                "OSM: institución deportiva con actividad deportiva",
            )

        return "", ""

    if leisure == "pitch":
        return "", ""

    return "", ""


def _es_asociacion_con_miembros(texto):
    asociaciones = (
        "asociacion civil" in texto
        or "asociación civil" in texto
        or "asociacion civil sin fines de lucro" in texto
        or "asociación civil sin fines de lucro" in texto
    )

    return (
        asociaciones
        and _es_contexto_miembros(texto)
    )


def clasificar(c):
    texto = _texto(c)

    if not texto:
        return (
            "dudoso",
            "sin información suficiente",
        )

    # 1. Instituciones educativas.
    if _es_educativo(texto):
        return (
            "descartado",
            "institución educativa",
        )

    # 2. Cámaras: nunca son generadores.
    if _es_camara(texto):
        return (
            "dudoso",
            "cámara: puede ser fuente de comercios, no generador",
        )

    # 3. Colegios profesionales.
    if _es_colegio_profesional(texto):
        return (
            "generador",
            "colegio profesional",
        )

    # 4. Clubes e instituciones deportivas.
    #
    # REGLA DEFINITIVA DE PASE 360:
    # los clubes e instituciones deportivas
    # SON GENERADORES.
    if _es_club_o_institucion_deportiva(texto):
        return (
            "generador",
            "club/institución deportiva con comunidad de miembros",
        )

    # 5. Generadores fuertes.
    if _contiene(
        texto,
        GENERADOR_FUERTE,
    ):
        if (
            "gremio" in texto
            or "gremial" in texto
        ):
            if not _es_contexto_gremial(texto):
                if not _contiene(
                    texto,
                    (
                        "sindicato",
                        "mutual",
                        "federacion",
                        "federación",
                    ),
                ):
                    return (
                        "dudoso",
                        "gremio sin contexto laboral suficiente",
                    )

        return (
            "generador",
            "organización con afiliados, asociados o beneficiarios",
        )

    # 6. Centros sociales válidos.
    if _es_centro_social_valido(texto):
        return (
            "generador",
            "organización social con comunidad de miembros",
        )

    # 7. Asociaciones con miembros.
    if _es_asociacion_con_miembros(texto):
        return (
            "generador",
            "asociación con miembros/beneficiarios",
        )

    # 8. Tags OSM.
    tipo_tags, motivo_tags = _tipo_por_tags(c)

    if tipo_tags:
        return (
            tipo_tags,
            motivo_tags,
        )

    # 9. Instalación deportiva sin evidencia
    # de una organización detrás.
    if _es_instalacion_deportiva(texto):
        return (
            "dudoso",
            "instalación deportiva: falta evidencia de organización generadora",
        )

    # 10. Comercio.
    if _contiene(
        texto,
        PALABRAS_COMERCIO,
    ):
        return (
            "comercio",
            "actividad comercial identificable",
        )

    # 11. Otras organizaciones.
    if _contiene(
        texto,
        (
            "asociacion",
            "asociación",
            "union",
            "unión",
            "fundacion",
            "fundación",
            "institucion",
            "institución",
        ),
    ):
        return (
            "dudoso",
            "organización sin evidencia suficiente",
        )

    return (
        "dudoso",
        "sin evidencia suficiente para clasificar",
    )
