# agente/clasificador.py

import re


# ============================================================
# GENERADORES INSTITUCIONALES
# ============================================================

GENERADOR_FUERTE = [
    "sindicato",
    "sindicatos",
    "gremio",
    "gremios",
    "union de trabajadores",
    "unión de trabajadores",
    "mutual",
    "mutualidad",
    "cooperativa",
    "cooperativas",
]


COLEGIOS_PROFESIONALES = [
    "colegio de abogados",
    "colegio de arquitectos",
    "colegio de contadores",
    "colegio de escribanos",
    "colegio de ingenieros",
    "colegio de martilleros",
    "colegio de médicos",
    "colegio de medicos",
    "colegio de odontologos",
    "colegio de odontólogos",
    "colegio de psicologos",
    "colegio de psicólogos",
    "colegio de farmacéuticos",
    "colegio de farmaceuticos",
    "colegio de kinesiólogos",
    "colegio de kinesiologos",
    "colegio de nutricionistas",
    "colegio de veterinarios",
    "colegio profesional",
    "consejo profesional",
    "consejo de profesionales",
    "consejo de ciencias economicas",
    "consejo de ciencias económicas",
]


# ============================================================
# CLUBES E INSTITUCIONES DEPORTIVAS
# ============================================================

CLUBES_DEPORTIVOS_CLAROS = [
    "club atletico",
    "club atlético",
    "club deportivo",
    "club social y deportivo",
    "club social deportivo",
    "club de futbol",
    "club de fútbol",
    "club de rugby",
    "club de hockey",
    "club de basquet",
    "club de básquet",
    "club de basket",
    "club de tenis",
    "club de golf",
    "club de polo",
    "club de boxeo",
    "club de boxeadores",
    "club nautico",
    "club náutico",
    "club de remo",
    "club de natacion",
    "club de natación",
    "club de voleibol",
    "club de voley",
    "club de vóley",
    "club de handball",
    "club de ciclismo",
    "club de ajedrez",
    "club de barrio",
    "club barrial",
    "jockey club",
]


INSTITUCIONES_DEPORTIVAS = [
    "institucion deportiva",
    "institución deportiva",
    "instituciones deportivas",
    "asociacion deportiva",
    "asociación deportiva",
    "asociacion de futbol",
    "asociación de fútbol",
    "federacion deportiva",
    "federación deportiva",
    "federacion de futbol",
    "federación de fútbol",
    "liga deportiva",
    "liga de futbol",
    "liga de fútbol",
    "liga de basquet",
    "liga de básquet",
    "liga de rugby",
    "entidad deportiva",
    "entidad deportiva y social",
    "asociacion atletica",
    "asociación atlética",
    "asociacion de atletismo",
    "asociación de atletismo",
]


# ============================================================
# COMERCIO
# ============================================================

COMERCIO_CLARO = [
    "restaurante",
    "restó",
    "resto",
    "restaurant",
    "sushi",
    "sushiclub",
    "club de la milanesa",
    "bar",
    "cafeteria",
    "cafetería",
    "cafe",
    "café",
    "parrilla",
    "pizzeria",
    "pizzería",
    "panaderia",
    "panadería",
    "pasteleria",
    "pastelería",
    "heladeria",
    "heladería",
    "lomiteria",
    "lomitería",
    "hamburgueseria",
    "hamburguesería",
    "rotiseria",
    "rotisería",
    "cerveceria",
    "cervecería",
    "vinoteca",
    "kiosco",
    "supermercado",
    "almacen",
    "almacén",
    "autoservicio",
    "dietética",
    "farmacia",
    "farmacias",
    "veterinaria",
    "veterinario",
    "pet shop",
    "gimnasio",
    "gym",
    "peluqueria",
    "peluquería",
    "barberia",
    "barbería",
    "estetica",
    "estética",
    "spa",
    "hotel",
    "hosteria",
    "hostería",
    "inmobiliaria",
    "alquiler de autos",
    "rent a car",
    "rentauto",
    "consultorio",
    "consultorios",
    "sanatorio",
    "clinica",
    "clínica",
    "hospital",
    "centro medico",
    "centro médico",
    "centro de salud",
    "laboratorio",
    "odontologia",
    "odontología",
    "dentista",
    "psicologia",
    "psicología",
    "kinesiologia",
    "kinesiología",
    "nutricion",
    "nutrición",
]


PALABRAS_COMERCIO = [
    "tienda",
    "local",
    "comercio",
    "negocio",
    "empresa",
    "servicios",
    "servicio",
    "ventas",
    "venta",
    "mayorista",
    "minorista",
    "boutique",
    "shopping",
    "mercado",
    "distribuidora",
    "proveedor",
    "proveedores",
    "s.a.",
    "s.a",
    "srl",
    "s.r.l.",
    "sas",
    "s.a.s.",
]


