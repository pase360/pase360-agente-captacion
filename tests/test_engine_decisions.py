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


if __name__ == "__main__":
    unittest.main()
