import threading
import gc
import numpy as np
import sounddevice as sd
import whisper
import queue
from typing import Callable, Optional

try:
	import torch
except Exception:
	torch = None


class TranscriptorAudio:
	def __init__(
		self,
		modelo: str = "tiny",
		idioma: str = "es",
		device: str = "auto",
		dispositivo_entrada: Optional[int] = None,
		max_queue_blocks: int = 120,
		max_lineas: int = 400,
	):
		"""
		Inicializa el transcriptor de audio.
		
		Args:
			modelo: Modelo de Whisper a usar (tiny, base, small, medium, large)
			idioma: Código de idioma (ej: 'es' para español)
			device: Dispositivo de inferencia ('auto', 'cpu' o 'cuda')
			dispositivo_entrada: ID de dispositivo de entrada (None = auto monitor)
			max_queue_blocks: Máximo de bloques de audio en cola
			max_lineas: Máximo de líneas acumuladas de texto
		"""
		self.device = self._resolver_device_inferencia(device)
		self.modelo = whisper.load_model(modelo, device=self.device)
		self.idioma = idioma
		self.escuchando = False
		self.texto_actual = ""
		self.texto_acumulado = ""
		self.max_lineas = max_lineas
		self.lineas_texto = []
		self.callback = None
		self.cola_audio = queue.Queue(maxsize=max_queue_blocks)
		self.bloques_descartados = 0
		self.hilo_grabacion = None
		self.hilo_transcripcion = None
		self.frecuencia_muestreo = 16000
		self.duracion_chunk = 3  # segundos entre transcripciones
		self.dispositivo_entrada = dispositivo_entrada

		if self.dispositivo_entrada is None:
			self.dispositivo_entrada = self._detectar_monitor_sistema()

		if self.dispositivo_entrada is None:
			print("No se encontro monitor de salida; se usara entrada por defecto (microfono).")
		else:
			info = sd.query_devices(self.dispositivo_entrada)
			print(f"Capturando audio del sistema desde: {info.get('name', self.dispositivo_entrada)}")

	@staticmethod
	def _resolver_device_inferencia(device: str) -> str:
		objetivo = (device or "auto").lower()

		if objetivo == "cpu":
			return "cpu"

		if torch is None:
			cuda_disponible = False
		else:
			cuda_disponible = bool(hasattr(torch, "cuda") and torch.cuda.is_available())

		if objetivo == "cuda":
			if cuda_disponible:
				return "cuda"
			raise RuntimeError(
				"No hay backend GPU disponible para Whisper en este entorno de PyTorch. "
				"Para usar VRAM en AMD RX570 necesitas un stack compatible (ROCm/PyTorch adecuado) "
				"o usar whisper.cpp con backend Vulkan."
			)

		if objetivo == "auto":
			return "cuda" if cuda_disponible else "cpu"

		return "cpu"

	@staticmethod
	def listar_dispositivos_entrada() -> list[dict]:
		"""Devuelve dispositivos de entrada disponibles, marcando monitores del sistema."""
		dispositivos = []
		for idx, d in enumerate(sd.query_devices()):
			if d.get("max_input_channels", 0) <= 0:
				continue
			nombre = str(d.get("name", ""))
			nombre_low = nombre.lower()
			es_monitor = (
				"monitor" in nombre_low
				or "what u hear" in nombre_low
				or "stereo mix" in nombre_low
				or ".monitor" in nombre_low
			)
			dispositivos.append({"id": idx, "name": nombre, "is_monitor": es_monitor})
		return dispositivos

	def _detectar_monitor_sistema(self) -> Optional[int]:
		"""Busca un dispositivo de entrada tipo monitor (Pulse/PipeWire)."""
		try:
			dispositivos = self.listar_dispositivos_entrada()
		except Exception:
			return None

		candidatos = [d["id"] for d in dispositivos if d.get("is_monitor")]

		if candidatos:
			# Prioriza nombres típicos de PulseAudio/PipeWire.
			for idx in candidatos:
				nombre = str(sd.query_devices(idx).get("name", "")).lower()
				if "monitor of" in nombre or ".monitor" in nombre:
					return idx
			return candidatos[0]

		return None
		
	def _grabar_audio(self) -> None:
		"""Captura audio del micrófono continuamente."""
		try:
			def callback_audio(indata, frames, time_info, status):
				if status:
					print(f"Advertencia de audio: {status}")
				bloque = indata.copy()
				try:
					self.cola_audio.put_nowait(bloque)
				except queue.Full:
					# Evita crecimiento infinito de memoria cuando Whisper se atrasa.
					try:
						self.cola_audio.get_nowait()
					except queue.Empty:
						pass
					self.bloques_descartados += 1
					try:
						self.cola_audio.put_nowait(bloque)
					except queue.Full:
						self.bloques_descartados += 1
			
			with sd.InputStream(
				samplerate=self.frecuencia_muestreo,
				channels=1,
				blocksize=self.frecuencia_muestreo // 10,
				device=self.dispositivo_entrada,
				callback=callback_audio,
				dtype=np.float32
			):
				while self.escuchando:
					sd.sleep(100)
		except Exception as e:
			print(f"Error en grabación de audio: {e}")
	
	def _transcribir_continuamente(self) -> None:
		"""Procesa el audio grabado y lo transcribe con Whisper."""
		buffer_audio = []
		contador_frames = 0
		frames_por_chunk = int(self.frecuencia_muestreo * self.duracion_chunk)
		
		try:
			while self.escuchando:
				try:
					# Obtener datos de audio de la cola
					datos = self.cola_audio.get(timeout=1)
					buffer_audio.append(datos)
					contador_frames += len(datos)
					
					# Transcribir cuando se alcanza la duración del chunk
					if contador_frames >= frames_por_chunk:
						# Concatenar todo el audio capturado
						audio_array = np.concatenate(buffer_audio, axis=0).reshape(-1).astype(np.float32)
						
						# Transcribir con Whisper
						resultado = self.modelo.transcribe(
							audio_array,
							language=self.idioma,
							fp16=(self.device == "cuda"),
							condition_on_previous_text=False,
							temperature=0,
						)
						
						# Extraer el texto transcrito
						texto_resultado = resultado.get("text", "") if isinstance(resultado, dict) else ""
						self.texto_actual = str(texto_resultado).strip()
						
						# Acumular el texto
						if self.texto_actual:
							self.lineas_texto.append(self.texto_actual)
							if len(self.lineas_texto) > self.max_lineas:
								self.lineas_texto = self.lineas_texto[-self.max_lineas:]
							self.texto_acumulado = "\n".join(self.lineas_texto)
							
							# Llamar al callback si existe
							if self.callback:
								self.callback(self.texto_actual, self.texto_acumulado)
						
						# Reiniciar buffer
						buffer_audio = []
						contador_frames = 0
						gc.collect()
						
				except queue.Empty:
					# Sin datos en la cola por ahora
					continue
				except Exception as e:
					print(f"Error en transcripción: {e}")
					
		except Exception as e:
			print(f"Error en hilo de transcripción: {e}")
	
	def iniciar(self, callback: Optional[Callable] = None) -> None:
		"""
		Inicia la captura y transcripción de audio.
		
		Args:
			callback: Función que se llama con (texto_nuevo, texto_acumulado)
		"""
		if self.escuchando:
			print("Ya se está escuchando")
			return
		
		self.callback = callback
		self.escuchando = True
		self.texto_actual = ""
		self.texto_acumulado = ""
		self.lineas_texto = []
		self.bloques_descartados = 0
		while not self.cola_audio.empty():
			try:
				self.cola_audio.get_nowait()
			except queue.Empty:
				break
		
		# Iniciar hilo de grabación
		self.hilo_grabacion = threading.Thread(target=self._grabar_audio, daemon=True)
		self.hilo_grabacion.start()
		
		# Iniciar hilo de transcripción
		self.hilo_transcripcion = threading.Thread(target=self._transcribir_continuamente, daemon=True)
		self.hilo_transcripcion.start()
		
		print("Escuchando... (presiona Ctrl+C para detener)")
	
	def detener(self) -> None:
		"""Detiene la captura y transcripción de audio."""
		self.escuchando = False
		
		# Esperar a que terminen los hilos
		if self.hilo_grabacion:
			self.hilo_grabacion.join(timeout=2)
		if self.hilo_transcripcion:
			self.hilo_transcripcion.join(timeout=2)
		
		print(f"Se detuvo la escucha. Bloques descartados: {self.bloques_descartados}")
	
	def obtener_texto_acumulado(self) -> str:
		"""Retorna el texto acumulado hasta ahora."""
		return self.texto_acumulado
	
	def obtener_texto_actual(self) -> str:
		"""Retorna el último texto transcrito."""
		return self.texto_actual
	
	def limpiar_texto(self) -> None:
		"""Limpia el texto acumulado."""
		self.texto_acumulado = ""
		self.texto_actual = ""


if __name__ == "__main__":
	# Ejemplo de uso
	def callback_transcripcion(texto_nuevo, texto_acumulado):
		print(f"\n[NUEVO] {texto_nuevo}")
		print(f"[ACUMULADO]\n{texto_acumulado}\n")
	
	transcriptor = TranscriptorAudio(modelo="tiny", idioma="es", device="auto")
	transcriptor.iniciar(callback=callback_transcripcion)
	
	try:
		while True:
			import time
			time.sleep(0.1)
	except KeyboardInterrupt:
		print("\nDeteniendo...")
		transcriptor.detener()
