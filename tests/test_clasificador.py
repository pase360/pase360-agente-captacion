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

    def test_club_de_la_milanesa_es_comercio(self):
        self.assertEqual(
            clasificar({"name": "Club de la Milanesa"})[0],
            "comercio",
        )

    def test_sushiclub_es_comercio(self):
        self.assertEqual(
            clasificar({"name": "SushiClub"})[0],
            "comercio",
        )
    def test_exclusion(self):
        c = {"name":"Parking Centro","tags":{"amenity":"parking"}}
        self.assertEqual(clasificar(c)[0], "descartado")

    def test_estacionamiento_descartado_por_tag_aunque_nombre_sea_generico(self):
        c = {"name": "Centro", "tags": {"amenity": "parking"}}
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

    def test_nuevos_colegios_profesionales_son_generadores(self):
        nombres = [
            "Colegio de Agrimensores de Córdoba",
            "Colegio de Arquitectos de Córdoba",
            "Colegio de Biólogos de Córdoba",
            "Colegio de Escribanos de Córdoba",
            "Colegio de Farmacéuticos de Córdoba",
            "Colegio de Fonoaudiólogos de Córdoba",
            "Colegio de Ingenieros Civiles de Córdoba",
            "Colegio de Ingenieros Agrónomos de Córdoba",
            "Colegio de Ingenieros Especialistas de Córdoba",
            "Colegio de Ópticos de la Provincia de Córdoba",
            "Colegio de Traductores Públicos de la Provincia de Córdoba",
            "Consejo Profesional de Ciencias Económicas de Córdoba",
        ]
        for nombre in nombres:
            with self.subTest(nombre=nombre):
                self.assertEqual(clasificar({"name": nombre})[0], "generador")

if __name__ == "__main__":
    unittest.main()
