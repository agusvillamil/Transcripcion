"""Captura de audio con parec (PipeWire / PulseAudio).

Para escuchar una llamada se usa el "monitor" de la salida de audio: es lo
mismo que suena en los auriculares o parlantes.
"""
import json
import subprocess
import threading
from dataclasses import dataclass
from typing import Callable

import numpy as np

import config

_MUESTRAS_BLOQUE = config.FRECUENCIA // 10  # 100 ms


@dataclass
class Fuente:
	nombre: str       # identificador de PipeWire/Pulse
	descripcion: str
	es_monitor: bool  # True = audio del sistema; False = micrófono


def listar_fuentes() -> list[Fuente]:
	"""Fuentes de audio, primero los monitores (audio del sistema)."""
	salida = subprocess.run(["pactl", "-f", "json", "list", "sources"], capture_output=True, text=True, check=True)
	fuentes = []
	for s in json.loads(salida.stdout):
		# pactl devuelve "(null)" cuando la descripción tiene acentos; se usa la del dispositivo.
		descripcion = s.get("description")
		if not descripcion or descripcion == "(null)":
			descripcion = s.get("properties", {}).get("device.description") or s["name"]
		fuentes.append(Fuente(s["name"], descripcion, s["name"].endswith(".monitor")))
	return sorted(fuentes, key=lambda f: not f.es_monitor)


def monitor_predeterminado() -> str | None:
	"""Monitor de la salida de audio por defecto (lo que se está escuchando)."""
	salida = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True)
	sink = salida.stdout.strip()
	return f"{sink}.monitor" if sink else None


class CapturaAudio:
	def __init__(self, fuente: str, al_bloque: Callable[[np.ndarray], None]) -> None:
		self.fuente = fuente
		self.al_bloque = al_bloque
		self.proceso: subprocess.Popen | None = None
		self._hilo: threading.Thread | None = None

	def iniciar(self) -> None:
		self.proceso = subprocess.Popen(
			[
				"parec", "-d", self.fuente,
				"--format=float32le", f"--rate={config.FRECUENCIA}", "--channels=1",
				"--raw", "--latency-msec=50",
			],
			stdout=subprocess.PIPE,
			stderr=subprocess.DEVNULL,
		)
		self._hilo = threading.Thread(target=self._leer, daemon=True)
		self._hilo.start()

	def detener(self) -> None:
		if self.proceso and self.proceso.poll() is None:
			self.proceso.terminate()
			self.proceso.wait(timeout=2)
		if self._hilo:
			self._hilo.join(timeout=2)
		self.proceso = None

	def activa(self) -> bool:
		return self.proceso is not None and self.proceso.poll() is None

	def _leer(self) -> None:
		tamano = _MUESTRAS_BLOQUE * 4
		flujo = self.proceso.stdout
		while True:
			datos = flujo.read(tamano)
			if not datos:
				return
			usable = len(datos) - len(datos) % 4
			self.al_bloque(np.frombuffer(datos[:usable], dtype=np.float32))
