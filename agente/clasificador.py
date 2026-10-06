from .util import normalizar_texto


# ============================================================
# GENERADORES REALES
# ============================================================

GENERATOR_STRONG = (
    "sindicato",
    "sindicatos",
    "sindical",
    "sindicales",
    "gremio",
    "gremial",
    "gremiales",
    "union de trabajadores",
    "unión de trabajadores",
    "union obrera",
    "unión obrera",
    "union de empleados",
    "unión de empleados",
    "union del personal",
    "unión del personal",
    "mutual",
    "mutualidad",
    "mutuales",
    "federacion de trabajadores",
    "federación de trabajadores",
    "federacion sindical",
    "federación sindical",
    "federacion de sindicatos",
    "federación de sindicatos",
    "federacion gremial",
    "federación gremial",
    "asociacion profesional",
    "asociación profesional",
    "asociacion de profesionales",
    "asociación de profesionales",
    "asociacion de trabajadores",
    "asociación de trabajadores",
    "asociacion de empleados",
    "asociación de empleados",
    "asociacion gremial",
    "asociación gremial",
    "cooperativa",
    "cooperativas",
)


# Palabras que solas NO alcanzan para ser generador.
GENERIC_GENERATOR_WORDS = (
    "asociacion",
    "asociación",
    "federacion",
    "federación",
    "union",
    "unión",
)


# ============================================================
# COLEGIOS PROFESIONALES
# ============================================================

PROFESSIONAL_COLLEGE_WORDS = (
    "colegio de abogados",
    "colegio de arquitectos",
    "colegio de ingenieros",
    "colegio de contadores",
    "colegio de escribanos",
    "colegio de procuradores",
    "colegio de medicos",
    "colegio de médicos",
    "colegio de odontologos",
    "colegio de odontólogos",
    "colegio de psicologos",
    "colegio de psicólogos",
    "colegio de farmaceuticos",
    "colegio de farmacéuticos",
    "colegio de kinesiologos",
    "colegio de kinesiólogos",
    "colegio de veterinarios",
    "colegio de trabajadores sociales",
    "colegio de martilleros",
    "colegio de corredores inmobiliarios",
    "colegio de corredores publicos",
    "colegio de corredores públicos",
    "colegio de nutricionistas",
    "colegio de bioquimicos",
    "colegio de bioquímicos",
    "colegio de fonoaudiologos",
    "colegio de fonoaudiólogos",
    "colegio de instrumentadores",
    "colegio de enfermeros",
    "colegio de enfermeras",
    "colegio de trabajadores de la salud",
    "colegio profesional",
    "colegio de profesionales",
)


# ============================================================
# ASOCIACIONES PROFESIONALES
# ============================================================

PROFESSIONAL_ASSOCIATION_WORDS = (
    "asociacion de abogados",
    "asociación de abogados",
    "asociacion de arquitectos",
    "asociación de arquitectos",
    "asociacion de ingenieros",
    "asociación de ingenieros",
    "asociacion de contadores",
    "asociación de contadores",
    "asociacion de escribanos",
    "asociación de escribanos",
    "asociacion de medicos",
    "asociación de médicos",
    "asociacion de odontologos",
    "asociación de odontólogos",
    "asociacion de psicologos",
    "asociación de psicólogos",
    "asociacion de farmaceuticos",
    "asociación de farmacéuticos",
    "asociacion profesional",
    "asociación profesional",
    "asociacion de profesionales",
    "asociación de profesionales",
)


# ============================================================
# CLUBES QUE PUEDEN SER GENERADORES
# ============================================================

CLUB_WORDS = (
    "club atletico",
    "club atlético",
    "club deportivo",
    "club social",
    "club social y deportivo",
    "club de futbol",
    "club de fútbol",
    "club de rugby",
    "club de hockey",
    "club de basquet",
    "club de básquet",
    "club de voleibol",
    "club de voley",
    "club nautico",
    "club náutico",
    "club de pesca",
    "club de golf",
    "club de tenis",
)


# ============================================================
# OTROS GENERADORES POR CONTEXTO
# ============================================================

GENERATOR_CONTEXT_WORDS = (
    "centro de jubilados",
    "centro de jubiladas",
    "centro de pensionados",
    "centro de pensionadas",
    "centro de trabajadores",
    "centro de empleados",
    "centro de profesionales",
    "asociacion de vecinos",
    "asociación de vecinos",
    "union vecinal",
    "unión vecinal",
)


