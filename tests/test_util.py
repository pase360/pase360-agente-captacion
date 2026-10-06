import unittest
from agente.util import normalizar_email, dominio, normalizar_texto

class TestUtil(unittest.TestCase):
    def test_email(self):
        self.assertEqual(normalizar_email(" TEST@Example.COM "), "test@example.com")
        self.assertEqual(normalizar_email("no-es-email"), "")
    def test_domain(self):
        self.assertEqual(dominio("a@b.com"), "b.com")
    def test_text(self):
        self.assertEqual(normalizar_texto("  Cámara  de Comercio "), "camara de comercio")

if __name__ == "__main__":
    unittest.main()
