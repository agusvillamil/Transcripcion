"""A/B local reproducible; no cambia modelos ni inicia servidores.

python -B bench/comparar_glosario.py --corpus corpus.json --salida resultados.json
El corpus es {"lineas": [{"texto": "...", "origen": "en", "grupo": "video"}]}.
Para reanudar, repetir el comando: valida la huella de código, corpus y glosario.
Solo genera dos veces si cambia el prompt; verifica igualdad en los demás casos.
"""
import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from frases import traduccion_fija
from glosario import Glosario
from traductor import Traductor


def main():
	p = argparse.ArgumentParser(description=__doc__)
	p.add_argument("--corpus", type=Path, required=True)
	p.add_argument("--salida", type=Path, required=True)
	p.add_argument("--url", default="http://127.0.0.1:11439")
	p.add_argument("--glosario", type=Path, default=config.GLOSARIO_RUTA)
	p.add_argument("--modelo", default=config.OLLAMA_MODELO)
	p.add_argument("--repeticiones", type=int, default=1)
	args = p.parse_args()
	if args.repeticiones < 1:
		p.error("repeticiones debe ser positivo")
	g = Glosario.cargar(args.glosario)
	if g.error or not g.indice:
		p.error(g.error or "glosario vacío")
	corpus = json.loads(args.corpus.read_text())
	base = Traductor(args.modelo, args.url)
	nuevo = Traductor(args.modelo, args.url, g)
	huella = hashlib.sha256(args.corpus.read_bytes() + args.glosario.read_bytes())
	for archivo in ("glosario.py", "traductor.py", "frases.py", "config.py", "bench/comparar_glosario.py"):
		huella.update((Path(__file__).resolve().parent.parent / archivo).read_bytes())
	meta = {"huella": huella.hexdigest(), "modelo": args.modelo, "contexto": config.OLLAMA_CONTEXTO,
		"repeticiones": args.repeticiones, "fuentes": corpus.get("fuentes", []), "entradas": g.cantidad}
	salida = {"meta": meta, "casos": []}
	if args.salida.exists():
		salida = json.loads(args.salida.read_text())
		if salida["meta"] != meta:
			p.error("el resultado pertenece a otra configuración/corpus; usar otra salida")
	base.precargar()
	print("GPU", base.en_gpu(), flush=True)
	for i, linea in enumerate(corpus["lineas"]):
		if i < len(salida["casos"]):
			continue
		texto, origen = linea["texto"], linea["origen"]
		destino = "es" if origen == "en" else "en"
		# Las frases sintéticas llevan sin_contexto=true para no inventar una conversación.
		contexto = [] if linea.get("sin_contexto") else [
			f'({l["origen"].upper()}) {l["texto"]}' for l in corpus["lineas"][max(0, i - 4):i]
			if l.get("grupo") == linea.get("grupo")]
		a, b = [t._mensajes(texto, origen, destino, contexto) for t in (base, nuevo)]
		fija = traduccion_fija(texto, origen)
		caso = {**linea, "indice": i, "contexto": contexto, "prompt_igual": a == b,
			"fija": fija, "referencia": b[0]["content"][len(a[0]["content"]):], "mediciones": []}
		if a != b and fija is None:
			for rep in range(args.repeticiones):
				for nombre in (("base", "glosario") if (i + rep) % 2 == 0 else ("glosario", "base")):
					# Igual prefijo calentado antes de cada variante. No dar ventaja al segundo.
					base.traducir("Please wait a moment.", "en", "es")
					t = base if nombre == "base" else nuevo
					tr = t.traducir(texto, origen, destino, contexto)
					caso["mediciones"].append({"modo": nombre, "repeticion": rep,
						"texto": tr.texto, "primer_token_s": tr.primer_token, "total_s": tr.total})
			s = " / ".join(f'{m["modo"]} {m["total_s"]:.2f}s' for m in caso["mediciones"])
		else:
			s = "fórmula fija" if fija else "prompt idéntico; sin inferencia duplicada"
		salida["casos"].append(caso)
		args.salida.parent.mkdir(parents=True, exist_ok=True)
		tmp = args.salida.with_suffix(".tmp")
		tmp.write_text(json.dumps(salida, ensure_ascii=False, indent=2))
		tmp.replace(args.salida)
		print(f'{i + 1}/{len(corpus["lineas"])} {linea.get("grupo", "")} {s}', flush=True)
	medidas = [m for c in salida["casos"] for m in c["mediciones"]]
	for modo in ("base", "glosario"):
		ms = [m for m in medidas if m["modo"] == modo]
		if ms:
			print(modo, "n", len(ms), "total", round(statistics.mean(m["total_s"] for m in ms), 3),
				"primer token", round(statistics.mean(m["primer_token_s"] for m in ms), 3))


if __name__ == "__main__":
	main()
