"""Índice local de Paso a Paso. Solo lectura; una instantánea por llamada."""
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import config

_AVISO = (
	"\n\nTerminology hints, only if appropriate here. Choose one natural equivalent, "
	"adapt its grammar; never copy slashes or add information:\n"
)


def _palabras(texto: str) -> tuple[str, ...]:
	# Conserva tildes: «año» y «ano» no son equivalentes.
	return tuple(re.findall(r"\w+", unicodedata.normalize("NFKC", texto).casefold()))


def estimar_tokens(texto: str) -> int:
	"""Margen deliberadamente amplio para EN/ES; no es un tokenizador exacto."""
	return math.ceil(len(texto.encode("utf-8")) / 2)


@dataclass(frozen=True)
class Coincidencia:
	original: str
	equivalente: str

	@property
	def linea(self) -> str:
		# JSON delimita los datos y escapa controles; nunca se incorporan notas.
		return json.dumps([self.original, self.equivalente], ensure_ascii=False)


class Glosario:
	def __init__(self) -> None:
		self.indice: dict[tuple[str, tuple[str, ...]], Coincidencia] = {}
		self.cantidad = 0
		self.error = ""
		self._max_palabras = 1

	@classmethod
	def cargar(cls, ruta: Path) -> "Glosario":
		g = cls()
		try:
			# Evita cargar accidentalmente un archivo enorme o una estructura ajena.
			with ruta.open("rb") as archivo:
				crudo = archivo.read(10_000_001)
			if len(crudo) > 10_000_000:
				raise ValueError("el archivo supera 10 MB")
			datos = json.loads(crudo)
			entradas = datos["datos"]["glosario"]
			if not isinstance(entradas, list):
				raise ValueError("glosario no es una lista")
			ambiguas = set()
			for e in entradas:
				if not isinstance(e, dict) or not all(isinstance(e.get(k), str) and e[k].strip() for k in ("en", "es")):
					continue
				if any(len(e[k]) > 300 or any(ord(c) < 32 for c in e[k]) for k in ("en", "es")):
					continue
				g.cantidad += 1
				for idioma, destino in (("en", "es"), ("es", "en")):
					# Solo variantes explícitas. No quitar calificadores entre paréntesis.
					for alias in re.split(r"\s+/\s+", e[idioma].strip()):
						palabras = _palabras(alias)
						if not palabras or len(palabras) > 12:
							continue
						clave = (idioma, palabras)
						coincidencia = Coincidencia(alias, e[destino].strip())
						previa = g.indice.get(clave)
						if previa and _palabras(previa.equivalente) != _palabras(coincidencia.equivalente):
							ambiguas.add(clave)
						g.indice[clave] = coincidencia
						g._max_palabras = max(g._max_palabras, len(palabras))
			for clave in ambiguas:
				g.indice.pop(clave, None)
		except (OSError, ValueError, KeyError, TypeError, RecursionError) as e:
			g = cls()
			g.error = f"No se pudo cargar el glosario: {e}"
		return g

	def buscar(self, texto: str, idioma: str) -> list[Coincidencia]:
		candidatas = []
		for tramo_id, tramo in enumerate(re.split(r"[.!?;:\n]", texto)):
			palabras = _palabras(tramo)
			for i in range(len(palabras)):
				for largo in range(min(self._max_palabras, len(palabras) - i), 0, -1):
					if c := self.indice.get((idioma, palabras[i:i + largo])):
						# Siglas cortas: «US» no debe coincidir con el pronombre «us».
						if c.original.isupper() and len(c.original) <= 4 and not re.search(r"(?<!\w)" + re.escape(c.original) + r"(?!\w)", tramo):
							continue
						candidatas.append((-largo, tramo_id, i, c))
		usados, vistas, resultado = set(), set(), []
		for negativo, tramo, inicio, c in sorted(candidatas, key=lambda x: x[:3]):
			posiciones = {(tramo, n) for n in range(inicio, inicio - negativo)}
			if usados & posiciones or c in vistas:
				continue
			usados.update(posiciones)
			vistas.add(c)
			resultado.append(c)
		return resultado

	def referencia(self, texto: str, idioma: str, prompt_actual: str) -> str:
		if config.GLOSARIO_MAX_ENTRADAS <= 0 or config.GLOSARIO_MAX_TOKENS <= 0:
			return ""
		bloque = ""
		for c in self.buscar(texto, idioma):
			# Una palabra aislada puede tener otro sentido (bottom, hold, benefits).
			# Perfil conservador: expresiones completas o siglas exactas, no vocablos
			# sueltos. La regla se aplica también a cada alias de una entrada.
			if len(_palabras(c.original)) < 2 and not (c.original.isupper() and 2 <= len(c.original) <= 4):
				continue
			candidato = (bloque + "\n" + c.linea) if bloque else (_AVISO + c.linea)
			if estimar_tokens(candidato) > config.GLOSARIO_MAX_TOKENS:
				continue
			# No recortar reglas ni conversación para hacer lugar al glosario.
			# Reserva para salida + plantilla de chat y error de estimación.
			if estimar_tokens(prompt_actual + candidato) + 640 > config.OLLAMA_CONTEXTO:
				continue
			bloque = candidato
			if bloque.count("\n[") >= config.GLOSARIO_MAX_ENTRADAS:
				break
		return bloque