# ============================================================
# COMERCIOS
# ============================================================

COMMERCE_WORDS = (
    "supermercado",
    "hipermercado",
    "almacen",
    "almacén",
    "autoservicio",
    "kiosco",
    "panaderia",
    "panadería",
    "restaurante",
    "parrilla",
    "bar",
    "cafeteria",
    "cafetería",
    "heladeria",
    "heladería",
    "pizzeria",
    "pizzería",
    "hotel",
    "hosteria",
    "hostería",
    "peluqueria",
    "peluquería",
    "barberia",
    "barbería",
    "farmacia",
    "optica",
    "óptica",
    "indumentaria",
    "zapateria",
    "zapatería",
    "libreria",
    "librería",
    "jugueteria",
    "juguetería",
    "gimnasio",
    "fitness",
    "crossfit",
    "mecanica",
    "mecánica",
    "taller",
    "ferreteria",
    "ferretería",
    "muebleria",
    "mueblería",
    "electrodomesticos",
    "electrodomésticos",
    "inmobiliaria",
    "veterinaria",
    "consultorio",
    "odontologia",
    "odontología",
    "estetica",
    "estética",
    "salon de belleza",
    "salón de belleza",
    "tienda",
    "boutique",
    "concesionaria",
    "lavadero",
    "repuestos",
    "neumaticos",
    "neumáticos",
    "reposteria",
    "repostería",
    "rotiseria",
    "rotisería",
    "dietética",
    "vinoteca",
    "cerveceria",
    "cervecería",
    "carniceria",
    "carnicería",
    "verduleria",
    "verdulería",
    "floreria",
    "florería",
    "pet shop",
    "tienda de mascotas",
    "agencia de viajes",
    "turismo",
    "spa",
)


# ============================================================
# CATEGORÍAS OBLIGATORIAMENTE EXCLUIDAS
# ============================================================

EXCLUDE_WORDS = (
    "parking",
    "estacionamiento",
    "naranjita",
    "parquimetro",
    "parquímetro",
    "municipalidad",
    "municipio",
    "policia",
    "policía",
    "comisaria",
    "comisaría",
    "hospital publico",
    "hospital público",
    "iglesia",
    "parroquia",
    "capilla",
    "basílica",
    "basilica",
    "templo",
    "museo",
    "monumento",
    "plaza",
    "parque publico",
    "parque público",
    "secretaria de",
    "secretaría de",
    "ministerio",
    "gobierno",
    "municipal",
    "provincial",
    "nacional",
    "jardin de infantes",
    "jardín de infantes",
    "instituto de enseñanza",
    "instituto educativo",
    "instituto educacional",
    "universidad",
    "facultad",
    "escuela",
    "colegio secundario",
    "colegio primario",
)


# ============================================================
# VALORES OSM
# ============================================================

SHOP_VALUES = {
    "supermarket",
    "convenience",
    "bakery",
    "butcher",
    "deli",
    "kiosk",
    "department_store",
    "clothes",
    "shoes",
    "jewelry",
    "books",
    "furniture",
    "hardware",
    "electronics",
    "mobile_phone",
    "computer",
    "beauty",
    "hairdresser",
    "car",
    "car_parts",
    "car_repair",
    "bicycle",
    "florist",
    "pet",
    "chemist",
    "pharmacy",
    "optician",
    "sports",
    "outdoor",
    "gift",
    "toys",
    "travel_agency",
    "alcohol",
}


COMMERCE_AMENITIES = {
    "restaurant",
    "cafe",
    "bar",
    "fast_food",
    "pub",
    "ice_cream",
    "fuel",
    "pharmacy",
    "clinic",
    "dentist",
    "veterinary",
    "hotel",
    "hostel",
}


# Solo social_centre se considera institucional por etiqueta.
# community_centre queda dudoso salvo que el nombre aporte
# evidencia suficiente de que reúne miembros/afiliados.
GENERATOR_AMENITIES = {
    "social_centre",
}


# NO se consideran generadores automáticamente.
# sports_centre y stadium pueden ser simples instalaciones.
GENERATOR_LEISURE = set()


# ============================================================
# UTILIDADES
# ============================================================

