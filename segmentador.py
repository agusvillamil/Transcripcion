"""Corta el audio continuo en fragmentos de voz usando energía y pausas.

Pensado para interpretación consecutiva: cada hablante dice una o varias
frases y hace una pausa. Los fragmentos se cierran en pausas naturales y los
silencios largos marcan un cambio de turno.
"""
from collections import deque
from dataclasses import dataclass

import numpy as np

import config


@dataclass
class Fragmento:
	audio: np.ndarray  # float32 mono a config.FRECUENCIA
	inicio: float      # segundos desde el comienzo de la captura
	fin: float
	turno: int         # fragmentos del mismo turno comparten id


class Segmentador:
	def __init__(self, frecuencia: int = config.FRECUENCIA) -> None:
		self.frecuencia = frecuencia
		self.frame = int(frecuencia * config.VAD_FRAME_MS / 1000)
		self.nivel_db = -100.0
		self.piso_db = -70.0
		self.turno = 0
		self._resto = np.zeros(0, dtype=np.float32)
		self._pre_roll = deque(maxlen=max(1, config.VAD_PRE_ROLL_MS // config.VAD_FRAME_MS))
		self._frames: list[np.ndarray] = []
		self._energias: list[float] = []
		self._en_voz = False
		self._ms_voz = 0
		self._ms_silencio = 10**9  # silencio acumulado (grande al inicio => nuevo turno)
		self._frames_totales = 0
		self._inicio_frame = 0

	@property
	def en_voz(self) -> bool:
		return self._en_voz

	def procesar(self, bloque: np.ndarray) -> list[Fragmento]:
		"""Agrega audio y devuelve los fragmentos que quedaron completos."""
		datos = np.concatenate([self._resto, bloque.reshape(-1).astype(np.float32)])
		n = len(datos) // self.frame
		self._resto = datos[n * self.frame:]
		salida = []
		for i in range(n):
			fragmento = self._procesar_frame(datos[i * self.frame:(i + 1) * self.frame])
			if fragmento is not None:
				salida.append(fragmento)
		return salida

	def vaciar(self) -> list[Fragmento]:
		"""Cierra el fragmento en curso (al detener la captura)."""
		fragmento = self._emitir(len(self._frames)) if self._en_voz else None
		self._en_voz = False
		return [fragmento] if fragmento else []

	def _procesar_frame(self, frame: np.ndarray) -> Fragmento | None:
		db = float(20 * np.log10(np.sqrt(np.mean(frame * frame)) + 1e-10))
		self.nivel_db = db
		self._frames_totales += 1
		es_voz = db > max(self.piso_db + config.VAD_MARGEN_DB, config.VAD_UMBRAL_MIN_DB)
		self._actualizar_piso(db, es_voz)

		if not self._en_voz:
			if es_voz:
				if self._ms_silencio >= config.VAD_SILENCIO_TURNO_MS:
					self.turno += 1
				self._en_voz = True
				self._frames = list(self._pre_roll) + [frame]
				self._energias = [-100.0] * len(self._pre_roll) + [db]
				self._inicio_frame = self._frames_totales - len(self._frames)
				self._ms_voz = config.VAD_FRAME_MS
				self._ms_silencio = 0
			else:
				self._ms_silencio += config.VAD_FRAME_MS
				self._pre_roll.append(frame)
			return None

		self._frames.append(frame)
		self._energias.append(db)
		if es_voz:
			self._ms_voz += config.VAD_FRAME_MS
			self._ms_silencio = 0
		else:
			self._ms_silencio += config.VAD_FRAME_MS

		duracion = len(self._frames) * config.VAD_FRAME_MS / 1000
		if self._ms_silencio >= config.VAD_PAUSA_CHUNK_MS or (
			duracion >= config.VAD_CORTE_SUAVE_S and self._ms_silencio >= config.VAD_PAUSA_SUAVE_MS
		):
			# Conserva ~200 ms de cola de silencio; el resto se descarta.
			sobrante = max(0, self._ms_silencio - 200) // config.VAD_FRAME_MS
			fragmento = self._emitir(len(self._frames) - sobrante)
			self._en_voz = False
			self._pre_roll.clear()
			return fragmento

		if duracion >= config.VAD_CORTE_DURO_S:
			# Corta en el frame más silencioso del último segundo y medio.
			ventana = int(1500 / config.VAD_FRAME_MS)
			cola = self._energias[-ventana:]
			corte = len(self._frames) - ventana + int(np.argmin(cola)) + 1
			return self._emitir(corte, continuar=True)
		return None

	def _actualizar_piso(self, db: float, es_voz: bool) -> None:
		if db < self.piso_db:
			self.piso_db = max(-85.0, 0.7 * self.piso_db + 0.3 * db)
		elif not es_voz:
			self.piso_db = min(-20.0, self.piso_db + 0.01 * (db - self.piso_db))

	def _emitir(self, n_frames: int, continuar: bool = False) -> Fragmento | None:
		frames, resto = self._frames[:n_frames], self._frames[n_frames:]
		inicio = self._inicio_frame
		ms_voz = self._ms_voz
		if continuar:
			self._frames = resto
			self._energias = self._energias[n_frames:]
			self._inicio_frame += n_frames
			self._ms_voz = len(resto) * config.VAD_FRAME_MS  # cortes duros ocurren en habla continua
		if not frames or ms_voz < config.VAD_VOZ_MIN_MS:
			return None
		segundos = self.frame / self.frecuencia
		return Fragmento(
			audio=np.concatenate(frames),
			inicio=inicio * segundos,
			fin=(inicio + len(frames)) * segundos,
			turno=self.turno,
		)
