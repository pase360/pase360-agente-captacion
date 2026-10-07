# agente/clasificador.py

import re


# ============================================================
# REGLAS DE CLASIFICACIÓN — PASE 360
#
# Generadores:
#   sindicatos, gremios, mutuales, asociaciones, federaciones,
#   cooperativas, fundaciones, colegios/consejos profesionales,
#   clubes e instituciones deportivas reales.
#
# No son generadores:
#   cámaras empresarias, escuelas, comercios, restaurantes,
#   farmacias, sanatorios, consultorios, gimnasios comerciales,
#   instalaciones deportivas comerciales, etc.
#
# IMPORTANTE:
# La palabra "club" por sí sola NO alcanza.
# Primero se descartan los casos comerciales evidentes.
# ============================================================


# ------------------------------------------------------------
# GENERADORES INSTITUCIONALES
# ------------------------------------------------------------

GENERADOR_FUERTE = [
    "sindicato",
    "sindicatos",
    "gremio",
    "gremial",
    "gremios",
    "union de trabajadores",
    "unión de trabajadores",
    "mutual",
    "mutualidad",
    "federacion",
    "federación",
    "federacion de",
    "federación de",
    "asociacion civil",
    "asociación civil",
    "asociacion de",
    "asociación de",
    "asociacion profesional",
    "asociación profesional",
    "asociacion de profesionales",
    "asociación de profesionales",
    "cooperativa",
    "cooperativas",
    "fundacion",
    "fundación",
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
    "colegio de veterinarias",
    "colegio profesional",
    "colegio profesional de",
    "consejo profesional",
    "consejo de profesionales",
    "consejo de ciencias economicas",
    "consejo de ciencias económicas",
    "consejo profesional de ciencias economicas",
    "consejo profesional de ciencias económicas",
]


# ------------------------------------------------------------
# DEPORTIVOS
#
# No usamos "club" genérico como único criterio.
# Un comercio como "Club de la Milanesa" no debe entrar.
# ------------------------------------------------------------

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
    "club de tiro",
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


# ------------------------------------------------------------
# COMERCIO / SERVICIOS
# ------------------------------------------------------------

