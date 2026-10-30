# Recordatorio de «usted» en cada frase al español

Fecha: 2026-10-29. Interruptor: `USTED_RECORDATORIO` en `config.py` (`False` = como antes).

## Problema

Las reglas de `_SISTEMA` exigen «usted», pero qwen3:8b igual tuteaba en **27 de 321**
frases al español (8 %), por ejemplo «¿Cómo te va con tu dieta?» o «Cuéntame más
sobre tu tos». No cuentan los «ustedes» correctos del video de asma, donde el
médico habla con la mamá y el hijo («you guys»).

## Cambio

Solo cambia el pedido de cada frase al español; `_SISTEMA` no se toca, así que el
prefijo que Ollama reutiliza es el mismo. La dirección ES→EN no cambia (se verifica):

```
Translate this English text into Spanish, using "usted" for "you":
```

## Resultado (321 frases al español, 9 videos de la playlist)

| | Original | B1 (descartada) | **B2 (elegida)** |
|---|---:|---:|---:|
| Frases con tuteo | 27 | 7 | **3** |
| Frases sin traducir | 0 | 2 | **0** |
| «Hágale saber» mal usado | 0 | 2 | 2 |
| Texto distinto del original | — | 150 | 182 |
| Tiempo total medio | 1,95 s | +0,08 s | +0,05 s |

B1 decía `addressing the listener as "usted" (never "tú")`. Dejó sin traducir dos
frases que empezaban con «Okay,».

**Revisión a ciegas de B2 frente al original** (158 frases que cambian, sin las
propagandas del canal; revisión asistida por IA, no clínica):

- Trato de usted: **27 mejores, 0 peores.**
- Otros cambios: 16 mejores y 21 peores, casi todos de redacción. Errores de
  sentido: 5 corregidos y 4 nuevos. El prompt nuevo reordena la salida del modelo
  y eso también mueve frases que no tienen nada que ver con el tuteo.

Errores nuevos de B2 que conviene conocer:

- «Let me know if it hurts» → «Hágale saber si le duele», y «Just make sure not to eat» →
  «Hágale saber que no debe comer». Parece el ejemplo «Hágales saber» de las reglas
  aplicado donde no corresponde. Pasó lo mismo con B1.
- «Get some rest» → «que se quite un poco de sueño». También con B1.
- «Please tell us if you see discharge» → «¿Tiene usted secreción…?»
  (una instrucción que pasó a ser pregunta).

En los 2 videos de control, que no se usaron para diseñar el cambio
(23 Hypertension y 30 Asthma), el tuteo bajó de 8 frases a 0 (con B1 y con B2).

## Método

- Videos: 4, 15, 18, 19 y 27 (`corpus_playlist.json`), 1 y 8 (`corpus_glosario.json`)
  y 23 y 30 de control (`corpus_control.json`). Transcripción real de Whisper, 4
  líneas de contexto, glosario apagado y temperatura 0.
- Original y B1 en pares, con orden alternado y el mismo prefijo calentado antes de
  cada pedido (`comparar_usted.py`, `resultados_usted_b1.json`). B2 se corrió
  aparte con el mismo contexto (`resultados_usted_b2.json`). Su tiempo no está
  pareado y es orientativo.

## Reproducir

```bash
OLLAMA_HOST=127.0.0.1:11439 OLLAMA_VULKAN=1 ollama serve
# Otra terminal (mide la redacción actual de _PEDIDO_USTED contra el original):
python -B bench/comparar_usted.py --corpus bench/corpus_playlist.json bench/corpus_glosario.json bench/corpus_control.json --salida /tmp/usted.json
```
