"""Arma la nota de repaso a partir de las llamadas guardadas.

Lee las notas de la bóveda sin modificarlas y escribe una sola nota (`config.REPASO_NOTA`) con:
  - llamadas y tiempo por semana y por día, para cruzar con el contador de horas;
  - los turnos marcados con «☆ Repasar» en la app (llevan `#repasar` debajo de la traducción);
  - los términos que más se repiten entre llamadas: un conteo simple de palabras, sirve de
    lista aproximada para armar un glosario.

La nota se reescribe entera cada vez. Para sacar un turno de la lista se borra su `#repasar`
en la nota de la llamada; para sumar uno, se escribe `#repasar` debajo de su traducción.

Uso:
	python repaso.py                # escribe la nota en la bóveda
	python repaso.py --salida x.md  # la escribe en otro lado, para mirarla antes
"""
import argparse
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import config
import limpieza

DIAS_MOSTRADOS = 30   # días con llamadas que entran en la tabla «Por día»
MIN_LLAMADAS = 2      # un término cuenta si aparece en al menos estas llamadas (deja afuera nombres propios)
MAX_PALABRAS = 40
MAX_FRASES = 25

_MARCA = "Nota generada por `repaso.py`"  # sin esto, una nota existente no se pisa
_ETIQUETA = re.compile(rf"\s*{re.escape(config.ETIQUETA_REPASAR)}\b")
_DIAS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")
_IDIOMAS = {"EN": "Inglés", "ES": "Español"}
_NEXOS = {"de", "del", "of"}  # unen dos palabras en un término: "fecha de nacimiento", "date of birth"

# Palabras que no son terminología (sin tildes: se comparan así).
_VACIAS = {
	"EN": set("""
		a about after again all also always am an and any anything are as ask at back be because been before being
		bit but by bye call called can come could day did do does doing done down each else even ever every
		everything few fine first for from get give go going gonna good got great had has have having he hello help
		her here hey hi him his hmm how i if in into is it its just kind know last let like little look lot ma'am
		made make many may maybe me mean mhm might miss more most much must my need never new next no not nothing
		now of off oh ok okay on once one only or other our out over own please put really right said same say see
		she should sir so some something sorry still such sure take talk tell than thank thanks that the their them
		then there these they thing things think this those through time to today too try two uh um under until up
		us use very wait want was way we well went were what when where which while who why will with would yeah
		yes yet you your yours
		able actually ahead already alright getting moment perfect probably second trying yourself
		three four five six seven eight nine ten eleven twelve twenty thirty forty fifty sixty seventy eighty ninety
		hundred thousand zero
	""".split()),
	"ES": set("""
		a aca aqui ahi alla alli ah aha aja al algo alguien algun alguna alguno algunos ante antes asi aun aunque
		bien buen buena buenas bueno buenos cada casi claro como con contra cosa cosas cual cuales cuando cuanto
		da dar de debe decir del desde despues dice dicho dijo doctor doctora donde dos durante eh el ella ellas
		ellos en entiendo entonces entre era eran eres es esa esas ese eso esos esta estaba estan estar estas este
		esto estos estoy favor fue fueron gracias ha habia hace hacer han has hasta hay he hizo hola hoy igual ir
		la las le les lo los luego mas me mi mientras mis mismo mm momento mucha muchas mucho muchos muy nada ni
		ningun ninguna ninguno no nos nosotros nunca o ok okay otra otras otro otros para pero poco podria por
		porque puede pueden puedo pues que quien quiere quiero sabe se sea segun senor senora senorita ser si
		siempre sin sobre solo son soy su sus tal tambien tan tanto te tenemos tener tenga tengo tenia ti tiene
		tienen toda todas todavia todo todos tu tus un una unas uno unos usted ustedes va vale vamos van ver vez voy
		y ya yo
		ahora ahorita correcto creo dieron dijeron fui hecho hicieron mal mejor pasa poner queria saber solamente tenido
		unico verdad
		tres cuatro cinco seis siete ocho nueve diez once doce veinte treinta cuarenta cincuenta sesenta setenta
		ochenta noventa cien ciento mil cero
	""".split()),
}


@dataclass(frozen=True)
class Llamada:
	nota: str      # nombre de la nota, sin ".md"
	fecha: date
	inicio: str    # "HH:MM"
	minutos: int
	turnos: tuple[limpieza.Turno, ...]


