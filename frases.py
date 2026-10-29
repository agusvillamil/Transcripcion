"""Fórmulas de cortesía y respuestas cortas con traducción fija.

Si una línea está formada solo por estas frases ("Thank you.", "No, ninguna.
Muchas gracias, doctora."), se traduce al instante, sin esperar la GPU ni al
LLM, que fuera de contexto a veces las traduce mal ("You're welcome" →
"Está bien"). Si la línea tiene cualquier otra cosa, va entera al LLM.

Para agregar una frase, sumala a la tabla del idioma en que se dice. Las
mayúsculas, tildes y puntuación de la clave no importan, salvo el "?" final,
que distingue la pregunta ("okay?") de la afirmación ("okay").
"""
import re
import unicodedata

# Dicho en inglés → interpretación al español (siempre "usted").
EN_ES = {
	"thank you": "Gracias.",
	"thanks": "Gracias.",
	"thank you very much": "Muchas gracias.",
	"thank you so much": "Muchas gracias.",
	"no thank you": "No, gracias.",
	"you're welcome": "De nada.",
	"you are welcome": "De nada.",
	"yes": "Sí.",
	"yeah": "Sí.",
	"no": "No.",
	"okay": "De acuerdo.",
	"ok": "De acuerdo.",
	"okay?": "¿De acuerdo?",
	"ok?": "¿De acuerdo?",
	"all right": "Muy bien.",
	"alright": "Muy bien.",
	"hello": "Hola.",
	"hi": "Hola.",
	"good morning": "Buenos días.",
	"good afternoon": "Buenas tardes.",
	"good evening": "Buenas noches.",
	"goodbye": "Adiós.",
	"bye": "Adiós.",
	"bye bye": "Adiós.",
	"have a nice day": "Que tenga un buen día.",
	"have a good day": "Que tenga un buen día.",
	"have a great day": "Que tenga un excelente día.",
	"take care": "Cuídese.",
	"you too": "Igualmente.",
	"same to you": "Igualmente.",
	"of course": "Por supuesto.",
	"one moment": "Un momento.",
	"one moment please": "Un momento, por favor.",
	"just a moment": "Un momento.",
	"i understand": "Entiendo.",
	"any questions?": "¿Alguna pregunta?",
	"do you have any questions?": "¿Tiene alguna pregunta?",
	"can you repeat that?": "¿Puede repetirlo?",
	"could you repeat that?": "¿Podría repetirlo?",
}

# Dicho en español → interpretación al inglés.
ES_EN = {
	"gracias": "Thank you.",
	"muchas gracias": "Thank you very much.",
	"muchísimas gracias": "Thank you so much.",
	"no gracias": "No, thank you.",
	"de nada": "You're welcome.",
	"sí": "Yes.",
	"no": "No.",
	"ninguna": "None.",
	"no ninguna": "No, none.",
	"está bien": "Okay.",
	"de acuerdo": "Okay.",
	"vale": "Okay.",
	"hola": "Hello.",
	"buenos días": "Good morning.",
	"buenas tardes": "Good afternoon.",
	"adiós": "Goodbye.",
	"chau": "Bye.",
	"chao": "Bye.",
	"hasta luego": "See you later.",
	"igualmente": "You too.",
	"claro": "Of course.",
	"claro que sí": "Of course.",
	"por supuesto": "Of course.",
	"un momento": "One moment.",
	"un momentito": "One moment.",
	"entiendo": "I understand.",
	"perdón": "Sorry.",
	"perdón?": "Sorry?",
	"cuídese": "Take care.",
	"que tenga un buen día": "Have a nice day.",
	"puede repetir?": "Can you repeat that?",
	"me lo puede repetir?": "Can you repeat that?",
}

# Tratamientos al final de la frase: "Muchas gracias, doctora." → "Thank you very much, doctor."
# "doctor" no está en inglés: en español no se sabría si es doctor o doctora.
VOCATIVOS = {
	"en": {"ma'am": "señora", "sir": "señor", "miss": "señorita"},
	"es": {"doctor": "doctor", "doctora": "doctor", "señora": "ma'am", "señor": "sir", "señorita": "miss"},
}


def _clave(texto: str) -> str:
	sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if not unicodedata.combining(c))
	t = re.sub(r"[¿¡.,!;:…\"“”-]", " ", sin_tildes.replace("’", "'"))
	return re.sub(r"\s*\?", "?", re.sub(r"\s+", " ", t).strip())


_TABLAS = {"en": {_clave(k): v for k, v in EN_ES.items()}, "es": {_clave(k): v for k, v in ES_EN.items()}}
_VOCATIVOS = {o: {_clave(k): v for k, v in t.items()} for o, t in VOCATIVOS.items()}


def traduccion_fija(texto: str, origen: str) -> str | None:
	"""Traducción de la línea si toda ella son fórmulas de la tabla; si no, None."""
	tabla, vocativos = _TABLAS[origen], _VOCATIVOS[origen]
	partes = []
	for oracion in re.split(r"(?<=[.?!])\s+", texto.strip()):
		clave = _clave(oracion)
		if not clave:
			continue
		if clave in tabla:
			partes.append(tabla[clave])
			continue
		pregunta = "?" if clave.endswith("?") else ""
		base, _, vocativo = clave.rstrip("?").rpartition(" ")
		fija = tabla.get(base + pregunta)
		if fija is None or vocativo not in vocativos:
			return None
		partes.append(f"{fija[:-1]}, {vocativos[vocativo]}{fija[-1]}")
	return " ".join(partes) or None
