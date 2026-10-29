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
   - Fórmulas de cortesía y respuestas cortas («Thank you.», «No, ninguna. Muchas gracias, doctora.») salen al
     instante de una tabla fija (`frases.py`), sin pasar por el LLM. Se pueden agregar frases ahí.
   - Filtros Todo / EN→ES / ES→EN, A−/A+ (Ctrl +/−), Guardar sesión (Ctrl+S), Limpiar (Ctrl+L).
4. Al terminar la llamada, **Guardar sesión (Ctrl+S)**: la guarda como nota en la bóveda de Obsidian
   (`~/Documentos/Obsidian Vault/Llamadas/DD-MM-YYYY - HH.MM.md`, con fecha, duración y turnos como propiedades)
   y limpia la consola. Si hay una frase traduciéndose, espera a que termine. La carpeta se cambia en `config.py`.
   Los turnos de puro relleno («Thank you.», «Okay.» que Whisper inventa sobre ruido) quedan plegados en bloques
   «Ruido» colapsados: no se borra nada. `python limpieza.py --deshacer` los despliega; `--aplicar` limpia notas viejas.

5. **Repaso.** «☆ Repasar» en una tarjeta marca ese turno para estudiarlo después: al guardar queda con
   `#repasar` debajo de la traducción (y `repasar: N` en las propiedades de la nota). Un turno marcado nunca
   se pliega como ruido. `python repaso.py` lee las llamadas sin modificarlas y escribe `Repaso.md` en la raíz
   de la bóveda: llamadas y tiempo por semana y por día, los turnos marcados con enlace a su llamada, y los
   términos que más se repiten entre llamadas (conteo simple, lista aproximada para un glosario).
   La nota se reescribe entera cada vez; para sacar un turno, borrar su `#repasar` en la nota de la llamada.

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
| `frases.py` | Traducciones fijas de fórmulas de cortesía (editable) |
| `sesion.py` | Orquesta transcripción → traducción; turna la GPU entre ambos |
| `repaso.py` | Arma `Repaso.md` con horas, turnos marcados y términos frecuentes |
| `config.py` | Modelos, umbrales y parámetros |
| `bench/probar_video.py` | Prueba/benchmark sobre un archivo de audio |
| `legacy/` | Versión anterior (Tkinter + openai-whisper), ya no se usa |

## Modelo de traducción

Probado con el video de práctica NBCMI/CCHI "Laparoscopic Cholecystectomy" (12:42, 55 frases EN/ES).
Reporte completo con las 55 traducciones de cada modelo: `bench/reporte_colecistectomia.md`.

| Modelo | Traducción (media) | Calidad |
|---|---|---|
| **qwen3:8b** (por defecto) | 1.9 s | La más fiel; mezclaba tú/usted (corregido en el prompt, ver abajo) |
| gemma3:4b | 2.3 s | Buena; algunas omisiones ("laparoscópica") |
| translategemma:4b | 1.0 s | Fluida pero agrega/invierte sentido (ej. "awareness" → "pérdida de conciencia") |
| mistral | 2.4 s | Tutea, agrega notas, inventa ante frases cortas |
| llama3.2:3b | 1.0 s | Muchos errores de terminología |

Todos corren 100% en la GPU junto con Whisper. Instalados: **qwen3:8b** y **gemma3:4b** (respaldo); los demás
se borraron tras la prueba. Se cambia desde el selector "Traducción" de la app.

El prompt (`traductor.py`) exige «usted» singular en todo (verbos, pronombres e imperativos: «Venga a verme»,
«Hágales saber») y fórmulas de cortesía por su equivalente («You're welcome» → «De nada»). Es igual para ambas
direcciones: Ollama reutiliza la parte ya procesada y las reglas extra no agregan latencia (medido: 1.53 s de
media antes y después, sobre las 55 frases del reporte). Validado solo con qwen3:8b.

## Notas de rendimiento (RX 570, 8 GB)

- ROCm/PyTorch no soporta esta GPU (Polaris, gfx803); Vulkan sí.
- Whisper turbo: ~2.6 s por frase en GPU (en CPU sería ~12 veces más lento).
- Prueba en vivo con el video: traducción completa ~4.5 s (mediana) después de que termina cada frase.
- Whisper y el LLM se turnan la GPU: usarlos a la vez la vuelve 4–6 veces más lenta.
- `WHISPER_AUDIO_CTX = 768` limita cada fragmento a 15 s (el segmentador corta a los 12 s).

## Consumo durante la llamada

Medido con el video de práctica NBCMI/CCHI "19. Coronary Artery Disease" (20:39, 73 líneas), antes y después de
estos ajustes: las 73 transcripciones y las 73 traducciones salen idénticas. No tocan los modelos.

| Ajuste (`config.py`) | Qué hace | Efecto medido | Como antes |
|---|---|---|---|
| `UI_REFRESCO_MS = 100` | Pinta la traducción en curso cada 100 ms, no con cada token | CPU de la interfaz al traducir, con 60 tarjetas: 82 % → 26 % de un núcleo | `0` |
| `AUDIO_TARJETAS = 10` | Solo las últimas 10 tarjetas guardan su audio y el botón «⇄» | Audio en RAM al final del video: 27 MB → 5 MB | `0` |

- `WHISPER_HILOS` sigue en 4: con 2 el texto, el tiempo por frase y la CPU (¼ de núcleo) son los mismos.
- El tiempo de Whisper cambia entre sesiones de la PC sin que cambie el texto: sobre el mismo video dio 2.6 s por
  frase el 7-oct de madrugada y 1.1 s al mediodía, tras reiniciar, con el mismo código, modelo y `config.py`
  (73 líneas y 1307 palabras las dos veces). Causa sin identificar; la traducción tardó lo mismo (2.3 s).
- Mientras procesa una frase la GPU está al ~100 % y `llama-server` ocupa ~0.8 núcleos. VRAM máxima: 6.1 de 8 GB.

## Actualizaciones futuras

- **Glosario personal en Obsidian.** Una nota de la bóveda (ej. `Glosario.md`) con pares de términos
  (`light duty = trabajo liviano`, `follow-up = cita de control`) que se le pasen al LLM en cada traducción,
  para que la terminología sea siempre la misma. Pasar solo los términos que aparecen en la frase, y ponerlos
  después de las reglas fijas del prompt, para no hacer más lenta la traducción.