def _texto(c):
    tags = c.get("tags") or {}

    partes = [
        c.get("name", ""),
        tags.get("official_name", ""),
        tags.get("short_name", ""),
        tags.get("description", ""),
        tags.get("operator", ""),
        tags.get("brand", ""),
        tags.get("organization", ""),
        tags.get("club", ""),
        tags.get("sport", ""),
        tags.get("sports", ""),
        tags.get("office", ""),
        tags.get("amenity", ""),
        tags.get("leisure", ""),
        tags.get("tourism", ""),
        tags.get("shop", ""),
        tags.get("craft", ""),
    ]

    return normalizar_texto(
        " ".join(
            str(x or "")
            for x in partes
        )
    )


def _tags(c):
    tags = c.get("tags") or {}

    return {
        "shop": normalizar_texto(tags.get("shop", "")),
        "amenity": normalizar_texto(tags.get("amenity", "")),
        "leisure": normalizar_texto(tags.get("leisure", "")),
        "office": normalizar_texto(tags.get("office", "")),
        "sport": normalizar_texto(tags.get("sport", "")),
        "sports": normalizar_texto(tags.get("sports", "")),
        "tourism": normalizar_texto(tags.get("tourism", "")),
        "craft": normalizar_texto(tags.get("craft", "")),
    }


def _contiene(texto, palabras):
    resultado = []

    for palabra in palabras:
        normalizada = normalizar_texto(palabra)

        if normalizada and normalizada in texto:
            resultado.append(normalizada)

    return resultado


# ============================================================
# GENERADORES
# ============================================================

def _es_colegio_profesional(texto):
    return bool(
        _contiene(
            texto,
            PROFESSIONAL_COLLEGE_WORDS,
        )
    )


def _es_asociacion_profesional(texto):
    return bool(
        _contiene(
            texto,
            PROFESSIONAL_ASSOCIATION_WORDS,
        )
    )


def _es_generador_institucional(texto):
    encontrados = _contiene(
        texto,
        GENERATOR_STRONG,
    )

    if encontrados:
        return encontrados

    genericos = _contiene(
        texto,
        GENERIC_GENERATOR_WORDS,
    )

    contexto = _contiene(
        texto,
        (
            "trabajadores",
            "trabajador",
            "empleados",
            "empleado",
            "profesionales",
            "profesional",
            "afiliados",
            "afiliado",
            "asociados",
            "asociado",
            "matriculados",
            "matriculado",
            "gremio",
            "gremial",
            "sindical",
            "sindicato",
            "colegio",
            "miembros",
            "miembro",
        ),
    )

    if genericos and contexto:
        return genericos + contexto[:2]

    return []


def _es_club_deportivo(c, texto):
    tags = _tags(c)

    # Clubes claramente identificables como instituciones.
    if _contiene(texto, CLUB_WORDS):
        return True

    # Si OSM identifica explícitamente "club" y además
    # hay deporte asociado, puede ser un club institucional.
    if "club" in texto:
        if tags["sport"] or tags["sports"]:
            return True

        if _contiene(
            texto,
            (
                "atletico",
                "atlético",
                "deportivo",
                "social",
                "futbol",
                "fútbol",
                "rugby",
                "hockey",
                "basquet",
                "básquet",
                "voley",
                "voleibol",
                "tenis",
                "golf",
                "pesca",
                "nautico",
                "náutico",
            ),
        ):
            return True

    return False


def _es_generador_por_contexto(texto):
    return _contiene(
        texto,
        GENERATOR_CONTEXT_WORDS,
    )


def _es_asociacion_con_miembros(texto):
    """
    Asociación civil genérica:
    solo se acepta cuando el nombre aporta evidencia de
    personas/colectivos que pueden ser beneficiarios.
    """
    if "asociacion civil" not in texto and "asociación civil" not in texto:
        return False

    contexto = (
        "afiliados",
        "afiliado",
        "asociados",
        "asociado",
        "miembros",
        "miembro",
        "profesionales",
        "profesional",
        "trabajadores",
        "trabajador",
        "empleados",
        "empleado",
        "vecinos",
        "vecinal",
        "jubilados",
        "jubiladas",
        "pensionados",
        "pensionadas",
        "familias",
        "deportistas",
    )

    return bool(_contiene(texto, contexto))


# ============================================================
# COMERCIOS
# ============================================================

def _es_comercio_estructurado(c):
    tags = _tags(c)

    if tags["shop"] in SHOP_VALUES:
        return True, f"shop:{tags['shop']}"

    if tags["amenity"] in COMMERCE_AMENITIES:
        return True, f"amenity:{tags['amenity']}"

    return False, ""


