"""Asistente de interpretación consecutiva EN⇄ES.

Escucha el audio del sistema (la llamada), transcribe cada frase con Whisper
y la traduce con un modelo local de Ollama. Ejecutar: python3 app.py
"""
import html
import re
import sys
import threading
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
	QApplication, QButtonGroup, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
	QMainWindow, QProgressBar, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

import config
from asr import ServidorWhisper
from captura import CapturaAudio, listar_fuentes, monitor_predeterminado
from segmentador import Segmentador
from sesion import Callbacks, Linea, Sesion
from traductor import Traductor

C = {
	"fondo": "#0E1116", "panel": "#161B22", "tarjeta": "#1B222C", "borde": "#2A3441",
	"texto": "#E6EDF3", "tenue": "#8B98A5", "numero": "#FFD166", "error": "#F85149",
	"en": "#58A6FF",  # EN → ES
	"es": "#3FB950",  # ES → EN
}
DIRECCION = {"en": "EN → ES", "es": "ES → EN"}
FUENTE_BASE_PX = 17

ESTILO = f"""
QMainWindow, QWidget#raiz, QWidget#feed {{ background: {C['fondo']}; }}
QWidget {{ color: {C['texto']}; font-family: 'Noto Sans'; font-size: 14px; }}
QFrame#barra {{ background: {C['panel']}; border-bottom: 1px solid {C['borde']}; }}
QComboBox {{ background: {C['tarjeta']}; border: 1px solid {C['borde']}; border-radius: 6px; padding: 5px 10px; }}
QComboBox QAbstractItemView {{ background: {C['tarjeta']}; selection-background-color: {C['borde']}; }}
QPushButton {{ background: {C['tarjeta']}; border: 1px solid {C['borde']}; border-radius: 6px; padding: 6px 12px; }}
QPushButton:hover {{ border-color: {C['tenue']}; }}
QPushButton:checked {{ background: {C['borde']}; border-color: {C['tenue']}; }}
QPushButton#iniciar {{ background: {C['es']}; color: {C['fondo']}; font-weight: 700; font-size: 15px;
	padding: 8px 22px; border: none; }}
QPushButton#iniciar[activo="true"] {{ background: {C['error']}; color: white; }}
QPushButton#iniciar:disabled {{ background: {C['borde']}; color: {C['tenue']}; }}
QPushButton#mini {{ padding: 3px 9px; font-size: 12px; color: {C['tenue']}; }}
QScrollArea {{ border: none; background: {C['fondo']}; }}
QScrollBar:vertical {{ background: {C['fondo']}; width: 10px; }}
QScrollBar::handle:vertical {{ background: {C['borde']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QProgressBar {{ background: {C['tarjeta']}; border: none; border-radius: 3px; }}
QProgressBar::chunk {{ background: {C['es']}; border-radius: 3px; }}
QLabel#tenue {{ color: {C['tenue']}; font-size: 12px; }}
QLabel#error {{ color: {C['error']}; }}
"""

# Números, dosis y unidades: lo más delicado de interpretar.
_NUM = (
	r"(?:\d+(?:[.,:/]\d+)*|(?:zero|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
	r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|"
	r"ninety|hundred|thousand|cero|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|"
	r"quince|dieciséis|diecisiete|dieciocho|diecinueve|veinte|treinta|cuarenta|cincuenta|sesenta|setenta|"
	r"ochenta|noventa|cien|ciento|cientos|doscientos|trescientos|cuatrocientos|quinientos|mil)\b)"
)
_UNIDAD = (
	r"(?:mg|mcg|µg|g|kg|ml|mL|cc|l|lb|lbs|%|milligrams?|miligramos?|grams?|gramos?|milliliters?|mililitros?|"
	r"units?|unidades?|tablets?|pills?|pastillas?|tabletas?|hours?|horas?|days?|días?|weeks?|semanas?|"
	r"months?|meses|mes|years?|años?|minutes?|minutos?|times?|veces|a\.m\.|p\.m\.|am|pm)"
)
_RE_NUMERO = re.compile(rf"\b{_NUM}(?:[\s-]+{_NUM})*(?:\s*{_UNIDAD}(?!\w))?", re.I)


