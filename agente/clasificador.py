from .util import normalizar_texto


# ============================================================
# CLASIFICACIÓN GENERAL
# ============================================================
#
# Objetivo:
# - Generador = institución/organización que puede distribuir
#   beneficios a sus afiliados, miembros, alumnos, asociados, etc.
# - Comercio = negocio que ofrece el beneficio.
# - Descartado = entidad que no corresponde a ninguno.
# - Dudoso = no hay evidencia suficiente para decidir.
#
# IMPORTANTE:
# "club" NO alcanza por sí solo para ser generador.
#


GENERATOR_STRONG = {
    "sindicato",
    "sindical",
    "gremio",
    "union",
    "mutual",
    "cooperativa",
    "federacion",
    "federación",
    "asociacion",
    "asociación",
    "camara",
    "cámara",
    "corporacion",
    "corporación",
    "sociedad",
    "fundacion",
    "fundación",
}

GENERATOR_PROFESSIONAL = {
    "colegio profesional",
    "colegio de abogados",
    "colegio de arquitectos",
    "colegio de ingenieros",
    "colegio de escribanos",
    "colegio de medicos",
    "colegio de médicos",
    "colegio de odontologos",
    "colegio de odontólogos",
    "colegio de contadores",
    "colegio de psicologos",
    "colegio de psicólogos",
    "colegio de profesionales",
}

GENERATOR_EDUCATION = {
    "universidad",
    "facultad",
    "escuela",
    "colegio",
    "instituto educativo",
    "instituto de educacion",
    "instituto de educación",
    "instituto superior",
    "instituto provincial",
    "instituto privado",
    "jardin de infantes",
    "jardín de infantes",
}

GENERATOR_CLUB = {
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
    "club deportivo y social",
}

COMMERCE_WORDS = {
    "supermercado",
    "hipermercado",
    "almacen",
    "almacén",
    "kiosco",
    "panaderia",
    "panadería",
    "restaurante",
    "bar",
    "cafeteria",
    "cafetería",
    "heladeria",
    "heladería",
    "hotel",
    "hostel",
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
    "gimnasio",
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
    "estetica",
    "estética",
    "salon",
    "salón",
    "tienda",
    "boutique",
    "vinoteca",
    "bodega",
    "pizzeria",
    "pizzería",
    "carniceria",
    "carnicería",
    "verduleria",
    "verdulería",
    "rotiseria",
    "rotisería",
    "reposteria",
    "repostería",
    "confiteria",
    "confitería",
    "cerveceria",
    "cervecería",
    "joyeria",
    "joyería",
    "perfumeria",
    "perfumería",
    "lavadero",
    "concesionario",
    "agencia",
    "servicios",
}


EXCLUDE_WORDS = {
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
    "juzgado",
    "tribunal",
    "ministerio",
    "consulado",
    "embajada",
    "cementerio",
    "monumento",
    "plaza",
    "parque",
    "monumento historico",
    "monumento histórico",
}


# Etiquetas OSM que son una señal muy fuerte de actividad comercial.
SHOP_VALUES = {
    "supermarket",
    "convenience",
    "bakery",
    "butcher",
    "clothes",
    "shoes",
    "hairdresser",
    "beauty",
    "pharmacy",
    "optician",
    "books",
    "furniture",
    "electronics",
    "hardware",
    "mobile_phone",
    "jewelry",
    "gift",
    "florist",
    "kiosk",
    "car",
    "car_repair",
    "car_parts",
    "beverages",
    "alcohol",
    "coffee",
    "pastry",
    "seafood",
    "greengrocer",
    "department_store",
    "doityourself",
    "sports",
    "travel_agency",
    "estate_agent",
    "veterinary",
}


# Amenities que normalmente representan negocios o servicios.
COMMERCE_AMENITIES = {
    "restaurant",
    "cafe",
    "bar",
    "fast_food",
    "ice_cream",
    "pub",
    "fuel",
    "cinema",
    "theatre",
    "hotel",
    "hostel",
    "spa",
    "clinic",
    "dentist",
    "doctors",
    "veterinary",
}


# Etiquetas institucionales que pueden indicar generadores.
GENERATOR_AMENITIES = {
    "school",
    "college",
    "university",
    "kindergarten",
}


GENERATOR_LEISURE = {
    "sports_centre",
    "stadium",
}


