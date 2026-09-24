# Intérprete EN ⇄ ES

Asistente para interpretación consecutiva de llamadas. Escucha el audio del sistema (lo que suena en los
auriculares), transcribe cada frase con Whisper y la traduce con un modelo local de Ollama:
inglés → español y español → inglés, detectando el idioma de cada frase automáticamente.

Todo corre local, en la GPU (AMD RX 570) vía **Vulkan**.

## Uso

```bash
python3 app.py
```

1. Esperar "Listo." (la primera carga de modelos tarda ~20 s).
2. En **Audio** elegir "Salida del sistema: …" (el monitor de los auriculares/parlantes de la llamada).
3. **Iniciar (F9)**. Cada turno aparece como una tarjeta: original arriba, traducción grande abajo.
   - Azul = EN → ES, verde = ES → EN. Números, dosis y unidades resaltados en amarillo.
   - «⇄ Es español / Es inglés» corrige una frase detectada en el idioma equivocado.
   - Filtros Todo / EN→ES / ES→EN, A−/A+ (Ctrl +/−), Guardar sesión (Ctrl+S), Limpiar (Ctrl+L).

## Requisitos (ya instalados en esta PC)

- `~/whisper.cpp` compilado con `-DGGML_VULKAN=1` y el modelo `ggml-large-v3-turbo-q5_0.bin`
  (`~/whisper.cpp/models/download-ggml-model.sh large-v3-turbo-q5_0`).
- `ollama` con soporte Vulkan (`ollama-vulkan`) y el modelo de traducción (`ollama pull <modelo>`).
  Si Ollama no está corriendo, la app lo inicia.
- Python 3 con `PySide6` y `numpy`; `pactl`/`parec` (PipeWire).

## Archivos

| Archivo | Qué hace |
|---|---|
| `app.py` | Interfaz (PySide6) |
| `captura.py` | Audio del sistema con `parec` |
| `segmentador.py` | Corta el audio en frases usando pausas (VAD por energía) |
| `asr.py` | Whisper (`whisper-server`) + detección de idioma por frase |
| `traductor.py` | Traducción con Ollama (prompt de intérprete médico) |
| `sesion.py` | Orquesta transcripción → traducción; turna la GPU entre ambos |
| `config.py` | Modelos, umbrales y parámetros |
| `bench/probar_video.py` | Prueba/benchmark sobre un archivo de audio |
| `legacy/` | Versión anterior (Tkinter + openai-whisper), ya no se usa |

## Modelo de traducción

Probado con el video de práctica NBCMI/CCHI "Laparoscopic Cholecystectomy" (12:42, 55 frases EN/ES).
Reporte completo con las 55 traducciones de cada modelo: `bench/reporte_colecistectomia.md`.

| Modelo | Traducción (media) | Calidad |
|---|---|---|
| **qwen3:8b** (por defecto) | 1.9 s | La más fiel; a veces mezcla tú/usted |
| gemma3:4b | 2.3 s | Buena; algunas omisiones ("laparoscópica") |
| translategemma:4b | 1.0 s | Fluida pero agrega/invierte sentido (ej. "awareness" → "pérdida de conciencia") |
| mistral | 2.4 s | Tutea, agrega notas, inventa ante frases cortas |
| llama3.2:3b | 1.0 s | Muchos errores de terminología |

Todos corren 100% en la GPU junto con Whisper. Se cambia desde el selector "Traducción" de la app.

## Notas de rendimiento (RX 570, 8 GB)

- ROCm/PyTorch no soporta esta GPU (Polaris, gfx803); Vulkan sí.
- Whisper turbo: ~2.6 s por frase en GPU (en CPU sería ~12 veces más lento).
- Prueba en vivo con el video: traducción completa ~4.5 s (mediana) después de que termina cada frase.
- Whisper y el LLM se turnan la GPU: usarlos a la vez la vuelve 4–6 veces más lenta.
- `WHISPER_AUDIO_CTX = 768` limita cada fragmento a 15 s (el segmentador corta a los 12 s).