def resaltar(texto: str) -> str:
	"""Texto → HTML con números y unidades resaltados."""
	partes, fin = [], 0
	for m in _RE_NUMERO.finditer(texto):
		partes.append(html.escape(texto[fin:m.start()]))
		partes.append(f'<span style="color:{C["numero"]};font-weight:700">{html.escape(m.group())}</span>')
		fin = m.end()
	partes.append(html.escape(texto[fin:]))
	return "".join(partes)


class Tarjeta(QFrame):
	"""Un turno de un hablante: texto original arriba, traducción abajo."""

	forzar = Signal(int, str)

	def __init__(self, tarjeta_id: int, origen: str, escala: float) -> None:
		super().__init__()
		self.setObjectName("tarjeta")
		self.id = tarjeta_id
		self.origen = origen
		self.escala = escala
		self.lineas: dict[int, list[str]] = {}  # id de línea -> [original, traducción]
		self.traduciendo: set[int] = set()

		self.badge = QLabel()
		self.hora = QLabel(datetime.now().strftime("%H:%M:%S"))
		self.hora.setObjectName("tenue")
		self.tiempos = QLabel()
		self.tiempos.setObjectName("tenue")
		self.boton_idioma = QPushButton()
		self.boton_idioma.setObjectName("mini")
		self.boton_idioma.setCursor(Qt.PointingHandCursor)
		self.boton_idioma.clicked.connect(lambda: self.forzar.emit(self.id, "es" if self.origen == "en" else "en"))
		boton_copiar = QPushButton("Copiar")
		boton_copiar.setObjectName("mini")
		boton_copiar.setCursor(Qt.PointingHandCursor)
		boton_copiar.clicked.connect(self._copiar)

		cabecera = QHBoxLayout()
		cabecera.addWidget(self.badge)
		cabecera.addWidget(self.hora)
		cabecera.addWidget(self.tiempos)
		cabecera.addStretch()
		cabecera.addWidget(self.boton_idioma)
		cabecera.addWidget(boton_copiar)

		self.original = QLabel()
		self.traduccion = QLabel()
		for etiqueta in (self.original, self.traduccion):
			etiqueta.setWordWrap(True)
			etiqueta.setTextFormat(Qt.RichText)
			etiqueta.setTextInteractionFlags(Qt.TextSelectableByMouse)

		capa = QVBoxLayout(self)
		capa.setContentsMargins(18, 12, 18, 14)
		capa.setSpacing(8)
		capa.addLayout(cabecera)
		capa.addWidget(self.original)
		capa.addWidget(self.traduccion)
		self.set_origen(origen)

	def set_origen(self, origen: str) -> None:
		self.origen = origen
		color = C[origen]
		self.setStyleSheet(
			f"QFrame#tarjeta {{ background: {C['tarjeta']}; border: 1px solid {C['borde']};"
			f" border-left: 5px solid {color}; border-radius: 10px; }}"
		)
		self.badge.setText(DIRECCION[origen])
		self.badge.setStyleSheet(
			f"background: {color}; color: {C['fondo']}; font-weight: 700; font-size: 12px;"
			" border-radius: 4px; padding: 2px 8px;"
		)
		self.boton_idioma.setText("⇄ Es español" if origen == "en" else "⇄ Es inglés")
		self._render()

	def poner_linea(self, linea_id: int, original: str, traduccion: str, traduciendo: bool) -> None:
		self.lineas[linea_id] = [original, traduccion]
		if traduciendo:
			self.traduciendo.add(linea_id)
		else:
			self.traduciendo.discard(linea_id)
		self._render()

	def agregar_token(self, linea_id: int, token: str) -> None:
		if linea_id in self.lineas:
			self.lineas[linea_id][1] += token
			self._render()

	def aplicar_escala(self, escala: float) -> None:
		self.escala = escala
		self._render()

	def texto_plano(self) -> tuple[str, str]:
		orden = sorted(self.lineas)
		return (
			" ".join(self.lineas[i][0] for i in orden).strip(),
			" ".join(self.lineas[i][1].strip() for i in orden).strip(),
		)

	def _render(self) -> None:
		original, traduccion = self.texto_plano()
		px = FUENTE_BASE_PX * self.escala
		self.original.setStyleSheet(f"color: {C['tenue']}; font-size: {px:.0f}px;")
		self.traduccion.setStyleSheet(f"color: {C['texto']}; font-size: {px * 1.4:.0f}px; font-weight: 600;")
		self.original.setText(resaltar(original))
		cursor = f' <span style="color:{C[self.origen]}">▍</span>' if self.traduciendo else ""
		self.traduccion.setText(resaltar(traduccion) + cursor)

	def _copiar(self) -> None:
		QGuiApplication.clipboard().setText(self.texto_plano()[1])


