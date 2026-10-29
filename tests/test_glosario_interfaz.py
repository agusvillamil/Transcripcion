"""Control de activación sin micrófono, captura ni servidores de IA."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
import app


class PruebasInterfaz(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.qt = QApplication.instance() or QApplication([])

	def setUp(self):
		self.tmp = tempfile.TemporaryDirectory()
		self.addCleanup(self.tmp.cleanup)
		self.ruta = Path(self.tmp.name) / "datos.json"
		self.ruta.write_text(json.dumps({"datos": {"glosario": [{"en": "pain", "es": "dolor"}]}}))
		for parche in (patch.object(app.Ventana, "_preparar_servicios"), patch.object(app, "listar_fuentes", return_value=[]),
			patch.object(app, "monitor_predeterminado", return_value=None), patch.object(app.config, "GLOSARIO_RUTA", self.ruta)):
			parche.start()
			self.addCleanup(parche.stop)
		self.v = app.Ventana()
		self.addCleanup(self.v.close)
		self.v._servicios_listos("Prueba sin modelos")

	def test_opcional_y_reversible(self):
		self.assertIsNone(self.v.traductor.glosario)
		self.v.boton_glosario.setChecked(True)
		self.assertTrue(self.v.traductor.glosario.indice)
		self.v.boton_glosario.setChecked(False)
		self.assertIsNone(self.v.traductor.glosario)

	def test_bloqueado_mientras_hay_pendientes(self):
		with patch.object(self.v.sesion, "pendientes", return_value=1):
			self.v._actualizar_vumetro()
			self.assertFalse(self.v.boton_glosario.isEnabled())
			self.v.boton_glosario.setChecked(True)
			self.assertFalse(self.v.boton_glosario.isChecked())
			self.assertIsNone(self.v.traductor.glosario)

	def test_bloqueado_mientras_escucha(self):
		with patch.object(self.v, "_escuchando", return_value=True):
			self.v.boton_glosario.setChecked(True)
			self.assertIsNone(self.v.traductor.glosario)

	def test_archivo_roto_desactiva_con_motivo(self):
		self.v.boton_glosario.setChecked(True)
		self.ruta.write_text("{")
		self.v._cambiar_glosario(True)
		self.assertIsNone(self.v.traductor.glosario)
		self.assertFalse(self.v.boton_glosario.isChecked())
		self.assertIn("No se pudo cargar", self.v.boton_glosario.toolTip())


if __name__ == "__main__":
	unittest.main()