# ============================================================
# ENTIDADES FUERA DEL PÚBLICO OBJETIVO
# ============================================================

ENTIDADES_EXCLUIDAS = [
    "capilla",
    "parroquia",
    "iglesia",
    "templo",
    "consulado",
    "embajada",
    "ministerio",
    "municipalidad",
    "secretaria de gobierno",
    "secretaría de gobierno",
    "organismo publico",
    "organismo público",
    "museo",
    "biblioteca publica",
    "biblioteca pública",
    "centro de investigacion",
    "centro de investigación",
]


# ============================================================
# NO GENERADORES
# ============================================================

EDUCACION = [
    "escuela",
    "colegio secundario",
    "colegio primario",
    "colegio privado",
    "colegio publico",
    "colegio público",
    "instituto educativo",
    "instituto educacional",
    "instituto privado",
    "instituto secundario",
    "instituto primario",
    "colegio nacional",
    "escuela tecnica",
    "escuela técnica",
    "ipet",
    "jardin de infantes",
    "jardín de infantes",
    "jardin maternal",
    "jardín maternal",
    "universidad",
    "facultad",
    "instituto superior",
    "academia",
    "instituto de enseñanza",
    "instituto de ensenanza",
    "centro educativo",
    "centro de educación",
    "centro de educacion",
    "primaria",
    "secundaria",
    "terciario",
]


CAMARAS = [
    "camara de comercio",
    "cámara de comercio",
    "camara empresarial",
    "cámara empresarial",
    "camara empresaria",
    "cámara empresaria",
    "camara industrial",
    "cámara industrial",
    "camara de empresarios",
    "cámara de empresarios",
    "camara",
    "cámara",
]


INSTALACIONES_DEPORTIVAS = [
    "polideportivo",
    "polideportiva",
    "estadio",
    "estadio municipal",
    "playon deportivo",
    "playón deportivo",
    "complejo deportivo",
    "complejo de deportes",
    "centro deportivo",
    "centro de deportes",
    "sports center",
    "sports centre",
    "gimnasio municipal",
    "cancha municipal",
    "predio deportivo",
    "predio de deportes",
]


CENTROS_SOCIALES_VALIDOS = [
    "centro vecinal",
    "asociacion vecinal",
    "asociación vecinal",
    "sociedad de fomento",
    "union vecinal",
    "unión vecinal",
    "centro de jubilados",
    "centro de jubilados y pensionados",
]


CONTEXTO_MIEMBROS = [
    "afiliados",
    "afiliado",
    "socios",
    "socio",
    "asociados",
    "asociado",
    "matriculados",
    "matriculado",
    "miembros",
    "miembro",
    "beneficiarios",
    "beneficiario",
]


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
        "categoria",
        "category",
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
            "amenity",
            "shop",
            "craft",
            "office",
            "leisure",
            "sport",
            "club",
            "type",
        ):
            valor = tags.get(clave)

            if valor:
                partes.append(str(valor))

    return " ".join(partes).strip()


def _normalizar(texto):
    texto = str(texto or "").lower().strip()

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

    return re.sub(r"\s+", " ", texto)


def _contiene(texto, lista):
    for termino in lista:
        termino = _normalizar(termino)

        if re.search(
            rf"(?<![a-z0-9]){re.escape(termino)}(?![a-z0-9])",
            texto,
        ):
            return True

    return False


def _tags(c):
    tags = c.get("tags")

    if isinstance(tags, dict):
        return {
            str(k).lower(): str(v).lower()
            for k, v in tags.items()
            if v is not None
        }

    return {}


# ============================================================
# DETECTORES
# ============================================================

def _es_educacion(c):
    """
    Descarta instituciones educativas, sin confundirlas con colegios
    y consejos profesionales que sí pueden ser generadores.
    """
    tags = _tags(c)

    # La etiqueta estructurada permite descartar escuelas aunque el
    # nombre no contenga palabras como "escuela" o "instituto".
    if tags.get("amenity") in {
        "school",
        "university",
        "college",
        "kindergarten",
        "preschool",
    }:
        return True

    if tags.get("office") in {
        "educational_institution",
        "school",
        "university",
    }:
        return True

    # Los colegios/consejos profesionales no son instituciones educativas
    # a estos efectos: son organizaciones con matriculados.
    if _es_colegio_profesional(c):
        return False

    return _contiene(
        _normalizar(_texto(c)),
        EDUCACION,
    )