class Puente(QObject):
	"""Pasa los eventos de los hilos de trabajo al hilo de la interfaz."""

	linea_nueva = Signal(object)
	token = Signal(object, str)
	linea_traducida = Signal(object)
	linea_actualizada = Signal(object)
	estado = Signal(str)
	error = Signal(str)
	modelos_llm = Signal(list)
	servicios = Signal(str)


class Ventana(QMainWindow):
	def __init__(self) -> None:
		super().__init__()
		self.setWindowTitle("Intérprete EN ⇄ ES")
		self.resize(1200, 820)
		self.escala = 1.0
		self.filtro = "todo"
		self.tarjetas: dict[int, Tarjeta] = {}
		self.captura: CapturaAudio | None = None
		self.segmentador: Segmentador | None = None
		self.asr = ServidorWhisper()
		self.traductor = Traductor()
		self.listo = False
		self._seguir_final = True
		self._cargando = threading.Lock()

		self.puente = Puente()
		self.puente.linea_nueva.connect(self._linea_nueva)
		self.puente.token.connect(lambda linea, t: self._tarjeta(linea).agregar_token(linea.id, t))
		self.puente.linea_traducida.connect(self._linea_traducida)
		self.puente.linea_actualizada.connect(self._linea_actualizada)
		self.puente.estado.connect(self._estado)
		self.puente.error.connect(self._error)
		self.puente.modelos_llm.connect(self._llenar_llm)
		self.puente.servicios.connect(self._servicios_listos)
		self.sesion = Sesion(self.asr, self.traductor, Callbacks(
			linea_nueva=self.puente.linea_nueva.emit,
			token=self.puente.token.emit,
			linea_traducida=self.puente.linea_traducida.emit,
			linea_actualizada=self.puente.linea_actualizada.emit,
			estado=self.puente.estado.emit,
			error=self.puente.error.emit,
		))

		raiz = QWidget(objectName="raiz")
		capa = QVBoxLayout(raiz)
		capa.setContentsMargins(0, 0, 0, 0)
		capa.setSpacing(0)
		capa.addWidget(self._construir_barra())
		capa.addWidget(self._construir_filtros())
		capa.addWidget(self._construir_feed(), 1)
		capa.addWidget(self._construir_estado())
		self.setCentralWidget(raiz)
		self.setStyleSheet(ESTILO)

		for tecla, accion in (
			("F9", self._alternar), ("Ctrl+L", self._limpiar), ("Ctrl+S", self._guardar),
			("Ctrl++", lambda: self._zoom(0.1)), ("Ctrl+=", lambda: self._zoom(0.1)), ("Ctrl+-", lambda: self._zoom(-0.1)),
		):
			QShortcut(QKeySequence(tecla), self).activated.connect(accion)

		self.vumetro_timer = QTimer(self, interval=60, timeout=self._actualizar_vumetro)
		self.vumetro_timer.start()
		threading.Thread(target=self._preparar_servicios, daemon=True).start()

	# --- construcción ---

	def _construir_barra(self) -> QFrame:
		barra = QFrame(objectName="barra")
		capa = QHBoxLayout(barra)
		capa.setContentsMargins(16, 12, 16, 12)
		capa.setSpacing(10)

		self.boton = QPushButton("Cargando modelos…", objectName="iniciar")
		self.boton.setEnabled(False)
		self.boton.setCursor(Qt.PointingHandCursor)
		self.boton.clicked.connect(self._alternar)
		capa.addWidget(self.boton)

		self.vumetro = QProgressBar(maximum=100, textVisible=False)
		self.vumetro.setFixedSize(90, 8)
		capa.addWidget(self.vumetro)
		self.indicador_voz = QLabel("")
		self.indicador_voz.setObjectName("tenue")
		self.indicador_voz.setFixedWidth(52)
		capa.addWidget(self.indicador_voz)

		capa.addWidget(self._etiqueta("Audio"))
		self.combo_fuente = QComboBox()
		self.combo_fuente.setMinimumWidth(240)
		predeterminado = monitor_predeterminado()
		for f in listar_fuentes():
			tipo = "Salida del sistema" if f.es_monitor else "Micrófono"
			self.combo_fuente.addItem(f"{tipo}: {f.descripcion.removeprefix('Monitor of ')}", f.nombre)
			if f.nombre == predeterminado:
				self.combo_fuente.setCurrentIndex(self.combo_fuente.count() - 1)
		capa.addWidget(self.combo_fuente)

		capa.addWidget(self._etiqueta("Whisper"))
		self.combo_whisper = QComboBox()
		for ruta in sorted(config.WHISPER_MODELOS_DIR.glob("ggml-*.bin")):
			if not ruta.name.startswith("for-tests") and ".en" not in ruta.name and "silero" not in ruta.name:
				self.combo_whisper.addItem(ruta.name.removeprefix("ggml-").removesuffix(".bin"), ruta.name)
		self.combo_whisper.setCurrentIndex(max(0, self.combo_whisper.findData(config.WHISPER_MODELO)))
		self.combo_whisper.currentIndexChanged.connect(self._cambiar_whisper)
		capa.addWidget(self.combo_whisper)

		capa.addWidget(self._etiqueta("Traducción"))
		self.combo_llm = QComboBox()
		self.combo_llm.addItem(config.OLLAMA_MODELO, config.OLLAMA_MODELO)
		self.combo_llm.currentIndexChanged.connect(self._cambiar_llm)
		capa.addWidget(self.combo_llm)
		capa.addStretch()
		return barra

	def _construir_filtros(self) -> QWidget:
		fila = QWidget()
		capa = QHBoxLayout(fila)
		capa.setContentsMargins(16, 10, 16, 4)
		grupo = QButtonGroup(self)
		for clave, texto in (("todo", "Todo"), ("en", "EN → ES"), ("es", "ES → EN")):
			b = QPushButton(texto, checkable=True, checked=clave == "todo")
			b.setCursor(Qt.PointingHandCursor)
			b.clicked.connect(lambda _=False, c=clave: self._filtrar(c))
			grupo.addButton(b)
			capa.addWidget(b)
		capa.addStretch()
		for texto, accion in (("A−", lambda: self._zoom(-0.1)), ("A+", lambda: self._zoom(0.1)),
							  ("Guardar sesión", self._guardar), ("Limpiar", self._limpiar)):
			b = QPushButton(texto)
			b.setCursor(Qt.PointingHandCursor)
			b.clicked.connect(accion)
			capa.addWidget(b)
		return fila

	def _construir_feed(self) -> QScrollArea:
		self.scroll = QScrollArea(widgetResizable=True)
		self.feed = QWidget(objectName="feed")
		self.capa_feed = QVBoxLayout(self.feed)
		self.capa_feed.setContentsMargins(16, 8, 16, 16)
		self.capa_feed.setSpacing(12)
		self.vacio = QLabel(
			"Presioná <b>Iniciar</b> (F9) y reproducí la llamada.<br><br>"
			f'<span style="color:{C["en"]}">■</span> Lo que se diga en inglés se traduce al español.<br>'
			f'<span style="color:{C["es"]}">■</span> Lo que se diga en español se traduce al inglés.<br><br>'
			"Si una frase se detecta en el idioma equivocado, usá «⇄» en su tarjeta."
		)
		self.vacio.setAlignment(Qt.AlignCenter)
		self.vacio.setStyleSheet(f"color: {C['tenue']}; font-size: 16px; padding: 60px;")
		self.capa_feed.addWidget(self.vacio)
		self.capa_feed.addStretch()
		self.scroll.setWidget(self.feed)
		barra = self.scroll.verticalScrollBar()
		barra.valueChanged.connect(lambda v: setattr(self, "_seguir_final", v >= barra.maximum() - 40))
		barra.rangeChanged.connect(lambda _a, maximo: self._seguir_final and barra.setValue(maximo))
		return self.scroll

	def _construir_estado(self) -> QFrame:
		marco = QFrame(objectName="barra")
		capa = QHBoxLayout(marco)
		capa.setContentsMargins(16, 6, 16, 6)
		self.etiqueta_estado = QLabel("Iniciando servicios…")
		self.etiqueta_estado.setObjectName("tenue")
		self.etiqueta_servicios = QLabel("")
		self.etiqueta_servicios.setObjectName("tenue")
		capa.addWidget(self.etiqueta_estado, 1)
		capa.addWidget(self.etiqueta_servicios)
		return marco

	def _etiqueta(self, texto: str) -> QLabel:
		etiqueta = QLabel(texto)
		etiqueta.setObjectName("tenue")
		return etiqueta

	# --- servicios (Whisper y Ollama) ---

	def _preparar_servicios(self) -> None:
		with self._cargando:
			try:
				self.puente.estado.emit("Iniciando Ollama…")
				self.traductor.asegurar_servidor()
				self.puente.modelos_llm.emit(self.traductor.modelos())
				self.puente.estado.emit("Cargando Whisper en la GPU…")
				self.asr.iniciar()
				self.puente.estado.emit(f"Cargando {self.traductor.modelo} en la GPU…")
				self.traductor.precargar()
				self.puente.servicios.emit(self._resumen_servicios())
			except Exception as e:
				self.puente.error.emit(f"No se pudieron iniciar los servicios: {e}")

	def _resumen_servicios(self) -> str:
		gpu_w = {True: "GPU", False: "CPU", None: "?"}[self.asr.usa_gpu]
		fraccion = self.traductor.en_gpu()
		gpu_t = "?" if fraccion is None else f"{fraccion:.0%} GPU"
		return f"Whisper {self.asr.modelo.removeprefix('ggml-').removesuffix('.bin')} · {gpu_w}   |   " \
			   f"{self.traductor.modelo} · {gpu_t}"

	def _servicios_listos(self, resumen: str) -> None:
		self.listo = True
		self.etiqueta_servicios.setText(resumen)
		self.boton.setEnabled(True)
		self._actualizar_boton()
		self._estado("Listo." if not self._escuchando() else "Escuchando…")

	def _llenar_llm(self, modelos: list[str]) -> None:
		self.combo_llm.blockSignals(True)
		self.combo_llm.clear()
		for m in modelos:
			self.combo_llm.addItem(m, m)
		indice = self.combo_llm.findData(self.traductor.modelo)
		if indice < 0:
			self.combo_llm.addItem(self.traductor.modelo, self.traductor.modelo)
			indice = self.combo_llm.count() - 1
		self.combo_llm.setCurrentIndex(indice)
		self.combo_llm.blockSignals(False)

	def _cambiar_whisper(self) -> None:
		modelo = self.combo_whisper.currentData()
		self._recargar(lambda: self._reiniciar_whisper(modelo))

	def _reiniciar_whisper(self, modelo: str) -> None:
		self.asr.detener()
		self.asr.modelo = modelo
		self.puente.estado.emit(f"Cargando Whisper {modelo}…")
		self.asr.iniciar()

	def _cambiar_llm(self) -> None:
		modelo = self.combo_llm.currentData()
		self._recargar(lambda: self._reiniciar_llm(modelo))

	def _reiniciar_llm(self, modelo: str) -> None:
		self.traductor.liberar()
		self.traductor.modelo = modelo
		self.puente.estado.emit(f"Cargando {modelo} en la GPU…")
		self.traductor.precargar()

	def _recargar(self, tarea) -> None:
		self.listo = False
		self.boton.setEnabled(self._escuchando())

		def correr() -> None:
			with self._cargando:
				try:
					tarea()
					self.puente.servicios.emit(self._resumen_servicios())
				except Exception as e:
					self.puente.error.emit(str(e))

		threading.Thread(target=correr, daemon=True).start()

	# --- captura ---

	def _escuchando(self) -> bool:
		return self.captura is not None and self.captura.activa()

	def _alternar(self) -> None:
		if self._escuchando():
			self.captura.detener()
			for f in self.segmentador.vaciar():
				self.sesion.agregar(f)
			self.captura = None
			self._estado("Detenido.")
		elif self.listo:
			fuente = self.combo_fuente.currentData()
			self.segmentador = Segmentador()
			self.captura = CapturaAudio(fuente, self._al_bloque)
			self.captura.iniciar()
			self._estado("Escuchando…")
		self._actualizar_boton()

	def _al_bloque(self, bloque) -> None:
		# Hilo de captura: segmentar es barato; Whisper corre en el hilo de la sesión.
		for fragmento in self.segmentador.procesar(bloque):
			self.sesion.agregar(fragmento)

	def _actualizar_boton(self) -> None:
		activo = self._escuchando()
		self.boton.setText("■  Detener (F9)" if activo else "▶  Iniciar (F9)")
		self.boton.setProperty("activo", "true" if activo else "false")
		self.boton.style().unpolish(self.boton)
		self.boton.style().polish(self.boton)
		self.combo_fuente.setEnabled(not activo)
		self.combo_whisper.setEnabled(not activo)  # reiniciar Whisper cortaría la transcripción

	def _actualizar_vumetro(self) -> None:
		if not self._escuchando():
			self.vumetro.setValue(0)
			self.indicador_voz.setText("")
			return
		db = self.segmentador.nivel_db
		self.vumetro.setValue(int(max(0, min(100, (db + 60) * 100 / 60))))
		self.indicador_voz.setText("● voz" if self.segmentador.en_voz else "")
		self.indicador_voz.setStyleSheet(f"color: {C['error']}; font-size: 12px;")

	# --- eventos de la sesión ---

	def _tarjeta(self, linea: Linea) -> Tarjeta:
		if linea.tarjeta not in self.tarjetas:
			self.vacio.hide()
			tarjeta = Tarjeta(linea.tarjeta, linea.origen, self.escala)
			tarjeta.forzar.connect(self.sesion.forzar_idioma)
			tarjeta.setVisible(self.filtro in ("todo", linea.origen))
			self.capa_feed.insertWidget(self.capa_feed.count() - 1, tarjeta)
			self.tarjetas[linea.tarjeta] = tarjeta
		return self.tarjetas[linea.tarjeta]

	def _linea_nueva(self, linea: Linea) -> None:
		self._tarjeta(linea).poner_linea(linea.id, linea.original, "", traduciendo=True)

	def _linea_traducida(self, linea: Linea) -> None:
		tarjeta = self._tarjeta(linea)
		tarjeta.poner_linea(linea.id, linea.original, linea.traduccion, traduciendo=False)
		tarjeta.tiempos.setText(f"· Whisper {linea.t_asr:.1f}s · traducción {linea.t_traduccion:.1f}s")

	def _linea_actualizada(self, linea: Linea) -> None:
		tarjeta = self._tarjeta(linea)
		tarjeta.set_origen(linea.origen)
		tarjeta.setVisible(self.filtro in ("todo", linea.origen))
		tarjeta.poner_linea(linea.id, linea.original, "", traduciendo=True)

	def _estado(self, texto: str) -> None:
		self.etiqueta_estado.setStyleSheet("")
		self.etiqueta_estado.setObjectName("tenue")
		self.etiqueta_estado.setText(texto)

	def _error(self, texto: str) -> None:
		self.etiqueta_estado.setStyleSheet(f"color: {C['error']}; font-size: 12px;")
		self.etiqueta_estado.setText(texto)

	# --- acciones ---

	def _filtrar(self, clave: str) -> None:
		self.filtro = clave
		for t in self.tarjetas.values():
			t.setVisible(clave in ("todo", t.origen))

	def _zoom(self, delta: float) -> None:
		self.escala = max(0.7, min(2.2, self.escala + delta))
		for t in self.tarjetas.values():
			t.aplicar_escala(self.escala)

	def _limpiar(self) -> None:
		for t in self.tarjetas.values():
			t.deleteLater()
		self.tarjetas.clear()
		self.sesion.limpiar()
		self.vacio.show()

	def _guardar(self) -> None:
		if not self.tarjetas:
			return
		sugerido = Path.home() / f"interpretacion-{datetime.now():%Y%m%d-%H%M}.md"
		ruta, _ = QFileDialog.getSaveFileName(self, "Guardar sesión", str(sugerido), "Markdown (*.md)")
		if not ruta:
			return
		lineas = [f"# Sesión de interpretación {datetime.now():%d/%m/%Y %H:%M}", ""]
		for t in self.tarjetas.values():
			original, traduccion = t.texto_plano()
			lineas += [f"### {t.hora.text()} · {DIRECCION[t.origen]}", f"> {original}", "", traduccion, ""]
		Path(ruta).write_text("\n".join(lineas), encoding="utf-8")
		self._estado(f"Sesión guardada en {ruta}")

	def closeEvent(self, evento) -> None:
		if self.captura:
			self.captura.detener()
		self.sesion.cerrar()
		self.asr.detener()
		self.traductor.detener()
		super().closeEvent(evento)


def main() -> None:
	app = QApplication(sys.argv)
	app.setApplicationName("Intérprete EN⇄ES")
	ventana = Ventana()
	ventana.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
