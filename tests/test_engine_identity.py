import unittest
from unittest.mock import patch

from agente import engine


class TestFusionIdentidadEstable(unittest.TestCase):
    def test_no_duplica_candidato_cuando_se_descubre_email(self):
        anterior = {
            "name": "Comercio Ejemplo",
            "source_id": "node:123",
            "email": "",
            "estado": "sin_email",
        }
        actualizado = {
            "name": "Comercio Ejemplo",
            "source_id": "node:123",
            "email": "contacto@ejemplo.com.ar",
            "estado": "listo_para_contactar",
        }
        with patch.object(engine, "cargar", return_value=[anterior]):
            resultado = engine._fusionar_base_candidatos([actualizado])

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["email"], "contacto@ejemplo.com.ar")
        self.assertEqual(resultado[0]["estado"], "listo_para_contactar")


if __name__ == "__main__":
    unittest.main()
