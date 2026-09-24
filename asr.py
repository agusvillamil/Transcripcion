"""Transcripción con whisper-server (whisper.cpp, GPU vía Vulkan).

El modelo se carga una sola vez en el servidor. Cada fragmento se envía por
HTTP y Whisper detecta el idioma de ese fragmento (inglés o español).
"""
import io
import json
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
import wave
from collections import deque
from dataclasses import dataclass

import numpy as np

import config

# Nombres que devuelve whisper.cpp -> código. Idiomas cercanos al español se
# tratan como español (Whisper a veces confunde es con pt/gl/ca/it).
_IDIOMAS_ROMANCES = {"spanish", "portuguese", "galician", "catalan", "italian"}

# Frases que Whisper inventa sobre silencio o ruido.
_ALUCINACIONES = {
	"subtítulos realizados por la comunidad de amara.org",
	"subtitulado por la comunidad de amara.org",
	"gracias por ver el video",
	"gracias por ver",
	"thanks for watching",
	"thank you for watching",
	"you",
	"[blank_audio]",
	"[music]",
	"(música)",
}

# Respuestas cortas que suenan igual en ambos idiomas.
_PALABRAS_AMBIGUAS = {"no", "ok", "okay", "si", "sí", "mm", "mhm", "ah", "eh", "oh"}


@dataclass
class Transcripcion:
	texto: str
	idioma: str          # "en" o "es"
	idioma_whisper: str  # lo que detectó Whisper (ej. "english")
	segundos: float      # tiempo de inferencia


class ServidorWhisper:
	"""Lanza whisper-server como subproceso y le envía fragmentos."""

	def __init__(
		self,
		modelo: str = config.WHISPER_MODELO,
		puerto: int = config.WHISPER_PUERTO,
		audio_ctx: int = config.WHISPER_AUDIO_CTX,
	) -> None:
		self.modelo = modelo
		self.puerto = puerto
		self.audio_ctx = audio_ctx
		self.url = f"http://{config.WHISPER_HOST}:{puerto}"
		self.proceso: subprocess.Popen | None = None
		self.usa_gpu: bool | None = None  # None = servidor externo, no se sabe
		self._log: deque[str] = deque(maxlen=200)

	def iniciar(self, timeout: float = 60) -> None:
		if self._responde():
			return  # ya hay un servidor escuchando en ese puerto
		ruta = config.WHISPER_MODELOS_DIR / self.modelo
		if not ruta.exists():
			raise FileNotFoundError(f"No existe el modelo Whisper: {ruta}")
		self.proceso = subprocess.Popen(
			[
				str(config.WHISPER_SERVER_BIN),
				"-m", str(ruta),
				"-l", "auto",
				"-t", str(config.WHISPER_HILOS),
				"--host", config.WHISPER_HOST,
				"--port", str(self.puerto),
				"-ac", str(self.audio_ctx),
				"-nlp",
			],
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
		)
		self.usa_gpu = False
		threading.Thread(target=self._drenar_log, daemon=True).start()
		limite = time.time() + timeout
		while not self._responde():
			if self.proceso.poll() is not None:
				raise RuntimeError("whisper-server terminó al iniciar:\n" + "".join(list(self._log)[-20:]))
			if time.time() > limite:
				self.detener()
				raise TimeoutError("whisper-server no respondió a tiempo")
			time.sleep(0.3)
		# El primer pedido compila shaders y fija audio_ctx para la detección de idioma.
		self.transcribir(np.zeros(config.FRECUENCIA, dtype=np.float32))

	def detener(self) -> None:
		if self.proceso and self.proceso.poll() is None:
			self.proceso.terminate()
			try:
				self.proceso.wait(timeout=5)
			except subprocess.TimeoutExpired:
				self.proceso.kill()
		self.proceso = None

	def transcribir(self, audio: np.ndarray, idioma: str | None = None) -> Transcripcion:
		"""Transcribe un fragmento; idioma=None detecta automáticamente."""
		t0 = time.time()
		respuesta = self._pedir(audio, idioma or "auto")
		detectado = str(respuesta.get("language", "")).lower()
		codigo = idioma or ("es" if detectado in _IDIOMAS_ROMANCES else "en")
		if idioma is None and detectado not in ("english", "spanish"):
			# Whisper transcribió en otro idioma: se repite forzando el más probable.
			respuesta = self._pedir(audio, codigo)
		return Transcripcion(
			texto=limpiar_texto(str(respuesta.get("text", ""))),
			idioma=codigo,
			idioma_whisper=detectado,
			segundos=time.time() - t0,
		)

	def _pedir(self, audio: np.ndarray, idioma: str) -> dict:
		campos = {
			"response_format": "verbose_json",
			"temperature": "0",
			"no_timestamps": "true",  # evita palabras partidas y bucles de repetición
			"no_language_probabilities": "true",  # evita un encode extra
			"audio_ctx": str(self.audio_ctx),
			"language": idioma,
		}
		frontera = uuid.uuid4().hex
		cuerpo = io.BytesIO()
		for nombre, valor in campos.items():
			cuerpo.write(f'--{frontera}\r\nContent-Disposition: form-data; name="{nombre}"\r\n\r\n{valor}\r\n'.encode())
		cuerpo.write(
			f'--{frontera}\r\nContent-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
			"Content-Type: audio/wav\r\n\r\n".encode()
		)
		cuerpo.write(a_wav(audio))
		cuerpo.write(f"\r\n--{frontera}--\r\n".encode())
		pedido = urllib.request.Request(
			self.url + "/inference",
			data=cuerpo.getvalue(),
			headers={"Content-Type": f"multipart/form-data; boundary={frontera}"},
		)
		with urllib.request.urlopen(pedido, timeout=60) as r:
			return json.loads(r.read())

	def _responde(self) -> bool:
		try:
			with urllib.request.urlopen(self.url + "/", timeout=1):
				return True
		except (urllib.error.URLError, OSError):
			return False

	def _drenar_log(self) -> None:
		"""Lee la salida del servidor para que la tubería no se llene."""
		for linea in self.proceso.stdout:
			self._log.append(linea)
			if "ggml_vulkan: 0 =" in linea:
				self.usa_gpu = True


def a_wav(audio: np.ndarray) -> bytes:
	buffer = io.BytesIO()
	with wave.open(buffer, "wb") as w:
		w.setnchannels(1)
		w.setsampwidth(2)
		w.setframerate(config.FRECUENCIA)
		w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
	return buffer.getvalue()


def limpiar_texto(texto: str) -> str:
	texto = re.sub(r"\s+", " ", texto).strip()
	if texto.lower().strip(" .!¡¿?") in _ALUCINACIONES:
		return ""
	# Quita oraciones repetidas consecutivas (bucles típicos de Whisper).
	oraciones = re.split(r"(?<=[.!?])\s+", texto)
	limpias: list[str] = []
	for o in oraciones:
		if not limpias or o.lower() != limpias[-1].lower():
			limpias.append(o)
	return " ".join(limpias)


def es_ambiguo(texto: str) -> bool:
	"""True si el texto solo tiene palabras que existen igual en inglés y español."""
	palabras = re.findall(r"[a-záéíóúñü]+", texto.lower())
	return bool(palabras) and all(p in _PALABRAS_AMBIGUAS for p in palabras)
