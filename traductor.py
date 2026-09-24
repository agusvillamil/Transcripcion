"""Traducción EN⇄ES con un modelo local de Ollama (GPU vía Vulkan)."""
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

import config

_NOMBRES = {"en": "English", "es": "Spanish"}

_SISTEMA = """You are a professional medical interpreter translating a live conversation between a healthcare provider and a patient. Translate the user's message from {origen} to {destino}.
Rules:
- Translate faithfully and completely: do not add, omit, summarize or explain anything.
- Keep the speaker's first-person voice, tone and register.
- Keep numbers, doses, units, dates, times and drug names exactly as said.
- Use correct medical terminology in {destino}. The text comes from speech recognition: if a medical term is misspelled, translate the intended term.
- The message may be very short (a greeting, "yes", "no"): translate just that, never continue or complete it.
- {estilo}
- Output only the {destino} translation, with no quotes, notes or labels."""

_PEDIDO = "Translate this {origen} text into {destino}:\n\n{texto}"

_ESTILO = {
	"es": "Use neutral Latin American Spanish. Always use formal 'usted' forms (le, su, usted), never 'tú' or 'vos'.",
	"en": "Use natural, plain American English.",
}

# Formato recomendado por Google para TranslateGemma.
_TRANSLATEGEMMA = (
	"You are a professional {origen} ({o}) to {destino} ({d}) translator. Your goal is to accurately convey "
	"the meaning and nuances of the original {origen} text while adhering to {destino} grammar, vocabulary, "
	"and cultural sensitivities.\nProduce only the {destino} translation, without any additional explanations "
	"or commentary. Please translate the following {origen} text into {destino}:\n\n\n{texto}"
)


@dataclass
class Traduccion:
	texto: str
	primer_token: float  # segundos hasta el primer token
	total: float


class Traductor:
	def __init__(self, modelo: str = config.OLLAMA_MODELO, url: str = config.OLLAMA_URL) -> None:
		self.modelo = modelo
		self.url = url
		self.proceso: subprocess.Popen | None = None
		self._piensa: dict[str, bool] = {}

	def asegurar_servidor(self, timeout: float = 30) -> None:
		"""Si Ollama no está corriendo, lo lanza como usuario."""
		if self._responde():
			return
		entorno = dict(os.environ, OLLAMA_KEEP_ALIVE="-1")
		self.proceso = subprocess.Popen(
			["ollama", "serve"], env=entorno, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
		)
		limite = time.time() + timeout
		while not self._responde():
			if time.time() > limite:
				raise TimeoutError("Ollama no respondió a tiempo")
			time.sleep(0.3)

	def detener(self) -> None:
		if self.proceso and self.proceso.poll() is None:
			self.proceso.terminate()
		self.proceso = None

	def modelos(self) -> list[str]:
		datos = self._json("/api/tags")
		return sorted(m["name"] for m in datos.get("models", []))

	def precargar(self) -> None:
		"""Carga el modelo en VRAM y lo calienta para que la primera traducción no espere."""
		self._json("/api/generate", {"model": self.modelo, "keep_alive": -1, "prompt": ""}, timeout=300)
		self.traducir("Good morning, how are you feeling today?", "en", "es")

	def liberar(self) -> None:
		"""Saca el modelo de la VRAM (al cambiar de modelo)."""
		self._json("/api/generate", {"model": self.modelo, "keep_alive": 0, "prompt": ""}, timeout=60)

	def en_gpu(self) -> float | None:
		"""Fracción del modelo cargado en VRAM (1.0 = todo en GPU)."""
		for m in self._json("/api/ps").get("models", []):
			if m.get("name") == self.modelo and m.get("size"):
				return m.get("size_vram", 0) / m["size"]
		return None

	def traducir(
		self,
		texto: str,
		origen: str,
		destino: str,
		contexto: list[str] | None = None,
		al_token: Callable[[str], None] | None = None,
	) -> Traduccion:
		"""Traduce en streaming. `contexto` son frases previas de la conversación."""
		cuerpo = {
			"model": self.modelo,
			"messages": self._mensajes(texto, origen, destino, contexto or []),
			"stream": True,
			"keep_alive": -1,
			"options": {"temperature": 0, "num_ctx": config.OLLAMA_CONTEXTO},
		}
		if self._soporta_pensar():
			cuerpo["think"] = False
		t0 = time.time()
		primer = None
		partes: list[str] = []
		pedido = urllib.request.Request(
			self.url + "/api/chat", data=json.dumps(cuerpo).encode(), headers={"Content-Type": "application/json"}
		)
		with urllib.request.urlopen(pedido, timeout=120) as r:
			for linea in r:
				dato = json.loads(linea)
				if "error" in dato:
					raise RuntimeError(dato["error"])
				token = dato.get("message", {}).get("content", "")
				if token:
					if primer is None:
						primer = time.time() - t0
					partes.append(token)
					if al_token:
						al_token(token)
				if dato.get("done"):
					break
		return Traduccion(limpiar_salida("".join(partes)), primer or 0.0, time.time() - t0)

	def _mensajes(self, texto: str, origen: str, destino: str, contexto: list[str]) -> list[dict]:
		o, d = _NOMBRES[origen], _NOMBRES[destino]
		if self.modelo.startswith("translategemma"):
			return [{"role": "user", "content": _TRANSLATEGEMMA.format(origen=o, destino=d, o=origen, d=destino, texto=texto)}]
		sistema = _SISTEMA.format(origen=o, destino=d, estilo=_ESTILO[destino])
		if contexto:
			sistema += "\n\nPrevious lines of the conversation, for context only (do not translate them):\n"
			sistema += "\n".join(f"- {linea}" for linea in contexto)
		pedido = _PEDIDO.format(origen=o, destino=d, texto=texto)
		return [{"role": "system", "content": sistema}, {"role": "user", "content": pedido}]

	def _soporta_pensar(self) -> bool:
		if self.modelo not in self._piensa:
			try:
				info = self._json("/api/show", {"model": self.modelo})
				self._piensa[self.modelo] = "thinking" in info.get("capabilities", [])
			except (urllib.error.URLError, OSError):
				self._piensa[self.modelo] = False
		return self._piensa[self.modelo]

	def _responde(self) -> bool:
		try:
			self._json("/api/version", timeout=1)
			return True
		except (urllib.error.URLError, OSError):
			return False

	def _json(self, ruta: str, cuerpo: dict | None = None, timeout: float = 10) -> dict:
		datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
		pedido = urllib.request.Request(self.url + ruta, data=datos, headers={"Content-Type": "application/json"})
		with urllib.request.urlopen(pedido, timeout=timeout) as r:
			return json.loads(r.read())


def limpiar_salida(texto: str) -> str:
	texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.S).strip()
	texto = re.sub(r"^(translation|traducción)\s*:\s*", "", texto, flags=re.I)
	if len(texto) >= 2 and texto[0] in "\"“«" and texto[-1] in "\"”»":
		texto = texto[1:-1].strip()
	return texto