COMERCIO_CLARO = [
    "restaurante",
    "restó",
    "resto",
    "restaurant",
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
    "comida",
    "comidas",
    "delivery",
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
    "clinicas",
    "clínicas",
    "hospital",
    "hospital privado",
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


# ------------------------------------------------------------
# EDUCACIÓN — NO GENERADORES
# ------------------------------------------------------------

EDUCACION = [
    "escuela",
    "colegio secundario",
    "colegio primario",
    "colegio privado",
    "colegio publico",
    "colegio público",
    "instituto educativo",
    "instituto educacional",
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


# ------------------------------------------------------------
# CÁMARAS
#
# Las cámaras NO son generadores.
# Pueden servir como fuente para encontrar comercios.
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# INSTALACIONES DEPORTIVAS
#
# Una instalación deportiva no es automáticamente un generador.
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# CENTROS SOCIALES / ORGANIZACIONES
# ------------------------------------------------------------

CENTROS_SOCIALES_VALIDOS = [
    "centro vecinal",
    "centro vecinal y",
    "centro de jubilados",
    "centro de jubilados y pensionados",
    "asociacion vecinal",
    "asociación vecinal",
    "sociedad de fomento",
    "union vecinal",
    "unión vecinal",
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


# ------------------------------------------------------------
# UTILIDADES
# ------------------------------------------------------------

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

    texto = re.sub(r"\s+", " ", texto)

    return texto


def _contiene(texto, lista):
    """
    Busca expresiones completas para evitar falsos positivos.
    """
    for termino in lista:
        termino_n = _normalizar(termino)

        if not termino_n:
            continue

        if re.search(
            rf"(?<![a-z0-9]){re.escape(termino_n)}(?![a-z0-9])",
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


def _es_comercio_por_tags(c):
    tags = _tags(c)

    # Comercios explícitos de OSM.
    if tags.get("shop"):
        return True

    if tags.get("craft"):
        return True

    # Servicios comerciales / profesionales.
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

    # Oficinas comerciales.
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

    # Algunos objetos vienen identificados directamente como commercial.
    if tags.get("commercial") in {"yes", "true", "1"}:
        return True

    return False


def _es_servicio_sanitario(c):
    texto = _normalizar(_texto(c))

    patrones = [
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

    return _contiene(texto, patrones)


def _es_educacion(c):
    texto = _normalizar(_texto(c))

    return _contiene(texto, EDUCACION)


def _es_camara(c):
    texto = _normalizar(_texto(c))

    return _contiene(texto, CAMARAS)


def _es_colegio_profesional(c):
    texto = _normalizar(_texto(c))

    return _contiene(texto, COLEGIOS_PROFESIONALES)


def _es_club_deportivo(c):
    texto = _normalizar(_texto(c))
    tags = _tags(c)

    # Un tag OSM "club" es evidencia fuerte.
    if tags.get("club"):
        valor = tags.get("club", "")

        # Si OSM identifica explícitamente un club deportivo,
        # lo tratamos como generador.
        if valor in {
            "sport",
            "sports",
            "society",
            "association",
            "club",
        }:
            return True

    # Nombres inequívocamente deportivos.
    if _contiene(texto, CLUBES_DEPORTIVOS_CLAROS):
        return True

    if _contiene(texto, INSTITUCIONES_DEPORTIVAS):
        return True

    # "club" solo NO alcanza.
    # Pero "club" + contexto deportivo explícito sí.
    tiene_club = _contiene(texto, ["club"])

    if tiene_club:
        sport = tags.get("sport", "")
        leisure = tags.get("leisure", "")

        if sport and leisure in {
            "sports_centre",
            "sports_hall",
            "stadium",
            "pitch",
        }:
            return True

        if sport and any(
            palabra in texto
            for palabra in (
                "atletico",
                "atlético",
                "deportivo",
                "deportiva",
                "futbol",
                "fútbol",
                "rugby",
                "hockey",
                "basquet",
                "básquet",
                "tenis",
                "golf",
                "polo",
                "boxeo",
                "natacion",
                "natación",
                "voley",
                "vóley",
                "handball",
                "ciclismo",
                "ajedrez",
            )
        ):
            return True

    return False


def _es_instalacion_deportiva(c):
    texto = _normalizar(_texto(c))
    tags = _tags(c)

    if _contiene(texto, INSTALACIONES_DEPORTIVAS):
        return True

    leisure = tags.get("leisure", "")

    return leisure in {
        "sports_centre",
        "sports_hall",
        "stadium",
        "pitch",
    }


def _es_generador_institucional(c):
    texto = _normalizar(_texto(c))

    if _contiene(texto, GENERADOR_FUERTE):
        return True

    return False


def _es_centro_social(c):
    texto = _normalizar(_texto(c))

    if _contiene(texto, CENTROS_SOCIALES_VALIDOS):
        return True

    # Un centro de jubilados es generador.
    if _contiene(
        texto,
        [
            "centro de jubilados",
            "centro de jubilados y pensionados",
        ],
    ):
        return True

    return False


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

    return _contiene(texto, CONTEXTO_MIEMBROS)


def _es_comercio_por_nombre(c):
    texto = _normalizar(_texto(c))

    if _contiene(texto, COMERCIO_CLARO):
        return True

    if _contiene(texto, PALABRAS_COMERCIO):
        return True

    return False


def _tipo_por_tags(c):
    """
    Devuelve:
      comercio
      generador
      ""
    """
    tags = _tags(c)

    # Los tags comerciales tienen prioridad para evitar falsos
    # generadores como "Club de la Milanesa".
    if _es_comercio_por_tags(c):
        return "comercio"

    # Organizaciones profesionales.
    if tags.get("office") in {
        "association",
        "ngo",
    }:
        return "generador"

    # Asociaciones / centros comunitarios.
    if tags.get("amenity") in {
        "social_centre",
        "community_centre",
        "association",
    }:
        return "generador"

    # Un tag explícito club tiene valor.
    if tags.get("club"):
        return "generador"

    return ""


def _clasificar_por_tipo_organizacion(c):
    """
    Clasificación específica de servicios que pertenecen a una
    organización pero NO son necesariamente el generador.

    Ejemplo:
      Farmacia Sindical -> comercio
      Sanatorio Sindical -> comercio
      Centro de Salud ... Cooperativa -> comercio

    El generador debe ser la organización, no su farmacia/sanatorio.
    """
    if _es_servicio_sanitario(c):
        return "comercio"

    return ""


# ============================================================
# CLASIFICACIÓN PRINCIPAL
# ============================================================

def clasificar(c):
    """
    Clasifica un candidato como:

      generador
      comercio
      dudoso
      descartado

    Nunca inventa un tipo cuando la evidencia no alcanza.
    """

    texto = _normalizar(_texto(c))

    if not texto:
        return "dudoso"

    # --------------------------------------------------------
    # 1. EDUCACIÓN
    # --------------------------------------------------------

    if _es_educacion(c):
        return "descartado"

    # --------------------------------------------------------
    # 2. CÁMARAS
    #
    # Nunca son generadores.
    # --------------------------------------------------------

    if _es_camara(c):
        return "dudoso"

    # --------------------------------------------------------
    # 3. SERVICIOS QUE PERTENECEN A UNA ORGANIZACIÓN
    #
    # Primero evitamos que "sindical", "cooperativa", etc.
    # conviertan una farmacia/clinica/sanatorio en generador.
    # --------------------------------------------------------

    tipo_servicio = _clasificar_por_tipo_organizacion(c)

    if tipo_servicio:
        return tipo_servicio

    # --------------------------------------------------------
    # 4. COLEGIOS Y CONSEJOS PROFESIONALES
    # --------------------------------------------------------

    if _es_colegio_profesional(c):
        return "generador"

    # --------------------------------------------------------
    # 5. TAGS COMERCIALES
    #
    # Va ANTES del "club" genérico.
    #
    # Esto evita:
    #   Club de la Milanesa -> comercio
    #   Club Milanesa -> comercio
    #   Club de Amigos Gym -> comercio
    #   Lomo Club -> comercio si OSM lo identifica como comida
    # --------------------------------------------------------

    tipo_tags = _tipo_por_tags(c)

    if tipo_tags == "comercio":
        return "comercio"

    # --------------------------------------------------------
    # 6. COMERCIO CLARO POR NOMBRE
    # --------------------------------------------------------

    if _es_comercio_por_nombre(c):
        return "comercio"

    # --------------------------------------------------------
    # 7. GENERADORES INSTITUCIONALES
    #
    # Después de eliminar servicios/comercios.
    # --------------------------------------------------------

    if _es_generador_institucional(c):
        return "generador"

    # --------------------------------------------------------
    # 8. CENTROS SOCIALES / VECINALES / JUBILADOS
    # --------------------------------------------------------

    if _es_centro_social(c):
        return "generador"

    # --------------------------------------------------------
    # 9. ASOCIACIONES CON EVIDENCIA DE MIEMBROS
    # --------------------------------------------------------

    if _es_asociacion_con_miembros(c):
        return "generador"

    # --------------------------------------------------------
    # 10. CLUBES E INSTITUCIONES DEPORTIVAS
    #
    # IMPORTANTE:
    # Club deportivo real -> generador.
    # Instalación deportiva genérica -> NO.
    # --------------------------------------------------------

    if _es_club_deportivo(c):
        return "generador"

    # --------------------------------------------------------
    # 11. OTROS TAGS ORGANIZACIONALES
    # --------------------------------------------------------

    if tipo_tags == "generador":
        return "generador"

    # --------------------------------------------------------
    # 12. INSTALACIÓN DEPORTIVA SIN EVIDENCIA DE ORGANIZACIÓN
    #
    # No la descartamos automáticamente porque podría necesitar
    # revisión, pero NO la contamos como generador.
    # --------------------------------------------------------

    if _es_instalacion_deportiva(c):
        return "dudoso"

    # --------------------------------------------------------
    # 13. ORGANIZACIONES GENÉRICAS
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
        return "dudoso"

    # --------------------------------------------------------
    # 14. NOMBRE DEMASIADO GENÉRICO
    # --------------------------------------------------------

    palabras = texto.split()

    if len(palabras) <= 1:
        return "dudoso"

    # --------------------------------------------------------
    # 15. SIN EVIDENCIA SUFICIENTE
    # --------------------------------------------------------

    return "dudoso"


# ============================================================
# COMPATIBILIDAD
# ============================================================

def clasificar_candidato(c):
    """
    Alias de compatibilidad por si otro módulo lo utiliza.
    """
    return clasificar(c)
