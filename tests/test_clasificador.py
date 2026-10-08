import unittest
from agente.clasificador import clasificar

class TestClasificador(unittest.TestCase):
    def test_generador(self):
        c = {"name":"Sindicato de Empleados","tags":{"office":"association"}}
        self.assertEqual(clasificar(c)[0], "generador")
    def test_capilla_no_es_generador(self):
        c = {"name":"Capilla Santa Teresita","tags":{"amenity":"place_of_worship"}}
        self.assertNotEqual(clasificar(c)[0], "generador")

    def test_fundacion_no_es_generador(self):
        c = {"name":"Fundación Mueve","tags":{"office":"foundation"}}
        self.assertNotEqual(clasificar(c)[0], "generador")

    def test_asociacion_generica_no_es_generador(self):
        c = {"name":"Asociación Empresaria Hotelera","tags":{"office":"association"}}
        self.assertNotEqual(clasificar(c)[0], "generador")

    def test_club_deportivo(self):
        c = {"name":"Club Universitario de Córdoba","tags":{"club":"sport","sport":"soccer"}}
        self.assertEqual(clasificar(c)[0], "generador")

    def test_comercio(self):
        c = {"name":"Panadería Córdoba","tags":{"shop":"bakery"}}
        self.assertEqual(clasificar(c)[0], "comercio")
    def test_exclusion(self):
        c = {"name":"Parking Centro","tags":{"amenity":"parking"}}
        self.assertEqual(clasificar(c)[0], "descartado")

    def test_parroquia_descartada(self):
        c = {"name":"Parroquia Nuestra Señora del Carmen","tags":{"amenity":"place_of_worship"}}
        self.assertEqual(clasificar(c)[0], "descartado")

    def test_consulado_descartado(self):
        c = {"name":"Consulado de Francia","tags":{"office":"diplomatic"}}
        self.assertEqual(clasificar(c)[0], "descartado")

    def test_instituto_secundario_descartado(self):
        c = {"name":"Instituto Privado Deán Funes","tags":{"amenity":"school"}}
        self.assertEqual(clasificar(c)[0], "descartado")

    def test_escuela_identificada_por_tag_descartada(self):
        c = {"name":"San Martín","tags":{"amenity":"school"}}
        self.assertEqual(clasificar(c)[0], "descartado")

    def test_colegio_profesional_sigue_como_generador(self):
        c = {"name":"Colegio de Abogados de Córdoba","tags":{"office":"association"}}
        self.assertEqual(clasificar(c)[0], "generador")

if __name__ == "__main__":
    unittest.main()
