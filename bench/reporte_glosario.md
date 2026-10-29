# Glosario de Paso a Paso: evaluación A/B

Fecha: 2026-10-29. Estado previo: `fd5c1e1`. Rama: `codex/glosario-paso-a-paso`.

## Resultado y decisión

**No se demostró una mejora general de calidad.** La versión conservadora corrige
un error claro en un caso sintético (`light duty`: «turnos ligeros» → «tareas
livianas»), pero también cambia una traducción correcta por otra menos natural
(`heartburn` → `acidity`, al traducir «acidez»). Un caso del video mejora el trato
formal pero empeora la construcción gramatical. Por eso queda **desactivado por
defecto**, disponible para pruebas o uso selectivo.

No se modificaron modelos, Whisper, segmentación, fórmulas fijas ni reglas del
prompt original. Con la opción apagada, los 102 pedidos se compararon con el
código del respaldo y fueron idénticos. Paso a Paso se leyó sin modificarlo.

## Material y método

- Qwen3 8B Q4_K_M, temperatura 0, thinking desactivado, contexto 2048.
- Ollama 0.40.12; AMD RX 570 8 GB, Vulkan, modelo 100% en GPU.
- 55 frases del benchmark anterior de colecistectomía.
- 35 fragmentos del [video solicitado de insuficiencia mitral](https://www.youtube.com/watch?v=lj1ObXJKDgA),
  transcritos una sola vez con `ggml-large-v3-turbo-q5_0.bin`, el segmentador y
  la detección de idioma actuales. No se retocó la transcripción para favorecer
  al glosario.
- 12 casos sintéticos, redactados antes de ejecutar el A/B, con criterios de
  significado, números, negaciones y registro.
- Ambas variantes reciben el mismo texto y las mismas cuatro líneas previas.
  Los casos sintéticos se ejecutan sin contexto artificial.
- Se calienta el mismo prefijo antes de cada variante y se alterna el orden A/B.
  Una repetición por variante. Se mide desde antes de enviar la petición.
- De 102 casos, el perfil final agrega referencias a **17**. Los otros **85**
  mantienen el mismo prompt o una fórmula fija: no se duplica su inferencia.
  No se presentan como 102 comparaciones de traducciones generadas.
- Cada resultado se guarda inmediatamente. El corpus, los resultados íntegros
  de los casos medidos y la huella de los archivos están en los JSON de `bench/`.

## Rendimiento del perfil final

Tiempos de traducción, con modelo ya cargado. **No incluyen Whisper, esperas de
cola ni una llamada en vivo.** Las pequeñas diferencias negativas son variación
normal de ejecución y/o longitud de salida, no aceleración atribuible al glosario.

| Grupo | Pares A/B | Base, media | Glosario, media | Incremento medio |
|---|---:|---:|---:|---:|
| Colecistectomía | 4 | 2,352 s | 2,455 s | +0,103 s |
| Video de insuficiencia mitral | 7 | 2,216 s | 2,440 s | +0,224 s |
| Contrastes sintéticos | 6 | 1,014 s | 1,383 s | +0,369 s |
| Total de frases con referencias | **17** | **1,824 s** | **2,071 s** | **+0,247 s** |

- Primer token: 0,802 s → 1,055 s (**+0,253 s**).
- Incremento de tiempo total: mediana +0,276 s; rango −0,091 a +0,542 s.
- Referencias añadidas: **37–81 tokens reales**, media 47,8, contados con el
  tokenizador del runner local. La aplicación usa un presupuesto estimado más
  conservador; no llama a otra IA ni a un tokenizador remoto en cada frase.
- Estos números no son un SLA ni sustituyen varias corridas con carga real.
  Frente a la estimación exploratoria de +0,53 s, este perfil envía menos entradas.

## Revisión lingüística de los 17 pares

Revisión asistida del significado frente al texto transcrito, no una validación
clínica ni una evaluación humana independiente. «Equivalente» permite diferencias
de redacción y no significa que ambas traducciones sean perfectas.

Los índices son los de `resultados_glosario.json`, desde cero.

| Índice | Resultado | Observación |
|---:|---|---|
| 5 | Equivalente | «Tiene alergia» / «es alérgico»; sin cambio relevante. |
| 25 | Equivalente | Ajuste natural de «a través de» a «por vía intravenosa». |
| 42 | Equivalente | Conserva transfusión, productos sanguíneos y permiso. |
| 43 | Equivalente | Cambia puntuación, conserva preocupación y pregunta. |
| 58 | Mixto | Corrige «hacerte/te sientes» a usted, pero produce «¿A veces se le falta de aliento?». |
| 70 | Equivalente | Sustituye «anticoagulante» por la paráfrasis del glosario. No prueba mayor precisión. |
| 72 | Equivalente | Conserva fibrilación auricular y prevención del coágulo. |
| 75 | Equivalente | Conserva prevención y destino cerebral; cambia el nombre del medicamento a una paráfrasis. |
| 79 | Equivalente | «Dificultad para respirar» / «falta de aliento»; negación intacta. |
| 82 | Equivalente | Ambas versiones interpretan literalmente «cámara del corazón»; no resuelve la ambigüedad. |
| 86 | Equivalente | Cambia términos de asistente y medicamento; conserva citas e instrucciones. |
| 90 | Mejora | «Light duty» deja de ser «turnos ligeros» y pasa a «tareas livianas»; conserva 10 libras y negación. |
| 91 | Idéntica | Copago y autorización previa ya eran correctos. |
| 92 | Equivalente | Paráfrasis de anticoagulante; mantiene frecuencia y no suspender sin llamar. |
| 94 | Equivalente | Mantiene primera persona, acidez y negaciones. |
| 99 | Empeora | «Heartburn» pasa a «acidity», aunque la referencia añadida era «dolor de pecho». Efecto fuera del término seleccionado. |
| 100 | Idéntica | Mantiene la pregunta de ayuno y seguimiento. |

Balance descriptivo: **14 equivalentes o idénticas, 1 mejora, 1 empeoramiento y
1 mixto**. No corresponde anunciar una mejora porcentual general con esta muestra.

## Ajuste tras el primer intento

El primer perfil admitía palabras aisladas. Se conservaron 72 casos procesados
en `resultados_glosario_inicial.json`; es una corrida parcial, no el resultado final.
Se encontraron estos problemas:

- Índice 40: `hold` indujo «retener el acto de firmar», peor que «posponer la firma».
- Índice 47: `bottom` cambió «parte inferior» por «parte trasera».
- Índice 42: copió literalmente «médico/a».

El perfil final solo envía expresiones completas de al menos dos palabras o
siglas exactas de 2–4 caracteres, y pide adaptar la gramática sin copiar barras.
Para `hold` y `bottom` vuelve a producir el prompt original. En el caso 42, el
nuevo resultado tampoco copia la barra. No se modificó el diccionario original.

Esta medida también descarta términos médicos válidos de una palabra: es un
compromiso deliberado de cobertura. No elimina todos los riesgos; el índice 99
muestra que agregar contexto todavía puede cambiar otras palabras.

## Límites y siguiente paso recomendado

- El glosario no contiene `mitral valve regurgitation`; no se aproxima a
  `mitral valve prolapse`, que es otro término. Ese diagnóstico no se beneficia
  de la incorporación actual.
- La transcripción incluye «y me quitó la comisión», una frase sospechosa de
  error de ASR. No se verificó exhaustivamente el audio contra una referencia
  humana, y este trabajo no intenta corregir Whisper mediante el glosario.
- El filtro se ajustó al encontrar errores en este mismo conjunto. Haría falta
  un conjunto independiente y revisión humana para afirmar generalización.
- El presupuesto de contexto es heurístico. En estos casos no hubo truncamiento;
  no es una garantía matemática para cualquier texto Unicode o cualquier modelo.
- Los resultados de calidad corresponden a Qwen3 8B; no se evaluó Gemma en este A/B.

Recomendación: mantener apagado para llamadas habituales. Si se quiere avanzar,
preparar una lista revisada de expresiones que el modelo traduce mal (como
`light duty`) y validarla con nuevas frases. Cambiar de modelo no forma parte
de esta propuesta.

## Archivos y reproducción

- `corpus_glosario.json`: textos, fuentes y tiempos de los fragmentos nuevos.
- `casos_glosario.json`: contrastes y criterios previos a las pruebas.
- `resultados_glosario.json`: los 102 casos; 34 inferencias medidas en 17 pares.
- `tokens_glosario.json`: tamaño real de las 17 referencias.
- `resultados_glosario_inicial.json`, `tokens_glosario_inicial.json`: evidencia exploratoria descartada.
- `comparar_glosario.py`: ejecución y reanudación con control de huellas.

```bash
python -B -m unittest discover -s tests -v
OLLAMA_HOST=127.0.0.1:11439 OLLAMA_VULKAN=1 ollama serve
# Otra terminal:
python -B bench/comparar_glosario.py --corpus bench/corpus_glosario.json --salida /tmp/nuevo-ab.json
```

El glosario se lee del archivo vivo. Si cambia, la nueva ejecución puede seleccionar
otras entradas; la huella permite detectar esa diferencia. No se incorpora al
repositorio una copia completa de los datos personales de Paso a Paso.
