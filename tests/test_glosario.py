import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import config
from glosario import Glosario, estimar_tokens
from traductor import Traductor, _SISTEMA, _PEDIDO


class PruebasGlosario(unittest.TestCase):
	def setUp(self):
		self.tmp = tempfile.TemporaryDirectory()
		self.addCleanup(self.tmp.cleanup)
		self.ruta = Path(self.tmp.name) / "datos.json"
		self.entradas = [
			{"en": "pain", "es": "dolor", "nota": "NO INCLUIR ESTA NOTA"},
			{"en": "chest pain", "es": "dolor de pecho / dolor torácico", "nota": "NO INCLUIR ESTA NOTA"},
			{"en": "medication / medicine / meds", "es": "medicamento / medicina"},
			{"en": "US", "es": "ultrasonido"},
			{"en": "IV", "es": "vía intravenosa"},
			{"en": "year", "es": "año"},
			{"en": "discharge (from hospital)", "es": "alta hospitalaria"},
		]

	def cargar(self, entradas=None):
		self.ruta.write_text(json.dumps({"datos": {"glosario": self.entradas if entradas is None else entradas}}))
		return Glosario.cargar(self.ruta)

	def test_frase_larga_prioritaria_sin_solapamiento(self):
		g = self.cargar()
		self.assertEqual([c.original for c in g.buscar("Chest pain and pain.", "en")], ["chest pain", "pain"])
		self.assertEqual(len(g.buscar("chest pain", "en")), 1)

	def test_variantes_explicitas_en_ambos_idiomas(self):
		g = self.cargar()
		self.assertEqual(g.buscar("my meds", "en")[0].equivalente, "medicamento / medicina")
		self.assertEqual(g.buscar("dolor torácico", "es")[0].equivalente, "chest pain")

	def test_no_subcadenas_ni_cruce_de_oraciones(self):
		g = self.cargar()
		self.assertEqual(g.buscar("painful painting", "en"), [])
		self.assertNotIn("chest pain", [c.original for c in g.buscar("chest. Pain", "en")])

	def test_tildes_y_siglas_no_se_confunden(self):
		g = self.cargar()
		self.assertEqual(g.buscar("help us", "en"), [])
		self.assertEqual(g.buscar("US and IV", "en")[0].original, "US")
		self.assertEqual(g.buscar("ano", "es"), [])
		self.assertTrue(g.buscar("año", "es"))

	def test_no_eliminar_calificadores_ambiguos(self):
		self.assertEqual(self.cargar().buscar("discharge from the eye", "en"), [])

	def test_alias_conflictivos_excluidos(self):
		g = self.cargar([{"en": "lead", "es": "plomo"}, {"en": "lead", "es": "dirigir"}])
		self.assertEqual(g.buscar("lead", "en"), [])

	def test_archivo_ausente_corrupto_y_esquemas_invalidos(self):
		self.assertTrue(Glosario.cargar(self.ruta).error)
		for valor in ["{", "null", "[]", '{"datos":{"glosario":{}}}', "\xff"]:
			with self.subTest(valor=valor):
				self.ruta.write_bytes(valor.encode("latin1"))
				g = Glosario.cargar(self.ruta)
				self.assertTrue(g.error)
				self.assertEqual(g.buscar("pain", "en"), [])

	def test_entradas_invalidas_no_afectan_validas(self):
		g = self.cargar([None, {}, {"en": 4, "es": "x"}, {"en": "", "es": "x"},
			{"en": "bad\nterm", "es": "x"}, self.entradas[0]])
		self.assertEqual(g.cantidad, 1)
		self.assertTrue(g.buscar("pain", "en"))

	def test_lectura_solo_al_recargar(self):
		g = self.cargar()
		antes = self.ruta.read_bytes()
		g.buscar("pain", "en")
		self.assertEqual(self.ruta.read_bytes(), antes)
		self.ruta.unlink()
		self.assertTrue(g.buscar("pain", "en"))
		self.assertFalse(Glosario.cargar(self.ruta).indice)

	def test_limite_entradas_tokens_y_contexto(self):
		g = self.cargar()
		texto = "chest pain medicine US IV"
		with patch.object(config, "GLOSARIO_MAX_ENTRADAS", 1):
			b = g.referencia(texto, "en", _SISTEMA)
			self.assertEqual(b.count("\n["), 1)
			self.assertLessEqual(estimar_tokens(b), config.GLOSARIO_MAX_TOKENS)
		self.assertEqual(g.referencia(texto, "en", "x" * 5000), "")
		with patch.object(config, "GLOSARIO_MAX_TOKENS", 2):
			self.assertEqual(g.referencia(texto, "en", ""), "")
		with patch.object(config, "GLOSARIO_MAX_ENTRADAS", 0):
			self.assertEqual(g.referencia(texto, "en", ""), "")

	def test_sin_notas_ni_datos_personales(self):
		b = self.cargar().referencia("chest pain", "en", _SISTEMA)
		self.assertIn('"dolor de pecho / dolor torácico"', b)
		self.assertNotIn("NO INCLUIR", b)

	def test_pedido_actual_intacto_sin_coincidencias_o_desactivado(self):
		base, nuevo = Traductor(), Traductor(glosario=self.cargar())
		for texto in ["Good morning.", "Please repeat that.", "a" * 5000]:
			self.assertEqual(base._mensajes(texto, "en", "es", ["(EN) Hello"]), nuevo._mensajes(texto, "en", "es", ["(EN) Hello"]))
		nuevo.glosario = None
		self.assertEqual(base._mensajes("pain", "en", "es", []), nuevo._mensajes("pain", "en", "es", []))

	def test_reglas_contexto_y_texto_original_intactos(self):
		base, nuevo = Traductor(), Traductor(glosario=self.cargar())
		a = base._mensajes("chest pain", "en", "es", ["(EN) Previous"])
		b = nuevo._mensajes("chest pain", "en", "es", ["(EN) Previous"])
		self.assertEqual(a[1], b[1])
		self.assertTrue(b[0]["content"].startswith(a[0]["content"]))
		self.assertGreater(len(b[0]["content"]), len(a[0]["content"]))

	def test_no_imponer_sentidos_de_palabras_aisladas(self):
		g = self.cargar([{"en": "Bottom", "es": "trasero"}, {"en": "Hold", "es": "retener"},
			{"en": "doctor / physician", "es": "médico/a"}])
		for texto in ["Sign at the bottom.", "Hold up on signing.", "The doctor will see you."]:
			self.assertEqual(g.referencia(texto, "en", _SISTEMA), "")

	def test_translategemma_conserva_formato(self):
		self.assertEqual(Traductor("translategemma:4b")._mensajes("pain", "en", "es", []),
			Traductor("translategemma:4b", glosario=self.cargar())._mensajes("pain", "en", "es", []))


if __name__ == "__main__":
	unittest.main()
