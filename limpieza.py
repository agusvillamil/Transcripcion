"""Limpia las notas de llamadas ya guardadas, sin perder nada.

Whisper inventa "Thank you." u "Okay." sobre el ruido de la línea y en el registro
quedan como turnos sueltos. Aquí cada racha de turnos de puro relleno se pliega en un
callout colapsado de Obsidian: la nota se lee limpia y el texto sigue ahí, a un clic.
También quita el "/no_think" que qwen3 a veces deja escapar en la traducción.

Antes de escribir se comprueba que la nota limpia contiene exactamente los mismos
turnos que la original; `--deshacer` la devuelve al formato en que se guardó.

Uso:
	python limpieza.py             # informa qué cambiaría, sin escribir
	python limpieza.py --aplicar   # reescribe las notas
	python limpieza.py --deshacer  # despliega el ruido de nuevo
"""
import argparse
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import config

# Palabras que, solas, no aportan a la llamada: muletillas y lo que Whisper alucina.
# "Sí", "No", "Yeah" y "Hello" quedan fuera a propósito: suelen ser respuestas reales.
_RELLENO = {
	"thank", "you", "thanks", "okay", "ok", "gracias",
	"oh", "uh", "um", "hmm", "hm", "mm", "mhm", "huh", "ah", "eh",
	"so", "and", "i", "y", "bye", "hey", "amen", "beep", "click",
}
_ANOTACION = re.compile(r"\*[^*]+\*|\[[^\]]+\]|\([^)]+\)")  # *crickets*, [music], (música)
_NO_THINK = re.compile(r"\s*/no_think\b")

_ENCABEZADO = re.compile(r"^### (\d\d:\d\d:\d\d) · (EN|ES) → (?:EN|ES)$")
_PLEGADO = re.compile(r"^> - (\d\d:\d\d:\d\d) (EN|ES) · (.*?) ⇒ ?(.*)$")
_CALLOUT = "> [!quote]- Ruido"
_CAMPO_RUIDO = "turnos_ruido:"
_DESTINO = {"EN": "ES", "ES": "EN"}


@dataclass(frozen=True)
class Turno:
	hora: str
	origen: str  # "EN" o "ES"
	original: str
	traduccion: str


def leer(texto: str) -> tuple[list[str], list[Turno]]:
	"""Separa la cabecera (frontmatter y título) de los turnos, estén plegados o no."""
	lineas = texto.split("\n")
	i = next((n for n, l in enumerate(lineas) if _ENCABEZADO.match(l) or l.startswith(_CALLOUT)), len(lineas))
	cabecera = [l for l in lineas[:i] if not l.startswith(_CAMPO_RUIDO)]
	turnos: list[Turno] = []
	while i < len(lineas):
		encabezado = _ENCABEZADO.match(lineas[i])
		if encabezado:
			original = lineas[i + 1].removeprefix(">").removeprefix(" ") if i + 1 < len(lineas) else ""
			# La traducción llega hasta el próximo turno: así una nota escrita a mano
			# debajo de un turno viaja con él en vez de perderse.
			fin = i + 3
			while fin < len(lineas) and not (_ENCABEZADO.match(lineas[fin]) or lineas[fin].startswith(_CALLOUT)):
				fin += 1
			traduccion = "\n".join(lineas[i + 3:fin]).rstrip("\n")
			turnos.append(Turno(encabezado[1], encabezado[2], original, traduccion))
			i = fin
		elif lineas[i].startswith(_CALLOUT):
			i += 1
			while i < len(lineas) and (plegado := _PLEGADO.match(lineas[i])):
				turnos.append(Turno(*plegado.groups()))
				i += 1
		else:
			i += 1  # línea en blanco entre bloques
	return cabecera, turnos


