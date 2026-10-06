from .util import normalizar_texto

GENERATOR_RULES = [
    "sindicato", "sindical", "gremio", "mutual", "cooperativa",
    "colegio profesional", "colegio de", "club", "asociacion",
    "asociación", "camara", "cámara", "federacion", "federación",
    "instituto", "fundacion", "fundación", "union", "unión",
    "sociedad", "corporacion", "corporación", "colegio",
]
COMMERCE_RULES = [
    "supermercado", "almacen", "almacén", "kiosco", "panader",
    "restaurante", "bar", "cafeter", "helader", "hotel", "peluquer",
    "barber", "farmacia", "optica", "óptica", "indumentaria", "zapater",
    "libreria", "librería", "gimnasio", "mecanica", "mecánica", "taller",
    "ferreter", "muebler", "electro", "inmobiliaria", "veterinaria",
    "consultorio", "estetica", "estética", "salon", "salón", "tienda",
]
EXCLUDE = [
    "parking", "estacionamiento", "naranjita", "parquimetro",
    "parquímetro", "municipalidad", "policia", "policía",
]

def clasificar(c):
    text = normalizar_texto(" ".join([
        c.get("name", ""),
        str(c.get("tags", {}).get("shop", "")),
        str(c.get("tags", {}).get("amenity", "")),
        str(c.get("tags", {}).get("office", "")),
        str(c.get("tags", {}).get("club", "")),
        str(c.get("tags", {}).get("leisure", "")),
    ]))
    if any(x in text for x in EXCLUDE):
        return "descartado", "categoria_excluida"
    gh = [x for x in GENERATOR_RULES if x in text]
    ch = [x for x in COMMERCE_RULES if x in text]
    if gh and not ch:
        return "generador", ",".join(gh[:3])
    if ch and not gh:
        return "comercio", ",".join(ch[:3])
    if gh and ch:
        return "dudoso", "ambas_categorias"
    return "dudoso", "sin_indicio_suficiente"