def leer_llamadas(carpeta: Path) -> list[Llamada]:
	llamadas = []
	for ruta in sorted(carpeta.glob("*.md")):
		cabecera, turnos = limpieza.leer(ruta.read_text(encoding="utf-8"))
		props = {m[1]: m[2].strip().strip('"') for l in cabecera if (m := re.match(r"^(\w+):\s*(.*)$", l))}
		try:
			llamada = Llamada(ruta.stem, date.fromisoformat(props["fecha"]), props.get("inicio", ""),
							  int(props["duracion_min"]), tuple(turnos))
		except (KeyError, ValueError):
			print(f"{ruta.name}: sin fecha o duración en las propiedades; no entra en el repaso", file=sys.stderr)
			continue
		llamadas.append(llamada)
	return sorted(llamadas, key=lambda l: (l.fecha, l.inicio))


def _tiempo(minutos: int) -> str:
	horas, resto = divmod(minutos, 60)
	return f"{horas} h {resto:02d} min" if horas else f"{resto} min"


def _tabla(titulo: str, grupos: dict[str, list[Llamada]]) -> list[str]:
	filas = [f"| {titulo} | Llamadas | Tiempo |", "|---|---|---|"]
	filas += [f"| {clave} | {len(ls)} | {_tiempo(sum(l.minutos for l in ls))} |" for clave, ls in grupos.items()]
	return filas + [""]


def horas(llamadas: list[Llamada]) -> list[str]:
	"""Llamadas y tiempo por semana y por día, lo más reciente arriba."""
	semanas: dict[str, list[Llamada]] = {}
	dias: dict[str, list[Llamada]] = {}
	for l in reversed(llamadas):
		lunes = l.fecha - timedelta(days=l.fecha.weekday())
		semanas.setdefault(f"{lunes:%d-%m-%Y}", []).append(l)
		dias.setdefault(f"{_DIAS[l.fecha.weekday()]} {l.fecha:%d-%m-%Y}", []).append(l)
	total = sum(l.minutos for l in llamadas)
	salida = [
		"## Horas", "",
		f"**Total:** {len(llamadas)} llamadas · {_tiempo(total)} · {_tiempo(round(total / len(llamadas)))} por llamada",
		"",
		"La duración va del primer al último turno de cada nota, redondeada al minuto de arriba.", "",
		"### Por semana", "",
		*_tabla("Semana del lunes", semanas),
		f"### Por día (últimos {DIAS_MOSTRADOS} con llamadas)", "",
		*_tabla("Día", dict(list(dias.items())[:DIAS_MOSTRADOS])),
	]
	return salida


def para_repasar(llamadas: list[Llamada]) -> list[str]:
	"""Los turnos con la etiqueta, agrupados por llamada, la más reciente arriba."""
	bloques: list[str] = []
	cantidad = 0
	for l in reversed(llamadas):
		marcados = [t for t in l.turnos if _ETIQUETA.search(t.traduccion)]
		if not marcados:
			continue
		cantidad += len(marcados)
		bloques += [f"### [[{l.nota}]]", ""]
		for t in marcados:
			# Sin la etiqueta: si quedara acá, la búsqueda de #repasar en Obsidian mostraría todo dos veces.
			traduccion = _ETIQUETA.sub("", t.traduccion).strip()
			bloques += [f"**{t.hora} · {t.origen} → {'ES' if t.origen == 'EN' else 'EN'}**", f"> {t.original}", "",
						traduccion, ""]
	if not bloques:
		bloques = ["Todavía no hay turnos marcados. En la app, «☆ Repasar» en una tarjeta marca ese turno;",
				   f"también se puede escribir `{config.ETIQUETA_REPASAR}` debajo de una traducción ya guardada.", ""]
	return [f"## Para repasar ({cantidad})", "", *bloques]


def _sin_tildes(texto: str) -> str:
	return "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c))