def _es_camara(c):
    return _contiene(
        _normalizar(_texto(c)),
        CAMARAS,
    )


def _es_colegio_profesional(c):
    return _contiene(
        _normalizar(_texto(c)),
        COLEGIOS_PROFESIONALES,
    )


def _es_comercio_por_tags(c):
    tags = _tags(c)

    if tags.get("shop"):
        return True

    if tags.get("craft"):
        return True

    amenity = tags.get("amenity", "")

    if amenity in {
        "restaurant",
        "cafe",
        "bar",
        "fast_food",
        "pub",
        "food_court",
        "pharmacy",
        "clinic",
        "doctors",
        "dentist",
        "veterinary",
        "hospital",
        "marketplace",
        "fuel",
        "car_rental",
        "hotel",
        "guest_house",
        "beauty",
    }:
        return True

    office = tags.get("office", "")

    if office in {
        "company",
        "estate_agent",
        "insurance",
        "financial",
        "lawyer",
        "accountant",
        "consulting",
        "travel_agent",
        "employment_agency",
        "advertising_agency",
    }:
        return True

    return False


def _es_servicio_de_organizacion(c):
    """
    Evita que un servicio de una organización sea tomado
    como el generador.

    Ejemplos:
      Farmacia Sindical -> comercio
      Sanatorio Sindical -> comercio
      Centro de Salud ... Cooperativa -> comercio
    """

    texto = _normalizar(_texto(c))

    servicios = [
        "farmacia",
        "sanatorio",
        "clinica",
        "hospital",
        "consultorio",
        "centro medico",
        "centro de salud",
        "laboratorio",
        "odontologia",
        "odontologo",
        "psicologia",
        "kinesiologia",
        "nutricion",
        "veterinaria",
    ]

    return _contiene(texto, servicios)


def _es_comercio_por_nombre(c):
    texto = _normalizar(_texto(c))

    if _contiene(texto, COMERCIO_CLARO):
        return True

    if _contiene(texto, PALABRAS_COMERCIO):
        return True

    return False


def _es_generador_institucional(c):
    return _contiene(
        _normalizar(_texto(c)),
        GENERADOR_FUERTE,
    )


def _es_centro_social(c):
    texto = _normalizar(_texto(c))

    return _contiene(
        texto,
        CENTROS_SOCIALES_VALIDOS,
    )


def _es_asociacion_con_miembros(c):
    texto = _normalizar(_texto(c))

    if not _contiene(
        texto,
        [
            "asociacion",
            "asociación",
            "union",
            "unión",
            "sociedad",
            "federacion",
            "federación",
        ],
    ):
        return False

    return _contiene(
        texto,
        CONTEXTO_MIEMBROS,
    )


def _es_club_deportivo(c):
    texto = _normalizar(_texto(c))
    tags = _tags(c)

    # Tag explícito de club.
    if tags.get("club") in {
        "sport",
        "sports",
        "society",
        "association",
        "club",
    }:
        return True

    # Instituciones inequívocas.
    if _contiene(
        texto,
        CLUBES_DEPORTIVOS_CLAROS,
    ):
        return True

    if _contiene(
        texto,
        INSTITUCIONES_DEPORTIVAS,
    ):
        return True

    # "club" solo NO alcanza.
    if _contiene(texto, ["club"]):
        sport = tags.get("sport", "")
        leisure = tags.get("leisure", "")

        if sport and leisure in {
            "sports_centre",
            "sports_hall",
            "stadium",
            "pitch",
        }:
            return True

    return False


def _es_instalacion_deportiva(c):
    texto = _normalizar(_texto(c))
    tags = _tags(c)

    if _contiene(
        texto,
        INSTALACIONES_DEPORTIVAS,
    ):
        return True

    return tags.get("leisure") in {
        "sports_centre",
        "sports_hall",
        "stadium",
        "pitch",
    }


def _tipo_por_tags(c):
    tags = _tags(c)

    # Solo tags que por sí mismos representan una actividad
    # comercial/servicio. No convertimos asociaciones genéricas
    # en generadores automáticamente.
    if _es_comercio_por_tags(c):
        return (
            "comercio",
            "OSM identifica actividad comercial o de servicios",
        )

    return (
        "",
        "",
    )


# ============================================================
# FUNCIÓN PRINCIPAL
#
# IMPORTANTE:
# engine.py espera EXACTAMENTE:
#
#     tipo, motivo = clasificador.clasificar(c)
#
# Por eso esta función SIEMPRE devuelve dos valores.
# ============================================================

