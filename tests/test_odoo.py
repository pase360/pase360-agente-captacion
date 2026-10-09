import unittest
from unittest.mock import patch

from agente.odoo import Odoo
from agente import config as C


class TestBusquedaLeadPorEmpresa(unittest.TestCase):
    def test_busca_solo_en_pase360_o_sin_empresa(self):
        odoo = Odoo.__new__(Odoo)
        with patch.object(odoo, "call", return_value=[42]) as call:
            resultado = odoo.buscar_lead_email("contacto@ejemplo.com")

        self.assertEqual(resultado, 42)
        call.assert_called_once_with(
            "crm.lead",
            "search",
            [
                ["email_from", "=", "contacto@ejemplo.com"],
                ["company_id", "in", [False, C.ODOO_COMPANY_ID]],
            ],
            limit=1,
        )

    def test_devuelve_none_si_no_hay_lead_de_pase360(self):
        odoo = Odoo.__new__(Odoo)
        with patch.object(odoo, "call", return_value=[]) as call:
            resultado = odoo.buscar_lead_email("contacto@ejemplo.com")

        self.assertIsNone(resultado)
        call.assert_called_once()


if __name__ == "__main__":
    unittest.main()
