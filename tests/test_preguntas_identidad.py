import unittest
from unittest.mock import patch

from agente import engine


class TestPreguntasIdentidadEstable(unittest.TestCase):
    def _estado(self):
        return {
            "contactados": {},
            "descartados": {},
            "preguntas": {},
            "seguimientos": {},
            "decisiones": {},
        }

    def test_no_repite_issue_si_el_email_cambio_la_clave(self):
        candidato = {
            "name": "Asociación de Prueba",
            "source_id": "node:456",
            "email": "contacto@asociacion.org.ar",
            "estado": "requiere_decision",
        }
        estado = self._estado()
        estado["preguntas"]["source:node:456"] = "https://github.com/example/1"

        with patch.object(engine, "_historial", return_value=estado), \
             patch.object(engine, "_sincronizar_decisiones"), \
             patch.object(engine, "cargar", return_value=[candidato]), \
             patch.object(engine, "_guardar_hist"), \
             patch.object(engine.github_issues, "crear_pregunta") as crear:
            resultado = engine.preguntas()

        self.assertEqual(resultado["creadas"], 0)
        crear.assert_not_called()

    def test_guarda_issue_con_clave_estable(self):
        candidato = {
            "name": "Asociación de Prueba",
            "source_id": "node:789",
            "email": "",
            "estado": "requiere_decision",
        }
        estado = self._estado()

        with patch.object(engine, "_historial", return_value=estado), \
             patch.object(engine, "_sincronizar_decisiones"), \
             patch.object(engine, "cargar", return_value=[candidato]), \
             patch.object(engine, "_guardar_hist"), \
             patch.object(engine.github_issues, "crear_pregunta", return_value={"ok": True, "url": "https://github.com/example/2"}):
            resultado = engine.preguntas()

        self.assertEqual(resultado["creadas"], 1)
        self.assertIn("source:node:789", estado["preguntas"])


if __name__ == "__main__":
    unittest.main()