def _es_comercio_por_texto(texto):
    encontrados = _contiene(
        texto,
        COMMERCE_WORDS,
    )

    if encontrados:
        return encontrados[:3]

    return []


# ============================================================
# CLASIFICACIÓN PRINCIPAL
# ============================================================

def clasificar(c):
    texto = _texto(c)
    tags = _tags(c)

    if not texto:
        return "dudoso", "sin_nombre"

    # --------------------------------------------------------
    # 1. EXCLUSIONES
    # --------------------------------------------------------

    excluidos = _contiene(
        texto,
        EXCLUDE_WORDS,
    )

    if excluidos:
        # Los colegios profesionales son una excepción válida.
        if not _es_colegio_profesional(texto):
            return (
                "descartado",
                "categoria_excluida:"
                + ",".join(excluidos[:3]),
            )

    # --------------------------------------------------------
    # 2. CÁMARAS
    # --------------------------------------------------------

    camaras = _contiene(
        texto,
        (
            "camara de comercio",
            "cámara de comercio",
            "camara empresarial",
            "cámara empresarial",
            "camara de comerciantes",
            "cámara de comerciantes",
            "camara industrial",
            "cámara industrial",
            "camara de turismo",
            "cámara de turismo",
            "camara argentina",
            "cámara argentina",
            "camara de",
            "cámara de",
        ),
    )

    if camaras:
        return (
            "dudoso",
            "camara_no_generador",
        )

    # --------------------------------------------------------
    # 3. GENERADORES INSTITUCIONALES
    # --------------------------------------------------------

    generadores = _es_generador_institucional(texto)

    if generadores:
        return (
            "generador",
            "institucional:"
            + ",".join(generadores[:3]),
        )

    # --------------------------------------------------------
    # 4. COLEGIOS PROFESIONALES
    # --------------------------------------------------------

    if _es_colegio_profesional(texto):
        return (
            "generador",
            "colegio_profesional",
        )

    # --------------------------------------------------------
    # 5. ASOCIACIONES PROFESIONALES
    # --------------------------------------------------------

    if _es_asociacion_profesional(texto):
        return (
            "generador",
            "asociacion_profesional",
        )

    # --------------------------------------------------------
    # 6. ASOCIACIONES CIVILES CON EVIDENCIA
    # --------------------------------------------------------

    if _es_asociacion_con_miembros(texto):
        return (
            "generador",
            "asociacion_civil_con_miembros",
        )

    # --------------------------------------------------------
    # 7. GENERADORES POR CONTEXTO
    # --------------------------------------------------------

    generadores_contexto = _es_generador_por_contexto(texto)

    if generadores_contexto:
        return (
            "generador",
            "institucion:"
            + ",".join(generadores_contexto[:3]),
        )

    # --------------------------------------------------------
    # 8. CLUBES DEPORTIVOS
    # --------------------------------------------------------

    if _es_club_deportivo(c, texto):
        return (
            "generador",
            "club_deportivo",
        )

    # --------------------------------------------------------
    # 9. AMENITY INSTITUCIONAL
    # --------------------------------------------------------

    if tags["amenity"] in GENERATOR_AMENITIES:
        return (
            "generador",
            "amenity_institucional:"
            + tags["amenity"],
        )

    # --------------------------------------------------------
    # 10. COMERCIO ESTRUCTURADO
    # --------------------------------------------------------

    es_comercio, motivo_comercio = _es_comercio_estructurado(c)

    if es_comercio:
        return (
            "comercio",
            motivo_comercio,
        )

    # --------------------------------------------------------
    # 11. COMERCIO POR TEXTO
    # --------------------------------------------------------

    comercios = _es_comercio_por_texto(texto)

    if comercios:
        return (
            "comercio",
            ",".join(comercios),
        )

    # --------------------------------------------------------
    # 12. CRAFT
    # --------------------------------------------------------

    if tags["craft"]:
        return (
            "comercio",
            f"craft:{tags['craft']}",
        )

    # --------------------------------------------------------
    # 13. TURISMO COMERCIAL
    # --------------------------------------------------------

    if tags["tourism"] in {
        "hotel",
        "hostel",
        "guest_house",
        "motel",
        "camp_site",
        "caravan_site",
    }:
        return (
            "comercio",
            f"tourism:{tags['tourism']}",
        )

    # --------------------------------------------------------
    # 14. TODO LO DEMÁS
    # --------------------------------------------------------

    return (
        "dudoso",
        "sin_indicio_suficiente",
    )
