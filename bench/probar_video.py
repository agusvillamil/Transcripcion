"""Prueba la cadena completa sobre un archivo de audio y genera un reporte.

Uso:
  python3 bench/probar_video.py audio.wav --llm gemma3:4b qwen3:8b --salida reporte.md
  python3 bench/probar_video.py audio.wav --realtime   # simula tiempo real (latencia de punta a punta)

El audio se transcribe una sola vez; cada modelo LLM traduce las mismas líneas.
"""
import argparse
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from asr import ServidorWhisper  # noqa: E402
from segmentador import Segmentador  # noqa: E402
from sesion import CONTEXTO_LINEAS, Callbacks, Sesion  # noqa: E402
from traductor import Traductor  # noqa: E402


def cargar_audio(ruta: str) -> np.ndarray:
	crudo = subprocess.run(
		["ffmpeg", "-loglevel", "error", "-i", ruta, "-f", "f32le", "-ac", "1", "-ar", str(config.FRECUENCIA), "-"],
		capture_output=True, check=True,
	).stdout
	return np.frombuffer(crudo, dtype=np.float32)


def main() -> None:
	p = argparse.ArgumentParser()
	p.add_argument("audio")
	p.add_argument("--llm", nargs="+", default=[config.OLLAMA_MODELO])
	p.add_argument("--whisper-model", default=config.WHISPER_MODELO)
	p.add_argument("--realtime", action="store_true")
	p.add_argument("--salida", default="reporte.md")
	args = p.parse_args()

	audio = cargar_audio(args.audio)
	asr = ServidorWhisper(args.whisper_model)
	print("Iniciando whisper-server…", flush=True)
	asr.iniciar()
	traductor = Traductor(args.llm[0])
	traductor.asegurar_servidor()
	print(f"Whisper en GPU: {asr.usa_gpu}. Cargando {args.llm[0]}…", flush=True)
	traductor.precargar()

	cb = Callbacks(
		linea_nueva=lambda l: print(f"[{l.origen}] {l.original}", flush=True),
		linea_traducida=lambda l: print(f"   → {l.traduccion}  (asr {l.t_asr:.1f}s, llm {l.t_traduccion:.1f}s)", flush=True),
		error=lambda e: print("ERROR", e, flush=True),
	)
	sesion = Sesion(asr, traductor, cb)
	seg = Segmentador()
	bloque = config.FRECUENCIA // 10
	t0 = time.time()
	for i in range(0, len(audio), bloque):
		if args.realtime:
			espera = t0 + i / config.FRECUENCIA - time.time()
			if espera > 0:
				time.sleep(espera)
		for f in seg.procesar(audio[i:i + bloque]):
			sesion.agregar(f, t_fin_habla=time.time())
	for f in seg.vaciar():
		sesion.agregar(f)
	sesion.esperar()
	lineas = sesion.lineas
	resultados = {args.llm[0]: [(l.traduccion, l.t_primer_token, l.t_traduccion) for l in lineas]}
	gpu = {args.llm[0]: traductor.en_gpu()}

	for modelo in args.llm[1:]:
		traductor.liberar()
		traductor.modelo = modelo
		print(f"\n=== {modelo}", flush=True)
		traductor.precargar()
		gpu[modelo] = traductor.en_gpu()
		filas = []
		for l in lineas:
			contexto = [f"({x.origen.upper()}) {x.original}" for x in lineas[max(0, l.id - CONTEXTO_LINEAS):l.id]]
			tr = traductor.traducir(l.original, l.origen, l.destino, contexto)
			print(f"[{l.origen}] {tr.texto}  ({tr.total:.1f}s)", flush=True)
			filas.append((tr.texto, tr.primer_token, tr.total))
		resultados[modelo] = filas

	sesion.cerrar()
	asr.detener()
	escribir_reporte(args, lineas, resultados, gpu)
	print(f"\nReporte: {args.salida}")


def escribir_reporte(args, lineas, resultados, gpu) -> None:
	t_asr = [l.t_asr for l in lineas]
	out = [f"# Reporte: {Path(args.audio).name}", ""]
	out.append(f"- Whisper: `{args.whisper_model}` — {len(lineas)} líneas, ASR media {statistics.mean(t_asr):.2f}s, "
			   f"máx {max(t_asr):.2f}s")
	if args.realtime:
		lat = [l.t_listo - l.t_fin_habla for l in lineas if l.t_listo]
		out.append(f"- Latencia fin de habla → traducción completa: media {statistics.mean(lat):.2f}s, "
				   f"máx {max(lat):.2f}s")
	out += ["", "| Modelo | 1er token (media) | Traducción (media) | Traducción (máx) | En GPU |", "|---|---|---|---|---|"]
	for modelo, filas in resultados.items():
		pt = [f[1] for f in filas]
		tt = [f[2] for f in filas]
		frac = gpu.get(modelo)
		out.append(f"| {modelo} | {statistics.mean(pt):.2f}s | {statistics.mean(tt):.2f}s | {max(tt):.2f}s | "
				   f"{'?' if frac is None else f'{frac:.0%}'} |")
	out += ["", "## Líneas", ""]
	for l in lineas:
		out.append(f"### {l.id} · {l.inicio:.1f}s · {l.origen.upper()}→{l.destino.upper()}")
		out.append(f"**Original:** {l.original}  ")
		for modelo, filas in resultados.items():
			out.append(f"**{modelo}:** {filas[l.id][0]}  ")
		out.append("")
	Path(args.salida).write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
	main()
