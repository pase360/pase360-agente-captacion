import unittest
from unittest.mock import patch

from agente import engine


class TestReporte(unittest.TestCase):
    def test_separa_metricas_historicas_del_ultimo_escaneo(self):
        historial = {
            "contactados": {"a": {}, "b": {}},
            "preguntas": {"x": "url-1"},
            "descartados": {},
            "seguimientos": {},
            "decisiones": {},
        }
        candidatos_historicos = [
            {"estado": "listo_para_contactar"},
            {"estado": "listo_para_contactar"},
            {"estado": "sin_email"},
            {"estado": "requiere_decision"},
        ]
        ultimo_diagnostico = {
            "fecha_ejecucion": "2026-10-09T09:00:00",
            "encontrados": 300,
            "clasificados": 90,
            "nuevos": 75,
            "por_estado": {
                "listo_para_contactar": 7,
                "sin_email": 60,
                "requiere_decision": 20,
                "descartado": 3,
            },
            "cuadre": {"cuadra": True},
        }

        with patch.object(engine, "_historial", return_value=historial), \
             patch.object(engine, "cargar", side_effect=[candidatos_historicos, ultimo_diagnostico]), \
             patch.object(engine, "guardar") as guardar:
            resultado = engine.reporte()

        self.assertEqual(resultado["candidatos_historicos_guardados"], 4)
        self.assertEqual(resultado["contactados_historicos"], 2)
        self.assertEqual(resultado["preguntas_historicas_creadas"], 1)
        self.assertEqual(resultado["ultimo_escaneo_listos"], 7)
        self.assertEqual(resultado["ultimo_escaneo_sin_email"], 60)
        self.assertEqual(resultado["ultimo_escaneo_dudosos"], 20)
        self.assertEqual(resultado["ultimo_escaneo_descartados"], 3)
        self.assertEqual(resultado["fecha_ultimo_escaneo"], "2026-10-09T09:00:00")
        self.assertTrue(resultado["ultimo_escaneo_cuadre"]["cuadra"])
        guardar.assert_called_once_with("reporte.json", resultado)

    def test_reporte_sin_diagnostico_no_falla(self):
        historial = {
            "contactados": {},
            "preguntas": {},
            "descartados": {},
            "seguimientos": {},
            "decisiones": {},
        }
        with patch.object(engine, "_historial", return_value=historial), \
             patch.object(engine, "cargar", side_effect=[[], {}]), \
             patch.object(engine, "guardar"):
            resultado = engine.reporte()

        self.assertEqual(resultado["ultimo_escaneo_listos"], 0)
        self.assertIsNone(resultado["fecha_ultimo_escaneo"])


if __name__ == "__main__":
    unittest.main()
