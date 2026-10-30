"""A/B de config.USTED_RECORDATORIO sobre corpus ya transcritos; no inicia servidores.

python -B bench/comparar_usted.py --corpus bench/corpus_playlist.json bench/corpus_glosario.json --salida /tmp/usted.json
Solo infiere las frases al español (las otras conservan el pedido; se verifica). Reanuda si se repite.
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from frases import traduccion_fija
from traductor import Traductor

# Formas de «tú»/«ustedes» que aparecieron en las pruebas; solo para contar, no es un detector completo.
TUTEO = re.compile(r"\b(tú|te|ti|tu|tus|contigo|puedes|tienes|estás|eres|quieres|sientes|vas|duermes|escuchas|"
	r"pudiste|desmayaste|tomabas|cuéntame|torturarte|hacerte|acostumbras|puedas|ustedes|tengan|puedan)\b", re.I)


def main():
	p = argparse.ArgumentParser(description=__doc__)
	p.add_argument("--corpus", type=Path, nargs="+", required=True)
	p.add_argument("--salida", type=Path, required=True)
	p.add_argument("--url", default="http://127.0.0.1:11439")
	args = p.parse_args()
	lineas = []
	for ruta in args.corpus:
		for l in json.loads(ruta.read_text())["lineas"]:
			lineas.append({**l, "corpus": ruta.name})
	t = Traductor(config.OLLAMA_MODELO, args.url)
	salida = json.loads(args.salida.read_text()) if args.salida.exists() else {"casos": []}
	t.precargar()
	print("GPU", t.en_gpu(), flush=True)
	for i, l in enumerate(lineas):
		if i < len(salida["casos"]):
			continue
		texto, origen = l["texto"], l["origen"]
		destino = "es" if origen == "en" else "en"
		previas = [x for x in lineas[max(0, i - 4):i] if x["corpus"] == l["corpus"] and x.get("grupo") == l.get("grupo")]
		contexto = [] if l.get("sin_contexto") else [f'({x["origen"].upper()}) {x["texto"]}' for x in previas]
		prompts = {}
		for modo in (False, True):
			config.USTED_RECORDATORIO = modo
			prompts[modo] = t._mensajes(texto, origen, destino, contexto)
		caso = {**l, "indice": i, "fija": traduccion_fija(texto, origen), "mediciones": []}
		if destino != "es":
			assert prompts[False] == prompts[True], i  # la otra dirección no cambia
		elif caso["fija"] is None:
			for modo in ((False, True) if i % 2 == 0 else (True, False)):
				config.USTED_RECORDATORIO = modo
				t.traducir("Please wait a moment.", "en", "es")  # mismo prefijo calentado antes de cada variante
				tr = t.traducir(texto, origen, destino, contexto)
				caso["mediciones"].append({"recordatorio": modo, "texto": tr.texto,
					"primer_token_s": tr.primer_token, "total_s": tr.total})
		salida["casos"].append(caso)
		tmp = args.salida.with_suffix(".tmp")
		tmp.write_text(json.dumps(salida, ensure_ascii=False, indent=1))
		tmp.replace(args.salida)
		print(f"{i + 1}/{len(lineas)} {l.get('grupo', '')} {len(caso['mediciones'])}", flush=True)
	pares = [c for c in salida["casos"] if c["mediciones"]]
	for modo in (False, True):
		ms = [m for c in pares for m in c["mediciones"] if m["recordatorio"] == modo]
		print("recordatorio", modo, "frases", len(ms), "con tuteo", sum(bool(TUTEO.search(m["texto"])) for m in ms),
			"total", round(statistics.mean(m["total_s"] for m in ms), 3),
			"primer token", round(statistics.mean(m["primer_token_s"] for m in ms), 3))


if __name__ == "__main__":
	main()
