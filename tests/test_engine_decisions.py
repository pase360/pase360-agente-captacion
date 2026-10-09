import unittest

from agente.engine import _aplicar_decision_humana, _key


class TestAplicacionDecisionHumana(unittest.TestCase):
    def test_aplica_decision_guardada_al_candidato(self):
        candidato = {"name": "Asociación de Prueba", "website": "https://prueba.org"}
        clave = _key(candidato)
        historial = {"decisiones": {clave: "generador"}}

        resultado = _aplicar_decision_humana(candidato, historial)

        self.assertEqual(resultado["tipo"], "generador")
        self.assertEqual(
            resultado["clasificacion_motivo"],
            "Decisión humana registrada en GitHub",
        )

    def test_aplica_decision_por_identidad_estable_aunque_cambie_email(self):
        candidato = {
            "name": "Asociación de Prueba",
            "source_id": "node:987",
            "email": "nuevo@prueba.org",
        }
        from agente.engine import _clave_identidad_estable
        clave_estable = _clave_identidad_estable(candidato)
        historial = {"decisiones": {clave_estable: "descartado"}}

        resultado = _aplicar_decision_humana(candidato, historial)

        self.assertEqual(resultado["tipo"], "descartado")

    def test_no_modifica_candidato_sin_decision(self):
        candidato = {"name": "Comercio de Prueba"}
        historial = {"decisiones": {}}

        resultado = _aplicar_decision_humana(candidato, historial)

        self.assertNotIn("tipo", resultado)


    def test_preguntas_no_repite_candidato_con_decision_guardada(self):
        from unittest.mock import patch
        from agente import engine

        candidato = {
            "name": "Asociación de Prueba",
            "source_id": "node:987",
            "estado": "requiere_decision",
        }
        clave_estable = engine._clave_identidad_estable(candidato)
        historial = {
            "contactados": {},
            "descartados": {},
            "preguntas": {},
            "seguimientos": {},
            "decisiones": {clave_estable: "descartado"},
        }

        with patch.object(engine, "_historial", return_value=historial), patch.object(engine, "_sincronizar_decisiones"), patch.object(engine, "cargar", return_value=[candidato]), patch.object(engine, "_guardar_hist"), patch.object(engine.github_issues, "crear_pregunta") as crear:
            resultado = engine.preguntas()

        self.assertEqual(resultado["creadas"], 0)
        crear.assert_not_called()

    def test_preguntas_no_repite_issue_ya_registrado(self):
        from unittest.mock import patch
        from agente import engine

        candidato = {
            "name": "Comercio Dudoso",
            "website": "https://ejemplo.org",
            "estado": "requiere_decision",
        }
        clave = engine._key(candidato)
        historial = {
            "contactados": {},
            "descartados": {},
            "preguntas": {clave: "https://github.com/pase360/pase360-agente-captacion/issues/123"},
            "seguimientos": {},
            "decisiones": {},
        }

        with patch.object(engine, "_historial", return_value=historial), \\
             patch.object(engine, "_sincronizar_decisiones"), \\
             patch.object(engine, "cargar", return_value=[candidato]), \\
             patch.object(engine, "_guardar_hist"), \\
             patch.object(engine.github_issues, "crear_pregunta") as crear:
            resultado = engine.preguntas()

        self.assertEqual(resultado["creadas"], 0)
        crear.assert_not_called()

if __name__ == "__main__":
    unittest.main()
