import unittest
from unittest.mock import Mock, patch

from agente import github_issues


class TestDecisionesHumanas(unittest.TestCase):
    @patch("agente.github_issues.requests.patch")
    @patch("agente.github_issues.requests.get")
    @patch("agente.github_issues._config", return_value=("token", "pase360/pase360-agente-captacion"))
    def test_lee_comando_exacto_y_cierra_issue(self, config, get, patch_request):
        respuesta = Mock()
        respuesta.json.return_value = [
            {"body": "Para mí debería ser generador"},
            {"body": "APROBAR GENERADOR"},
        ]
        respuesta.raise_for_status.return_value = None
        get.return_value = respuesta

        cierre = Mock()
        cierre.raise_for_status.return_value = None
        patch_request.return_value = cierre

        decision = github_issues.leer_decision(
            "https://github.com/pase360/pase360-agente-captacion/issues/80"
        )

        self.assertEqual(decision, "generador")
        get.assert_called_once()
        patch_request.assert_called_once()
        self.assertEqual(patch_request.call_args.kwargs["json"], {"state": "closed"})

    @patch("agente.github_issues.requests.get")
    @patch("agente.github_issues._config", return_value=("token", "pase360/pase360-agente-captacion"))
    def test_no_interpreta_texto_libre_como_decision(self, config, get):
        respuesta = Mock()
        respuesta.json.return_value = [
            {"body": "Creo que tal vez conviene aprobar generador"}
        ]
        respuesta.raise_for_status.return_value = None
        get.return_value = respuesta

        decision = github_issues.leer_decision(
            "https://github.com/pase360/pase360-agente-captacion/issues/81"
        )

        self.assertEqual(decision, "")


if __name__ == "__main__":
    unittest.main()
