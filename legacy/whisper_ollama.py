import subprocess
import time
import re

# ------------------------
# CONFIG
# ------------------------

WHISPER_CMD = [
    "/home/kindue/whisper.cpp/build/bin/whisper-stream",
    "-m", "/home/kindue/whisper.cpp/models/ggml-base.bin",
    "-t", "2",
    "-l", "en",
    "--step", "3000",
    "--length", "8000",
    "--keep", "0"
]

OLLAMA_MODEL = "mistral"

BUFFER_SIZE = 8   # cantidad de frases antes de procesar


# ------------------------
# FUNCIONES
# ------------------------

historial = ""

def limpiar_repeticiones(texto):
    frases = texto.split(".")
    nuevas = []

    for f in frases:
        f = f.strip()
        if not f:
            continue

        # evita repetir frases recientes
        if f.lower() not in historial.lower():
            nuevas.append(f)

    return ". ".join(nuevas)


def procesar_con_ollama(texto):
    prompt = f"""
        You are a medical interpreter assistant.

        Your task:
        - Correct transcription errors
        - Remove repetitions
        - Improve clarity and grammar
        - Keep the original meaning EXACTLY

        Rules:
        - DO NOT add new information
        - DO NOT summarize
        - DO NOT skip content
        - ALWAYS return the corrected text, even if minimal

        If the sentence is unclear, fix it as best as possible.

        Text:
        {texto}
        """

    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=10   # 👈 clave
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return texto  # fallback


# ------------------------
# MAIN
# ------------------------

proc = subprocess.Popen(
    WHISPER_CMD,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

buffer = []

print("🟢 Sistema iniciado...\n")

try:
    for line in proc.stdout:
        line = line.strip()

       # ignorar líneas vacías y mensajes iniciales
        if not line or "[Start speaking]" in line:
            continue

        # 🔴 ignorar logs técnicos
        if (
            line.startswith("init:")
            or line.startswith("whisper_")
            or line.startswith("ggml_")
        ):
            continue

        # 🔴 ignorar ruido de audio
        if any(tag in line for tag in ["[Music]", "[BLANK_AUDIO]"]):
            continue

        print(f"[RAW] {line}")

        limpio = limpiar_repeticiones(line)

        if limpio:
            buffer.append(limpio)

        texto_actual = " ".join(buffer)

        # detectar fin de frase
        if any(texto_actual.endswith(p) for p in [".", "?", "!"]) or len(buffer) >= 8:

            texto = texto_actual
            buffer = []

            corregido = procesar_con_ollama(texto)

            if not corregido.strip():
                corregido = texto

            print("\n🧠 [CORREGIDO]")
            print(corregido)
            print("\n" + "-"*50 + "\n")

            historial += " " + corregido

except KeyboardInterrupt:
    proc.terminate()
    print("\n🛑 Finalizado")
