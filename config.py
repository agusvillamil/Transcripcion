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
WHISPER_HILOS = 4  # con 2 da el mismo texto, tiempo y CPU (medido): el trabajo lo hace la GPU
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

# --- Consumo de la app (para no competir con el navegador durante la llamada) ---
# No tocan los modelos ni el texto que producen. Cada uno se desactiva con 0.
UI_REFRESCO_MS = 100  # la traducción en curso se pinta cada 100 ms; 0 = con cada token, como antes
AUDIO_TARJETAS = 10   # tarjetas recientes que conservan su audio para «⇄»; 0 = todas, como antes

# --- Registro de llamadas: "Guardar sesión" escribe aquí (bóveda de Obsidian) ---
SESIONES_DIR = Path.home() / "Documentos/Obsidian Vault/Llamadas"

# --- Repaso: turnos marcados con «☆ Repasar» y la nota que arma `python repaso.py` ---
ETIQUETA_REPASAR = "#repasar"  # queda debajo de la traducción del turno marcado
REPASO_NOTA = SESIONES_DIR.parent / "Repaso.md"  # fuera de Llamadas/: no es una llamada