def es_ruido(turno: Turno) -> bool:
	if "\n" in turno.traduccion or "⇒" in turno.original:
		return False  # no cabría en una línea del callout
	if config.ETIQUETA_REPASAR in turno.traduccion:
		return False  # marcado para repasar: tiene que quedar a la vista
	palabras = re.findall(r"[a-záéíóúñü0-9]+", _ANOTACION.sub(" ", turno.original.lower()))
	return all(p in _RELLENO for p in palabras)


def escribir(cabecera: list[str], turnos: list[Turno], plegar: bool) -> str:
	"""Arma la nota; con `plegar=False` queda igual que la que guarda la aplicación."""
	cuerpo: list[str] = []
	racha: list[Turno] = []

	def cerrar_racha() -> None:
		if racha:
			plural = "s" if len(racha) > 1 else ""
			horas = racha[0].hora if len(racha) == 1 else f"{racha[0].hora}–{racha[-1].hora}"
			cuerpo.append(f"{_CALLOUT} · {len(racha)} turno{plural} · {horas}")
			cuerpo.extend(f"> - {t.hora} {t.origen} · {t.original} ⇒ {t.traduccion}".rstrip() for t in racha)
			cuerpo.append("")
			racha.clear()

	for t in turnos:
		if plegar and es_ruido(t):
			racha.append(t)
			continue
		cerrar_racha()
		cuerpo += [f"### {t.hora} · {t.origen} → {_DESTINO[t.origen]}", f"> {t.original}", "", t.traduccion, ""]
	cerrar_racha()
	if plegar:
		ruido = sum(es_ruido(t) for t in turnos)
		cabecera = [c for l in cabecera for c in ([l, f"{_CAMPO_RUIDO} {ruido}"] if l.startswith("turnos:") else [l])]
	return "\n".join(cabecera + cuerpo)


def limpiar(texto: str) -> str:
	"""Devuelve la nota con el ruido plegado. Falla antes que perder un turno."""
	cabecera, turnos = leer(texto)
	turnos = [replace(t, traduccion=_NO_THINK.sub("", t.traduccion).strip()) for t in turnos]
	limpia = escribir(cabecera, turnos, plegar=True)
	if leer(limpia) != (cabecera, turnos):
		raise ValueError("la nota limpia no conserva todos los turnos; no se toca")
	return limpia


def desplegar(texto: str) -> str:
	return escribir(*leer(texto), plegar=False)


def main() -> None:
	analizador = argparse.ArgumentParser(description="Pliega el ruido de las llamadas guardadas, sin perder nada.")
	analizador.add_argument("notas", nargs="*", type=Path, help="notas a procesar (por defecto, toda la bóveda)")
	modo = analizador.add_mutually_exclusive_group()
	modo.add_argument("--aplicar", action="store_true", help="reescribe las notas (sin esto solo informa)")
	modo.add_argument("--deshacer", action="store_true", help="despliega el ruido de nuevo")
	args = analizador.parse_args()

	notas = args.notas or sorted(config.SESIONES_DIR.glob("*.md"))
	total = total_ruido = 0
	for ruta in notas:
		texto = ruta.read_text(encoding="utf-8")
		try:
			nueva = desplegar(texto) if args.deshacer else limpiar(texto)
		except ValueError as e:
			print(f"{ruta.name}: {e}", file=sys.stderr)
			continue
		turnos = leer(nueva)[1]
		ruido = sum(es_ruido(t) for t in turnos)
		total += len(turnos)
		total_ruido += ruido
		estado = "sin cambios" if nueva == texto else "reescrita" if args.aplicar or args.deshacer else "cambiaría"
		print(f"{ruta.name:28} {len(turnos):4} turnos · {ruido:3} de ruido · {estado}")
		if nueva != texto and (args.aplicar or args.deshacer):
			ruta.write_text(nueva, encoding="utf-8")
	if total:
		print(f"{'Total':28} {total:4} turnos · {total_ruido:3} de ruido ({100 * total_ruido // total}%)")


if __name__ == "__main__":
	main()
