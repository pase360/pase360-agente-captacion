import unittest

from agente.fuentes import _fusionar


class TestFusionFuentes(unittest.TestCase):
    def test_promueve_fuente_generador_sin_perder_email(self):
        mixto = {
            "name": "Club de Prueba",
            "source": "osm_email",
            "grupo_fuente": "mixto",
            "source_id": "node:123",
            "email": "contacto@clubprueba.com.ar",
            "tags": {"name": "Club de Prueba", "email": "contacto@clubprueba.com.ar"},
        }
        generador = {
            "name": "Club de Prueba",
            "source": "generadores_clubes",
            "grupo_fuente": "generador",
            "source_id": "node:123",
            "email": "",
            "tags": {"name": "Club de Prueba", "club": "sport"},
        }

        resultado = _fusionar([mixto, generador])

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["grupo_fuente"], "generador")
        self.assertEqual(resultado[0]["source"], "generadores_clubes")
        self.assertEqual(resultado[0]["email"], "contacto@clubprueba.com.ar")


if __name__ == "__main__":
    unittest.main()
