from .util import normalizar_texto


# ============================================================
# GENERADORES REALES
# ============================================================
# Organizaciones que reúnen personas afiliadas, matriculadas,
# asociadas o adherentes y que pueden distribuir beneficios.
#
# IMPORTANTE:
# - "colegio" significa COLEGIO PROFESIONAL.
# - cámaras NO son generadores.
# - empresas/sociedades NO son generadores por su forma jurídica.
# - escuelas/colegios educativos NO son generadores.
# ============================================================

GENERATOR_STRONG = (
    "sindicato",
    "sindical",
    "gremio",
    "union de trabajadores",
    "unión de trabajadores",
    "mutual",
    "federacion de trabajadores",
    "federación de trabajadores",
    "federacion sindical",
    "federación sindical",
    "asociacion profesional",
    "asociación profesional",
    "asociacion de profesionales",
    "asociación de profesionales",
    "asociacion civil",
    "asociación civil",
    "cooperativa",
    "fundacion",
    "fundación",
)

# Colegio solamente cuando se refiere a profesionales.
PROFESSIONAL_COLLEGE_WORDS = (
    "colegio de abogados",
    "colegio de arquitectos",
    "colegio de ingenieros",
    "colegio de contadores",
    "colegio de escribanos",
    "colegio de procuradores",
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
    "colegio de veterinarios",
    "colegio de trabajadores sociales",
    "colegio profesional",
    "colegio de profesionales",
    "colegio profesional de",
)

# Federaciones/asociaciones profesionales.
PROFESSIONAL_ASSOCIATION_WORDS = (
    "asociacion de abogados",
    "asociación de abogados",
    "asociacion de arquitectos",
    "asociación de arquitectos",
    "asociacion de ingenieros",
    "asociación de ingenieros",
    "asociacion de contadores",
    "asociación de contadores",
    "asociacion de médicos",
    "asociación de medicos",
    "asociacion de odontologos",
    "asociación de odontólogos",
    "asociacion de psicologos",
    "asociación de psicólogos",
    "asociacion profesional",
    "asociación profesional",
    "asociacion de profesionales",
    "asociación de profesionales",
)

# Clubes que realmente funcionan como instituciones deportivas/sociales.
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

GENERATOR_AMENITIES = {
    "social_centre",
}

GENERATOR_LEISURE = {
    "sports_centre",
    "stadium",
}


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

    return normalizar_texto(" ".join(str(x or "") for x in partes))


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
    return [p for p in palabras if normalizar_texto(p) in texto]


# ============================================================
# GENERADORES
# ============================================================

def _es_colegio_profesional(texto):
    return bool(_contiene(texto, PROFESSIONAL_COLLEGE_WORDS))


def _es_asociacion_profesional(texto):
    return bool(_contiene(texto, PROFESSIONAL_ASSOCIATION_WORDS))


def _es_generador_institucional(texto):
    """
    Detecta organizaciones de afiliados.

    NO considera:
    - cámara
    - sociedad
    - corporación
    - empresa
    - compañía

    porque esas palabras pueden identificar simplemente
    empresas comerciales.
    """
    encontrados = _contiene(texto, GENERATOR_STRONG)
    return encontrados


def _es_club_deportivo(c, texto):
    tags = _tags(c)

    # Nombre explícito de club deportivo/social.
    if _contiene(texto, CLUB_WORDS):
        return True

    # Un sports_centre o stadium puede ser una institución
    # deportiva, pero no cualquier gimnasio comercial.
    if tags["leisure"] in GENERATOR_LEISURE:
        return True

    # "club" explícito + actividad deportiva.
    if "club" in texto:
        if tags["sport"] or tags["sports"]:
            return True

        if any(
            palabra in texto
            for palabra in (
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
            )
        ):
            return True

    return False


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
    encontrados = _contiene(texto, COMMERCE_WORDS)

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
    excluidos = _contiene(texto, EXCLUDE_WORDS)

    if excluidos:
        # "colegio profesional" sí es un generador válido.
        if not _es_colegio_profesional(texto):
            return "descartado", f"categoria_excluida:{','.join(excluidos[:3])}"

    # --------------------------------------------------------
    # 2. CÁMARAS
    # --------------------------------------------------------
    # Una cámara NO es generador.
    # Se conserva como dudosa para una futura etapa de
    # captación de comercios asociados a cámaras.
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
        ),
    )

    if camaras:
        return "dudoso", "camara_no_generador"

    # --------------------------------------------------------
    # 3. COMERCIO ESTRUCTURADO
    # --------------------------------------------------------
    es_comercio, motivo_comercio = _es_comercio_estructurado(c)

    if es_comercio:
        return "comercio", motivo_comercio

    # --------------------------------------------------------
    # 4. GENERADORES INSTITUCIONALES
    # --------------------------------------------------------
    generadores = _es_generador_institucional(texto)

    if generadores:
        return "generador", f"institucional:{','.join(generadores[:3])}"

    # --------------------------------------------------------
    # 5. COLEGIOS PROFESIONALES
    # --------------------------------------------------------
    if _es_colegio_profesional(texto):
        return "generador", "colegio_profesional"

    # --------------------------------------------------------
    # 6. ASOCIACIONES PROFESIONALES
    # --------------------------------------------------------
    if _es_asociacion_profesional(texto):
        return "generador", "asociacion_profesional"

    # --------------------------------------------------------
    # 7. CLUBES DEPORTIVOS
    # --------------------------------------------------------
    if _es_club_deportivo(c, texto):
        return "generador", "club_deportivo"

    # --------------------------------------------------------
    # 8. AMENITIES INSTITUCIONALES
    # --------------------------------------------------------
    if tags["amenity"] in GENERATOR_AMENITIES:
        return "generador", f"amenity_institucional:{tags['amenity']}"

    # --------------------------------------------------------
    # 9. COMERCIO POR NOMBRE / TEXTO
    # --------------------------------------------------------
    comercios = _es_comercio_por_texto(texto)

    if comercios:
        return "comercio", ",".join(comercios)

    # --------------------------------------------------------
    # 10. CRAFT
    # --------------------------------------------------------
    if tags["craft"]:
        return "comercio", f"craft:{tags['craft']}"

    # --------------------------------------------------------
    # 11. TURISMO COMERCIAL
    # --------------------------------------------------------
    if tags["tourism"] in {
        "hotel",
        "hostel",
        "guest_house",
        "motel",
        "camp_site",
        "caravan_site",
    }:
        return "comercio", f"tourism:{tags['tourism']}"

    # --------------------------------------------------------
    # 12. TODO LO DEMÁS QUEDA EN REVISIÓN
    # --------------------------------------------------------
    return "dudoso", "sin_indicio_suficiente"
