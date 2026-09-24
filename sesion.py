"""Orquesta fragmento de audio → transcripción → traducción.

Dos hilos: uno transcribe (Whisper) y otro traduce (Ollama), así el texto
original aparece apenas termina Whisper, sin esperar a la traducción.
Whisper y el LLM se turnan la GPU: en la RX 570 correr ambos a la vez hace
que cada uno tarde 4-6 veces más.
Los callbacks se llaman desde esos hilos; la interfaz debe reenviarlos a su
propio hilo.
"""
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from asr import ServidorWhisper, es_ambiguo
from segmentador import Fragmento
from traductor import Traductor

CONTEXTO_LINEAS = 4


@dataclass
class Linea:
	id: int
	tarjeta: int     # líneas del mismo turno e idioma comparten tarjeta
	origen: str      # "en" o "es"
	original: str
	inicio: float
	fin: float
	audio: np.ndarray = field(repr=False)
	traduccion: str = ""
	t_asr: float = 0.0
	t_primer_token: float = 0.0
	t_traduccion: float = 0.0
	t_fin_habla: float = 0.0  # reloj de pared cuando terminó la voz (para latencia total)
	t_listo: float = 0.0

	@property
	def destino(self) -> str:
		return "es" if self.origen == "en" else "en"


@dataclass
class Callbacks:
	linea_nueva: Callable[[Linea], None] = lambda linea: None
	token: Callable[[Linea, str], None] = lambda linea, token: None
	linea_traducida: Callable[[Linea], None] = lambda linea: None
	linea_actualizada: Callable[[Linea], None] = lambda linea: None  # tras forzar idioma
	estado: Callable[[str], None] = lambda texto: None
	error: Callable[[str], None] = lambda texto: None


class Sesion:
	def __init__(self, asr: ServidorWhisper, traductor: Traductor, callbacks: Callbacks) -> None:
		self.asr = asr
		self.traductor = traductor
		self.cb = callbacks
		self.lineas: list[Linea] = []
		self._cola_asr: queue.Queue = queue.Queue()
		self._cola_trad: queue.Queue = queue.Queue()
		self._candado = threading.Lock()
		self._gpu = threading.Lock()
		self._tarjeta = 0
		self._ultimo_turno: int | None = None
		self._activa = True
		self._hilos = [
			threading.Thread(target=self._bucle_asr, daemon=True),
			threading.Thread(target=self._bucle_traduccion, daemon=True),
		]
		for h in self._hilos:
			h.start()

	def agregar(self, fragmento: Fragmento, t_fin_habla: float | None = None) -> None:
		self._cola_asr.put(("nuevo", fragmento, t_fin_habla or time.time()))

	def forzar_idioma(self, tarjeta: int, idioma: str) -> None:
		"""Re-transcribe y re-traduce todas las líneas de una tarjeta en `idioma`."""
		self._cola_asr.put(("forzar", tarjeta, idioma))

	def pendientes(self) -> int:
		return self._cola_asr.unfinished_tasks + self._cola_trad.unfinished_tasks

	def esperar(self) -> None:
		self._cola_asr.join()
		self._cola_trad.join()

	def cerrar(self) -> None:
		self._activa = False
		self._cola_asr.put(None)
		self._cola_trad.put(None)

	def limpiar(self) -> None:
		with self._candado:
			self.lineas.clear()
			self._ultimo_turno = None

	# --- hilos ---

	def _bucle_asr(self) -> None:
		while self._activa:
			trabajo = self._cola_asr.get()
			try:
				if trabajo is None:
					return
				if trabajo[0] == "nuevo":
					self._transcribir(trabajo[1], trabajo[2])
				else:
					self._forzar(trabajo[1], trabajo[2])
			except Exception as e:  # la sesión sigue aunque falle un fragmento
				self.cb.error(f"Transcripción: {e}")
			finally:
				self._cola_asr.task_done()

	def _bucle_traduccion(self) -> None:
		while self._activa:
			linea = self._cola_trad.get()
			try:
				if linea is None:
					return
				self._traducir(linea)
			except Exception as e:
				self.cb.error(f"Traducción: {e}")
			finally:
				self._cola_trad.task_done()

	def _transcribir(self, fragmento: Fragmento, t_fin_habla: float) -> None:
		self.cb.estado("Transcribiendo…")
		with self._gpu:
			tr = self.asr.transcribir(fragmento.audio)
		if not tr.texto:
			self.cb.estado("Escuchando…")
			return
		with self._candado:
			anterior = self.lineas[-1] if self.lineas else None
			mismo_turno = anterior is not None and fragmento.turno == self._ultimo_turno
			idioma = tr.idioma
			if es_ambiguo(tr.texto) and anterior:
				# "No", "OK": en consecutiva, un turno nuevo suele ser del otro hablante.
				idioma = anterior.origen if mismo_turno else anterior.destino
			if not (mismo_turno and anterior.origen == idioma):
				self._tarjeta += 1
			self._ultimo_turno = fragmento.turno
			linea = Linea(
				id=len(self.lineas),
				tarjeta=self._tarjeta,
				origen=idioma,
				original=tr.texto,
				inicio=fragmento.inicio,
				fin=fragmento.fin,
				audio=fragmento.audio,
				t_asr=tr.segundos,
				t_fin_habla=t_fin_habla,
			)
			self.lineas.append(linea)
		self.cb.linea_nueva(linea)
		self._cola_trad.put(linea)

	def _forzar(self, tarjeta: int, idioma: str) -> None:
		with self._candado:
			lineas = [l for l in self.lineas if l.tarjeta == tarjeta]
		for linea in lineas:
			self.cb.estado("Re-transcribiendo…")
			with self._gpu:
				tr = self.asr.transcribir(linea.audio, idioma=idioma)
			linea.origen, linea.original, linea.traduccion = idioma, tr.texto, ""
			self.cb.linea_actualizada(linea)
			self._cola_trad.put(linea)

	def _traducir(self, linea: Linea) -> None:
		self.cb.estado("Traduciendo…")
		with self._candado:
			previas = [l for l in self.lineas if l.id < linea.id][-CONTEXTO_LINEAS:]
		contexto = [f"({l.origen.upper()}) {l.original}" for l in previas]
		with self._gpu:
			tr = self.traductor.traducir(
				linea.original, linea.origen, linea.destino, contexto, al_token=lambda t: self.cb.token(linea, t)
			)
		linea.traduccion = tr.texto
		linea.t_primer_token = tr.primer_token
		linea.t_traduccion = tr.total
		linea.t_listo = time.time()
		self.cb.linea_traducida(linea)
		if self.pendientes() <= 1:
			self.cb.estado("Escuchando…")
