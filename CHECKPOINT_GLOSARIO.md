# Checkpoint: glosario de Paso a Paso

Actualizado: 2026-10-29. **Implementación y evaluación completadas.**

## Solicitud y restricciones

Integrar un glosario opcional y comprobar si mejora la interpretación, manteniendo
los modelos existentes. No escribir en Paso a Paso. No agregar autoría ni coautoría
de IA a los commits. Mantener el estado previo recuperable fuera de main.

## Git

- Rama: `codex/glosario-paso-a-paso`.
- Respaldo previo completo: `fd5c1e1`, incluye cambios preexistentes y pycache.
- `main` permanece en `b84a96a`; no se hizo push ni merge.
- Identidad Git existente de Agustin Villamil, sin coautores.
- Implementación y pruebas en un commit posterior; consultar `git log -3`.

## Estado final

- `glosario.py`: índice en memoria, solo lectura de `datos.glosario` en
  `/home/kindue/Proyectos/Paso a paso/datos.json` (3698 entradas en la prueba).
- `traductor.py`: referencia opcional, sin alterar las reglas existentes.
- `app.py`: botón apagado por defecto, bloqueado durante captura/tareas pendientes.
  Recarga entre llamadas; si falla el archivo, vuelve al modo habitual.
- Perfil final: expresiones de al menos dos palabras y siglas exactas; hasta tres
  entradas y 150 tokens estimados. Omite palabras aisladas por ambigüedad.
- Los 102 prompts apagados se verificaron idénticos al código de `fd5c1e1`.
- Pasaron 19 pruebas automatizadas, incluidas pruebas Qt sin micrófono ni modelos.
- Captura de interfaz inspeccionada en 1200×820, sin cortes del nuevo botón.

## Evidencia y conclusión

Leer `bench/reporte_glosario.md`. El corpus incluye 55 frases anteriores,
35 fragmentos del video solicitado y 12 casos sintéticos. Solo 17 prompts cambian;
se hicieron 34 inferencias medidas (una por variante/caso). Los otros 85 conservan
el pedido o la fórmula fija. No confundir 102 casos con 102 pares generados.

Resultado: 14 equivalentes/idénticos, 1 mejora (light duty), 1 empeoramiento
(heartburn → acidity) y 1 mixto (usted correcto, gramática peor). No se demostró
mejora general. **Se recomienda mantener desactivado para llamadas habituales.**
Demora adicional media con referencia: +0,247 s; primer token +0,253 s.
No incluye ASR ni cola en vivo. No hubo revisión clínica humana independiente.

El intento inicial con palabras aisladas es parcial (72/102), guardado en
`bench/resultados_glosario_inicial.json`. Sus regresiones motivaron el filtro.
El resultado final completo es `bench/resultados_glosario.json`; las huellas
se verificaron contra el código y los datos actuales.

## Continuar

No quedan tareas necesarias para este pedido. Un próximo trabajo podría preparar
una lista de expresiones revisadas y validarla con un conjunto independiente y
revisión humana. No activar automáticamente ni prometer que más términos mejoran
la calidad. Los comandos están en README y el informe.

El benchmark guarda un checkpoint después de cada caso. Repetir el mismo comando
reanuda si coinciden las huellas. Si cambian código o glosario, usar salida nueva.
Usar `python -B` para no alterar los pycache del respaldo.

El servidor temporal Ollama (puerto 11439, grupo 57639) ya se detuvo. Whisper
temporal también se detuvo. No hay benchmarks pendientes.
Audio temporal: `/tmp/transcripcion-glosario-bench/lj1ObXJKDgA.webm`.
Fuente: https://www.youtube.com/watch?v=lj1ObXJKDgA
La transcripción está en `bench/corpus_glosario.json`.
