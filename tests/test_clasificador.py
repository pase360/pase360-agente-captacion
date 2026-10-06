import unittest
from agente.clasificador import clasificar

class TestClasificador(unittest.TestCase):
    def test_generador(self):
        c = {"name":"Sindicato de Empleados","tags":{"office":"association"}}
        self.assertEqual(clasificar(c)[0], "generador")
    def test_comercio(self):
        c = {"name":"Panadería Córdoba","tags":{"shop":"bakery"}}
        self.assertEqual(clasificar(c)[0], "comercio")
    def test_exclusion(self):
        c = {"name":"Parking Centro","tags":{"amenity":"parking"}}
        self.assertEqual(clasificar(c)[0], "descartado")

if __name__ == "__main__":
    unittest.main()
