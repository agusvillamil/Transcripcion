"""Avisos sobre una línea ya traducida. No cambian ningún texto: solo señalan qué mirar dos veces.

`cifras_distintas` compara los números escritos con cifras a ambos lados de la traducción.
Es deliberadamente conservador, para no acostumbrar al ojo a ignorarlo:

- Un número con cifras se da por bueno si del otro lado está con cifras o con palabras
  ("2" ↔ "dos", "15" ↔ "quince", "1,000" ↔ "mil", "10/15" ↔ "15 de octubre").
- Los números que están en palabras de los dos lados no se comparan.
- Si lo único que cambia es cómo se agrupan los dígitos ("555 1234" ↔ "5551234",
  "twenty twenty-six" ↔ "2026", "8.30" ↔ "8:30"), no avisa. Un decimal sí: "2.5" no es "25".
"""
import re
import unicodedata
from collections import Counter

Tramo = tuple[int, int]  # posición [inicio, fin) dentro de un texto

_UNIDADES = {
	"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
	"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
	"ocho": 8, "nueve": 9,
}
# 10–19 (y 21–29 en español, que van en una sola palabra): solo pueden seguir a cientos o miles.
_CERRADOS = {
	"ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
	"seventeen": 17, "eighteen": 18, "nineteen": 19,
	"diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "dieciseis": 16,
	"diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veintiun": 21, "veintiuno": 21, "veintiuna": 21,
	"veintidos": 22, "veintitres": 23, "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26,
	"veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
}
_DECENAS = {
	"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
	"veinte": 20, "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70, "ochenta": 80,
	"noventa": 90,
}
_CIENTOS = {
	"cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300, "cuatrocientos": 400, "quinientos": 500,
	"seiscientos": 600, "setecientos": 700, "ochocientos": 800, "novecientos": 900,
}
_CIENTOS |= {k[:-2] + "as": v for k, v in _CIENTOS.items() if k.endswith("os")}
_MILES = {"thousand", "mil"}
# Otras formas de decir un número. Solo sirven para dar por bueno uno escrito con cifras.
_SUELTOS = {
	"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
	"ninth": 9, "tenth": 10,
	"primer": 1, "primero": 1, "primera": 1, "segundo": 2, "segunda": 2, "tercer": 3, "tercero": 3,
	"tercera": 3, "cuarto": 4, "cuarta": 4, "quinto": 5, "quinta": 5, "sexto": 6, "sexta": 6, "septimo": 7,
	"septima": 7, "octavo": 8, "octava": 8, "noveno": 9, "novena": 9, "decimo": 10, "decima": 10,
	"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7, "august": 8,
	"september": 9, "october": 10, "november": 11, "december": 12,
	"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
	"septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
	"half": 30, "media": 30, "quarter": 15,  # "2:30" ↔ "dos y media"; «cuarto» ya vale 4 (ordinal)
	"noon": 12, "midnight": 12, "mediodia": 12, "medianoche": 12,
	"zero": 0, "cero": 0,
}

_RE_CIFRA = re.compile(r"\d+(?:[.,]\d+)*")
_RE_GRUPO = re.compile(r"\d+")
_RE_HORA = re.compile(r"\d{1,2}[.,]\d{2}")
_RE_PALABRA = re.compile(r"[a-z]+")

Numero = tuple[float, Tramo]  # (valor, dónde está en el texto)


def cifras_distintas(original: str, traduccion: str) -> tuple[list[Tramo], list[Tramo]]:
	"""Números con cifras sin pareja del otro lado: (tramos del original, tramos de la traducción)."""
	if not _RE_CIFRA.search(original) and not _RE_CIFRA.search(traduccion):
		return [], []
	cifras_o, cifras_t = _cifras(original), _cifras(traduccion)
	palabras_o, palabras_t = _en_palabras(original), _en_palabras(traduccion)
	faltan, sobran = _comparar(cifras_o, palabras_o, cifras_t, palabras_t)
	# Los mismos dígitos en el mismo orden, agrupados distinto: "555 1234" ↔ "5551234", "1020" ↔ "10:20",
	# "twenty twenty-six" ↔ "2026". Un decimal conserva su punto: "2.5" no es "25".
	if (faltan or sobran) and (
		_digitos(cifras_o) == _digitos(cifras_t) or _digitos(cifras_o + palabras_o) == _digitos(cifras_t + palabras_t)
	):
		return [], []
	# "8.30" también puede ser una hora ("8:30", "30 minutos después de las 8"): se prueba leerlo como
	# dos números y queda la lectura que deja menos cifras sueltas.
	horas_o, horas_t = _cifras(original, horas=True), _cifras(traduccion, horas=True)
	for lectura_o, lectura_t in ((horas_o, cifras_t), (cifras_o, horas_t), (horas_o, horas_t)):
		otra = _comparar(lectura_o, palabras_o, lectura_t, palabras_t)
		if len(otra[0]) + len(otra[1]) < len(faltan) + len(sobran):
			faltan, sobran = otra
	return [tramo for _, tramo in faltan], [tramo for _, tramo in sobran]