def _texto(c):
    tags = c.get("tags") or {}

    partes = [
        c.get("name", ""),
        tags.get("official_name", ""),
        tags.get("operator", ""),
        tags.get("description", ""),
        tags.get("brand", ""),
        tags.get("organization", ""),
        tags.get("club", ""),
        tags.get("office", ""),
        tags.get("amenity", ""),
        tags.get("leisure", ""),
        tags.get("tourism", ""),
        tags.get("shop", ""),
        tags.get("craft", ""),
    ]

    return normalizar_texto(" ".join(str(x) for x in partes if x))


def _tags(c):
    return c.get("tags") or {}


def _contiene(texto, palabras):
    return [
        palabra
        for palabra in palabras
        if palabra in texto
    ]


def _es_club_deportivo(texto, tags):
    leisure = normalizar_texto(tags.get("leisure", ""))
    sport = normalizar_texto(tags.get("sport", ""))
    club = normalizar_texto(tags.get("club", ""))

    if leisure in GENERATOR_LEISURE:
        return True

    if sport:
        return True

    if club in {
        "sport",
        "sports",
        "social",
    }:
        return True

    if any(x in texto for x in GENERATOR_CLUB):
        return True

    return False


def _es_institucion_educativa(texto, tags):
    amenity = normalizar_texto(tags.get("amenity", ""))
    office = normalizar_texto(tags.get("office", ""))

    if amenity in GENERATOR_AMENITIES:
        return True

    if office in {
        "educational_institution",
        "association",
        "ngo",
        "charity",
    }:
        return True

    return bool(_contiene(texto, GENERATOR_EDUCATION))


def clasificar(c):
    tags = _tags(c)
    texto = _texto(c)

    # --------------------------------------------------------
    # 1. Exclusiones inequívocas
    # --------------------------------------------------------
    excluidas = _contiene(texto, EXCLUDE_WORDS)

    if excluidas:
        return (
            "descartado",
            "categoria_excluida:" + ",".join(excluidas[:3]),
        )

    # --------------------------------------------------------
    # 2. Señales estructuradas de comercio
    # --------------------------------------------------------
    shop = normalizar_texto(tags.get("shop", ""))
    amenity = normalizar_texto(tags.get("amenity", ""))

    if shop in SHOP_VALUES:
        # Si además tiene una señal institucional muy fuerte,
        # dejamos que la institución gane más adelante.
        strong_generators = _contiene(
            texto,
            GENERATOR_STRONG,
        )

        if not strong_generators:
            return (
                "comercio",
                "osm_shop:" + shop,
            )

    if amenity in COMMERCE_AMENITIES:
        strong_generators = _contiene(
            texto,
            GENERATOR_STRONG,
        )

        if not strong_generators:
            return (
                "comercio",
                "osm_amenity:" + amenity,
            )

    # --------------------------------------------------------
    # 3. Instituciones claramente reconocibles
    # --------------------------------------------------------
    strong = _contiene(
        texto,
        GENERATOR_STRONG,
    )

    professional = _contiene(
        texto,
        GENERATOR_PROFESSIONAL,
    )

    if strong:
        return (
            "generador",
            "institucional:" + ",".join(strong[:3]),
        )

    if professional:
        return (
            "generador",
            "colegio_profesional:"
            + ",".join(professional[:3]),
        )

    # --------------------------------------------------------
    # 4. Educación
    # --------------------------------------------------------
    if _es_institucion_educativa(texto, tags):
        return (
            "generador",
            "institucion_educativa",
        )

    # --------------------------------------------------------
    # 5. Clubes
    #
    # "club" solo NO alcanza.
    # Solo aceptamos club cuando hay señales deportivas/sociales
    # reales.
    # --------------------------------------------------------
    if _es_club_deportivo(texto, tags):
        return (
            "generador",
            "club_deportivo",
        )

    # --------------------------------------------------------
    # 6. Comercio por nombre
    # --------------------------------------------------------
    commerce = _contiene(
        texto,
        COMMERCE_WORDS,
    )

    if commerce:
        return (
            "comercio",
            "actividad_comercial:"
            + ",".join(commerce[:3]),
        )

    # --------------------------------------------------------
    # 7. Entidades explícitamente comerciales por OSM
    # --------------------------------------------------------
    craft = normalizar_texto(
        tags.get("craft", "")
    )

    if craft:
        return (
            "comercio",
            "osm_craft:" + craft,
        )

    tourism = normalizar_texto(
        tags.get("tourism", "")
    )

    if tourism in {
        "hotel",
        "guest_house",
        "hostel",
        "motel",
        "camp_site",
    }:
        return (
            "comercio",
            "osm_tourism:" + tourism,
        )

    # --------------------------------------------------------
    # 8. Si no hay evidencia suficiente, dudoso.
    # --------------------------------------------------------
    return (
        "dudoso",
        "sin_indicio_suficiente",
    )
