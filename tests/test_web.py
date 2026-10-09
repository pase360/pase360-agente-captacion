import unittest
from unittest.mock import patch
from agente import web

class TestWebQueries(unittest.TestCase):
    def test_email_domains_are_grouped(self):
        queries = web._consultas_base({'name': 'Comercio de Prueba'})
        self.assertIn('("@gmail.com" OR "@hotmail.com" OR "@outlook.com")', queries[2])


    def test_email_osm_registra_fuente_correcta(self):
        candidato = {'name': 'Comercio de Prueba', 'email': 'contacto@comercioprueba.com.ar'}
        resultado = web.completar(candidato)
        self.assertEqual(resultado['email_source'], 'osm')
        self.assertTrue(resultado['contactable'])

    def test_email_web_registra_fuente_correcta(self):
        candidato = {'name': 'Comercio de Prueba', 'website': 'https://comercioprueba.com.ar'}
        with patch.object(web, '_analizar_web', return_value=['contacto@comercioprueba.com.ar']):
            resultado = web.completar(candidato)
        self.assertEqual(resultado['email_source'], 'website')
        self.assertEqual(resultado['email'], 'contacto@comercioprueba.com.ar')

if __name__ == '__main__':
    unittest.main()