def _comparar(cifras_o: list[Numero], palabras_o: list[Numero], cifras_t: list[Numero], palabras_t: list[Numero]):
	"""Cifras de cada lado que no están del otro, ni con cifras ni con palabras."""
	faltan = _sin_pareja(cifras_o, Counter(v for v, _ in cifras_t + palabras_t))
	sobran = _sin_pareja(cifras_t, Counter(v for v, _ in cifras_o + palabras_o))
	# El año dicho con dos cifras y escrito con cuatro: "94" ↔ "1994".
	for corto, largo in ((faltan, sobran), (sobran, faltan)):
		for numero in list(corto):
			pareja = next((n for n in largo if n[0] // 100 in (19, 20) and n[0] % 100 == numero[0]), None)
			if pareja:
				corto.remove(numero)
				largo.remove(pareja)
	return faltan, sobran


def _cifras(texto: str, horas: bool = False) -> list[Numero]:
	"""Números escritos con cifras. Los separadores se leen como en un número: "1,000" = "1.000" = 1000,
	"2.5" = "2,5" = 2.5 y "1,200.50" = "1.200,50" = 1200.5. Con `horas`, "8.30" son dos números: 8 y 30."""
	numeros: list[Numero] = []
	for m in _RE_CIFRA.finditer(texto):
		grupos = re.split(r"[.,]", m.group())
		if len(grupos) == 1 or all(len(g) == 3 for g in grupos[1:]):  # "12,000"
			numeros.append((int("".join(grupos)), m.span()))
		elif all(len(g) == 3 for g in grupos[1:-1]) and not (horas and _RE_HORA.fullmatch(m.group())):  # "2.5", "1,200.50"
			numeros.append((float("".join(grupos[:-1]) + "." + grupos[-1]), m.span()))
		else:  # una hora ("8.30") o una fecha ("10.15.2026"): cada grupo por su lado
			numeros += [(int(g.group()), (m.start() + g.start(), m.start() + g.end())) for g in _RE_GRUPO.finditer(m.group())]
	return numeros


def _sin_pareja(cifras: list[Numero], disponibles: Counter) -> list[Numero]:
	sueltas = []
	for valor, tramo in cifras:
		if valor == 0:
			continue  # "2:00" ↔ "las dos"
		if disponibles[valor] > 0:
			disponibles[valor] -= 1
		else:
			sueltas.append((valor, tramo))
	return sueltas


def _digitos(numeros: list[Numero]) -> str:
	"""Todos los dígitos en el orden en que se dicen, sin importar cómo estén agrupados."""
	return "".join(f"{valor:g}" if isinstance(valor, float) else str(valor) for valor, _ in sorted(numeros, key=lambda n: n[1]))


def _en_palabras(texto: str) -> list[Numero]:
	"""Números escritos con palabras, en inglés o en español: (valor, tramo).

	"treinta y cinco" → 35, "one hundred fifty" → 150, "two thousand five" → 2005. Dos números
	seguidos no se suman: "five five five" → 5, 5, 5.
	"""
	sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if not unicodedata.combining(c))
	numeros: list[Numero] = []
	miles = actual = inicio = fin = 0
	ultimo = ""  # qué fue la palabra anterior: u(nidad), c(errado), d(ecena), h (cientos), m(iles); "" = ninguna

	def cerrar() -> None:
		nonlocal miles, actual, ultimo
		if ultimo:
			numeros.append((miles + actual, (inicio, fin)))
		miles = actual = 0
		ultimo = ""

	for m in _RE_PALABRA.finditer(sin_tildes):
		palabra = m.group()
		if palabra in ("and", "y") and ultimo in ("d", "h"):
			continue  # "treinta y cinco", "one hundred and five"
		clase = (
			"u" if palabra in _UNIDADES else "c" if palabra in _CERRADOS else "d" if palabra in _DECENAS
			else "h" if palabra in _CIENTOS or palabra == "hundred" else "m" if palabra in _MILES else ""
		)
		# Sigue el número en curso solo si esta palabra puede ir detrás de la anterior.
		sigue = ultimo and {
			"u": ultimo in ("d", "h", "m"),
			"c": ultimo in ("h", "m"),
			"d": ultimo in ("h", "m"),
			"h": ultimo == "m" or (palabra == "hundred" and ultimo in ("u", "c", "d") and actual < 100),
			"m": True,
		}.get(clase, False)
		if not sigue:
			cerrar()
			inicio = m.start()
		fin = m.end()
		if clase == "u":
			actual += _UNIDADES[palabra]
		elif clase in ("c", "d"):
			actual += _CERRADOS.get(palabra) or _DECENAS[palabra]
		elif palabra == "hundred":
			actual = (actual or 1) * 100  # "two hundred", "fifteen hundred", "a hundred"
		elif clase == "h":
			actual += _CIENTOS[palabra]
		elif clase == "m":
			miles += (actual or 1) * 1000
			actual = 0
		elif palabra in _SUELTOS:
			numeros.append((_SUELTOS[palabra], m.span()))
		ultimo = clase
	cerrar()
	return numeros