def clasificar(c):

    texto = _normalizar(_texto(c))

    if not texto:
        return (
            "dudoso",
            "Sin nombre o identidad suficiente",
        )

    # --------------------------------------------------------
    # 1. ENTIDADES QUE NO DEBEN RECIBIR INVITACIÓN
    # --------------------------------------------------------

    if _contiene(texto, ENTIDADES_EXCLUIDAS):
        return (
            "descartado",
            "Entidad fuera del público objetivo de Pase 360",
        )

    # --------------------------------------------------------
    # 2. EDUCACIÓN
    # --------------------------------------------------------

    if _es_educacion(c):
        return (
            "descartado",
            "Institución educativa",
        )

    # --------------------------------------------------------
    # 2. CÁMARAS
    # --------------------------------------------------------

    if _es_camara(c):
        return (
            "dudoso",
            "Cámara empresaria/comercial: sirve como fuente, no como generador",
        )

    # --------------------------------------------------------
    # 3. SERVICIOS DE ORGANIZACIONES
    #
    # Primero para evitar:
    # Farmacia Sindical -> generador
    # Sanatorio Sindical -> generador
    # --------------------------------------------------------

    if _es_servicio_de_organizacion(c):
        return (
            "comercio",
            "Servicio sanitario/comercial aunque pertenezca a una organización",
        )

    # --------------------------------------------------------
    # 4. COLEGIOS PROFESIONALES
    # --------------------------------------------------------

    if _es_colegio_profesional(c):
        return (
            "generador",
            "Colegio o consejo profesional",
        )

    # --------------------------------------------------------
    # 5. TAGS COMERCIALES
    #
    # Esto ocurre antes del club genérico.
    #
    # Club de la Milanesa -> comercio
    # Club Milanesa -> comercio
    # --------------------------------------------------------

    tipo, motivo = _tipo_por_tags(c)

    if tipo == "comercio":
        return tipo, motivo

    # --------------------------------------------------------
    # 6. COMERCIO POR NOMBRE
    # --------------------------------------------------------

    if _es_comercio_por_nombre(c):
        return (
            "comercio",
            "Actividad comercial/servicio identificada por nombre",
        )

    # --------------------------------------------------------
    # 7. GENERADORES INSTITUCIONALES
    # --------------------------------------------------------

    if _es_generador_institucional(c):
        return (
            "generador",
            "Organización con capacidad de agrupar beneficiarios",
        )

    # --------------------------------------------------------
    # 8. CENTROS SOCIALES
    # --------------------------------------------------------

    if _es_centro_social(c):
        return (
            "dudoso",
            "Organización social: no alcanza evidencia para asumir que genera beneficios",
        )

    # --------------------------------------------------------
    # 9. ASOCIACIONES CON MIEMBROS
    # --------------------------------------------------------

    if _es_asociacion_con_miembros(c):
        return (
            "dudoso",
            "Asociación con miembros: requiere validación humana antes de contactar",
        )

    # --------------------------------------------------------
    # 10. CLUBES E INSTITUCIONES DEPORTIVAS
    # --------------------------------------------------------

    if _es_club_deportivo(c):
        return (
            "generador",
            "Club o institución deportiva identificada",
        )

    # --------------------------------------------------------
    # 11. GENERADOR DETECTADO POR TAG
    # --------------------------------------------------------

    if tipo == "generador":
        return tipo, motivo

    # --------------------------------------------------------
    # 12. INSTALACIÓN DEPORTIVA SIN EVIDENCIA DE ORGANIZACIÓN
    #
    # NO se convierte automáticamente en generador.
    # --------------------------------------------------------

    if _es_instalacion_deportiva(c):
        return (
            "dudoso",
            "Instalación deportiva sin evidencia suficiente de organización de miembros",
        )

    # --------------------------------------------------------
    # 13. ORGANIZACIÓN GENÉRICA
    # --------------------------------------------------------

    if _contiene(
        texto,
        [
            "asociacion",
            "asociación",
            "federacion",
            "federación",
            "sociedad",
            "union",
            "unión",
        ],
    ):
        return (
            "dudoso",
            "Organización identificada pero sin evidencia suficiente para clasificarla",
        )

    # --------------------------------------------------------
    # 14. NOMBRE DEMASIADO GENÉRICO
    # --------------------------------------------------------

    if len(texto.split()) <= 1:
        return (
            "dudoso",
            "Nombre demasiado genérico",
        )

    # --------------------------------------------------------
    # 15. SIN EVIDENCIA SUFICIENTE
    # --------------------------------------------------------

    return (
        "dudoso",
        "No hay evidencia suficiente para clasificar con seguridad",
    )


def clasificar_candidato(c):
    """
    Compatibilidad con posibles llamadas externas.
    """
    return clasificar(c)