def _terminos(texto: str, idioma: str) -> tuple[set[str], list[str], list[str]]:
	"""Palabras y frases de dos palabras (o unidas por "de"/"of") que no son relleno."""
	vacias = _VACIAS[idioma]
	palabras, frases = [], []
	for tramo in re.split(r"[.?!,;:¿¡()\"“”…—]+", re.sub(r"['’]s\b", "", texto.lower())):
		fichas = re.findall(r"[a-záéíóúñü]+(?:[-'’][a-záéíóúñü]+)*", tramo)  # "follow-up" es una sola palabra
		utiles = [len(f) > 2 and "'" not in f and "’" not in f and _sin_tildes(f) not in vacias for f in fichas]
		for i, ficha in enumerate(fichas):
			if not utiles[i]:
				continue
			palabras.append(ficha)
			if i + 1 < len(fichas) and utiles[i + 1]:
				frases.append(f"{ficha} {fichas[i + 1]}")
			elif i + 2 < len(fichas) and fichas[i + 1] in _NEXOS and utiles[i + 2]:
				frases.append(f"{ficha} {fichas[i + 1]} {fichas[i + 2]}")
	return set(palabras) | set(frases), palabras, frases


def terminos(llamadas: list[Llamada]) -> list[str]:
	salida = [
		"## Términos frecuentes", "",
		f"Conteo simple de lo que se dijo en cada idioma, sin el ruido. Entran los términos que aparecen en "
		f"{MIN_LLAMADAS} llamadas o más, ordenados por cantidad de llamadas. Es una lista aproximada: sirve para "
		"elegir qué anotar en un glosario, no reemplaza leer las llamadas.", "",
	]
	for idioma, nombre in _IDIOMAS.items():
		en_llamadas: Counter[str] = Counter()
		veces_palabras: Counter[str] = Counter()
		veces_frases: Counter[str] = Counter()
		for l in llamadas:
			vistos: set[str] = set()
			for t in l.turnos:
				if t.origen != idioma or limpieza.es_ruido(t):
					continue
				unicos, palabras, frases = _terminos(t.original, idioma)
				vistos |= unicos
				veces_palabras.update(palabras)
				veces_frases.update(frases)
			en_llamadas.update(vistos)
		for titulo, veces, maximo in (("palabras", veces_palabras, MAX_PALABRAS), ("frases", veces_frases, MAX_FRASES)):
			filas = sorted(((en_llamadas[t], n, t) for t, n in veces.items() if en_llamadas[t] >= MIN_LLAMADAS),
						   key=lambda f: (-f[0], -f[1], f[2]))[:maximo]
			salida += [f"### {nombre}: {titulo}", ""]
			if not filas:
				salida += ["Todavía no hay términos repetidos entre llamadas.", ""]
				continue
			salida += ["| Término | Llamadas | Veces |", "|---|---|---|"]
			salida += [f"| {t} | {n_llamadas} | {n} |" for n_llamadas, n, t in filas]
			salida.append("")
	return salida


def armar(llamadas: list[Llamada], ahora: datetime) -> str:
	return "\n".join([
		"---",
		f'generado: "{ahora:%Y-%m-%d %H:%M}"',
		"tags: [repaso]",
		"---",
		"# Repaso de llamadas",
		"",
		f"> {_MARCA}: se reescribe entera cada vez, no la edites. Para sacar un turno de «Para repasar»,",
		f"> borrá su `{config.ETIQUETA_REPASAR}` en la nota de la llamada.",
		"",
		*horas(llamadas),
		*para_repasar(llamadas),
		*terminos(llamadas),
	])


def main() -> None:
	analizador = argparse.ArgumentParser(description="Arma la nota de repaso con las llamadas guardadas.")
	analizador.add_argument("--salida", type=Path, default=config.REPASO_NOTA, help="dónde escribir la nota")
	args = analizador.parse_args()

	llamadas = leer_llamadas(config.SESIONES_DIR)
	if not llamadas:
		sys.exit(f"No hay llamadas guardadas en {config.SESIONES_DIR}")
	if args.salida.exists() and _MARCA not in args.salida.read_text(encoding="utf-8"):
		sys.exit(f"{args.salida} ya existe y no la generó este script: no se toca. Usá --salida con otro nombre.")
	args.salida.write_text(armar(llamadas, datetime.now()), encoding="utf-8")
	marcados = sum(bool(_ETIQUETA.search(t.traduccion)) for l in llamadas for t in l.turnos)
	print(f"{args.salida}: {len(llamadas)} llamadas · {_tiempo(sum(l.minutos for l in llamadas))} · "
		  f"{marcados} turnos para repasar")


if __name__ == "__main__":
	main()
