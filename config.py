"""Configuración central del asistente de interpretación EN⇄ES."""
from pathlib import Path

FRECUENCIA = 16000  # Whisper trabaja a 16 kHz mono

# --- Whisper (whisper.cpp con backend Vulkan) ---
WHISPER_DIR = Path.home() / "whisper.cpp"
WHISPER_SERVER_BIN = WHISPER_DIR / "build/bin/whisper-server"
WHISPER_MODELOS_DIR = WHISPER_DIR / "models"
WHISPER_MODELO = "ggml-large-v3-turbo-q5_0.bin"
WHISPER_HOST = "127.0.0.1"
WHISPER_PUERTO = 8178
WHISPER_HILOS = 4
WHISPER_AUDIO_CTX = 768  # 15 s de contexto: ~2x más rápido que 30 s en la RX 570

# --- Ollama (backend Vulkan) ---
OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODELO = "qwen3:8b"  # el más fiel en el benchmark médico; ver README
OLLAMA_CONTEXTO = 2048

# --- Segmentación por voz (VAD por energía) ---
VAD_FRAME_MS = 30
VAD_PRE_ROLL_MS = 300        # audio previo al inicio de voz que se conserva
VAD_VOZ_MIN_MS = 200         # menos voz que esto se descarta (clics); un "No." dura ~400 ms
VAD_PAUSA_CHUNK_MS = 500     # pausa que cierra un fragmento
VAD_PAUSA_SUAVE_MS = 250     # pausa corta aceptada si el fragmento ya es largo
VAD_CORTE_SUAVE_S = 6.0
VAD_CORTE_DURO_S = 12.0
VAD_SILENCIO_TURNO_MS = 1200  # silencio que separa turnos de hablantes
VAD_MARGEN_DB = 10.0         # dB sobre el piso de ruido para considerar voz
VAD_UMBRAL_MIN_DB = -55.0    # nunca se considera voz por debajo de esto

IDIOMAS = {"en": "English", "es": "Español"}
