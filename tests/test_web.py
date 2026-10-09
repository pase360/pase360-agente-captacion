import unittest
from agente import web

class TestWebQueries(unittest.TestCase):
    def test_email_domains_are_grouped(self):
        queries = web._consultas_base({'name': 'Comercio de Prueba'})
        self.assertIn('("@gmail.com" OR "@hotmail.com" OR "@outlook.com")', queries[2])

if __name__ == '__main__':
    unittest.main()
