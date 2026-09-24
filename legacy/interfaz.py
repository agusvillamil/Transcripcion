import tkinter as tk
from tkinter import ttk
from transcribir import TranscriptorAudio


class InterfazAsistente:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Asistente IA")
		self.root.configure(bg="#1A5FB4")
		self.root.geometry("1400x850")
		self.root.minsize(900, 560)
		self.fuente_principal = ("Noto Sans", 17)
		self.fuente_titulo = ("Noto Sans", 25, "bold")

		# Se construye al iniciar para usar el dispositivo seleccionado por usuario.
		self.transcriptor = None
		self.configuracion_actual = None
		self.escuchando_activo = False

		self.canvas = tk.Canvas(
			self.root,
			bg="#1A5FB4",
			highlightthickness=0,
		)
		self.canvas.pack(fill="both", expand=True)
		self.canvas.bind("<Configure>", self._redibujar_fondo)

		self.panel = tk.Frame(self.canvas, bg="#1A5FB4")
		self.panel_window = self.canvas.create_window(0, 0, window=self.panel, anchor="nw")

		self.encabezado = tk.Frame(self.panel, bg="#1A5FB4")
		self.encabezado.pack(pady=(24, 18))

		self.etiqueta_escucha = tk.Label(
			self.encabezado,
			text="Comenzar a escuchar",
			font=self.fuente_titulo,
			fg="#F9F06B",
			bg="#1A5FB4",
		)
		self.etiqueta_escucha.pack(side="left", padx=(0, 14))

		self.boton_microfono = tk.Button(
			self.encabezado,
			text="🎤",
			font=("Noto Sans", 22),
			fg="#F9F06B",
			bg="#1A5FB4",
			activebackground="#164d93",
			activeforeground="#F9F06B",
			bd=0,
			cursor="hand2",
			command=self._alternar_escucha,
		)
		self.boton_microfono.pack(side="left")

		self.controles = tk.Frame(self.panel, bg="#1A5FB4")
		self.controles.pack(fill="x", padx=60, pady=(0, 10))

		self._construir_selectores_audio()

		self.contenedor_texto = tk.Frame(self.panel, bg="#1A5FB4")
		self.contenedor_texto.pack(fill="both", expand=True, padx=60, pady=(8, 36))

		self.marco_texto = tk.Frame(
			self.contenedor_texto,
			bg="#1A5FB4",
			highlightbackground="#ffffff",
			highlightthickness=2,
		)
		self.marco_texto.pack(fill="both", expand=True)

		self.scrollbar = tk.Scrollbar(self.marco_texto, orient="vertical")
		self.scrollbar.pack(side="right", fill="y")

		self.texto = tk.Text(
			self.marco_texto,
			wrap="word",
			bg="#1A5FB4",
			fg="#F9F06B",
			insertbackground="#F9F06B",
			bd=0,
			highlightthickness=0,
			font=self.fuente_principal,
			padx=8,
			pady=8,
			yscrollcommand=self.scrollbar.set,
		)
		self.texto.pack(side="left", fill="both", expand=True)
		self.scrollbar.config(command=self.texto.yview)

		self.texto.insert("1.0", "")
		self.texto.configure(state="disabled")

		self.agregar_texto(
			"Hablante 1: Hola mi nombre es Juan\n"
			"Hablante 2: Hola Juan, como estas?\n"
			"Hablante 1: Bien, estoy muy bien,\n"
			"            y tu como estas?\n"
			"Hablante 2: Genial, gracias por preguntar\n\n"
			"[Presiona el micrófono para comenzar a transcribir]"
		)

	def _construir_selectores_audio(self) -> None:
		self.dispositivos_entrada = TranscriptorAudio.listar_dispositivos_entrada()
		self.dispositivo_label_a_id = {}

		label_fuente = tk.Label(
			self.controles,
			text="Fuente de audio:",
			font=("Noto Sans", 12, "bold"),
			fg="#F9F06B",
			bg="#1A5FB4",
		)
		label_fuente.pack(side="left", padx=(0, 8))

		opciones_dispositivo = []
		for d in self.dispositivos_entrada:
			nombre = d["name"]
			if d.get("is_monitor"):
				nombre = f"{nombre} [Monitor]"
			texto = f"{d['id']} - {nombre}"
			self.dispositivo_label_a_id[texto] = d["id"]
			opciones_dispositivo.append(texto)

		self.dispositivo_var = tk.StringVar()
		self.combo_dispositivo = ttk.Combobox(
			self.controles,
			textvariable=self.dispositivo_var,
			values=opciones_dispositivo,
			state="readonly",
			width=62,
		)
		self.combo_dispositivo.pack(side="left", padx=(0, 16))

		preferido = next((d for d in self.dispositivos_entrada if d.get("is_monitor")), None)
		if preferido:
			nombre = preferido["name"] + " [Monitor]"
			self.dispositivo_var.set(f"{preferido['id']} - {nombre}")
		elif opciones_dispositivo:
			self.dispositivo_var.set(opciones_dispositivo[0])

		label_inferencia = tk.Label(
			self.controles,
			text="Inferencia:",
			font=("Noto Sans", 12, "bold"),
			fg="#F9F06B",
			bg="#1A5FB4",
		)
		label_inferencia.pack(side="left", padx=(4, 8))

		self.inferencia_var = tk.StringVar(value="GPU (VRAM)")
		self.combo_inferencia = ttk.Combobox(
			self.controles,
			textvariable=self.inferencia_var,
			values=["GPU (VRAM)", "CPU"],
			state="readonly",
			width=12,
		)
		self.combo_inferencia.pack(side="left")

	def _obtener_dispositivo_seleccionado(self):
		seleccion = self.dispositivo_var.get().strip()
		if not seleccion:
			return None
		return self.dispositivo_label_a_id.get(seleccion)

	def _redibujar_fondo(self, event: tk.Event) -> None:
		self.canvas.delete("borde")

		margen = 14
		radio = 34
		x1, y1 = margen, margen
		x2, y2 = event.width - margen, event.height - margen

		self._rectangulo_redondeado(
			x1,
			y1,
			x2,
			y2,
			radio,
			fill="#1A5FB4",
			outline="#d9d9d9",
			width=3,
			tags="borde",
		)

		ancho_panel = max(100, x2 - x1 - 36)
		alto_panel = max(100, y2 - y1 - 36)
		self.canvas.coords(self.panel_window, x1 + 18, y1 + 18)
		self.canvas.itemconfigure(self.panel_window, width=ancho_panel, height=alto_panel)

	def _rectangulo_redondeado(
		self,
		x1: int,
		y1: int,
		x2: int,
		y2: int,
		radio: int,
		**kwargs,
	) -> None:
		puntos = [
			x1 + radio,
			y1,
			x2 - radio,
			y1,
			x2,
			y1,
			x2,
			y1 + radio,
			x2,
			y2 - radio,
			x2,
			y2,
			x2 - radio,
			y2,
			x1 + radio,
			y2,
			x1,
			y2,
			x1,
			y2 - radio,
			x1,
			y1 + radio,
			x1,
			y1,
		]
		self.canvas.create_polygon(puntos, smooth=True, splinesteps=36, **kwargs)

	def _alternar_escucha(self) -> None:
		if not self.escuchando_activo:
			# Iniciar escucha
			dispositivo_entrada = self._obtener_dispositivo_seleccionado()
			device_inferencia = "cuda" if self.inferencia_var.get() == "GPU (VRAM)" else "cpu"
			config_nueva = (dispositivo_entrada, device_inferencia)

			try:
				if self.transcriptor is None or self.configuracion_actual != config_nueva:
					self.transcriptor = TranscriptorAudio(
						modelo="tiny",
						idioma="es",
						device=device_inferencia,
						dispositivo_entrada=dispositivo_entrada,
					)
					self.configuracion_actual = config_nueva
			except Exception as e:
				self.agregar_texto(f"Error al iniciar transcriptor: {e}")
				return

			self.escuchando_activo = True
			self.etiqueta_escucha.config(text="Escuchando...")
			self.texto.configure(state="normal")
			self.texto.delete("1.0", "end")
			self.texto.configure(state="disabled")
			self.transcriptor.iniciar(callback=self._callback_transcripcion)
			self.agregar_texto(
				f"Iniciado con dispositivo {dispositivo_entrada} e inferencia {device_inferencia.upper()}"
			)
		else:
			# Detener escucha
			self.escuchando_activo = False
			self.etiqueta_escucha.config(text="Comenzar a escuchar")
			if self.transcriptor:
				self.transcriptor.detener()

	def _callback_transcripcion(self, texto_nuevo: str, texto_acumulado: str) -> None:
		"""Callback que se ejecuta cuando el transcriptor recibe nuevo texto."""
		self.root.after(0, self._actualizar_texto_desde_hilo, texto_acumulado)

	def _actualizar_texto_desde_hilo(self, texto_acumulado: str) -> None:
		self.texto.configure(state="normal")
		self.texto.delete("1.0", "end")
		self.texto.insert("1.0", texto_acumulado)
		self.texto.see("end")
		self.texto.configure(state="disabled")

	def agregar_texto(self, nuevo_texto: str) -> None:
		self.texto.configure(state="normal")
		if self.texto.index("end-1c") != "1.0":
			self.texto.insert("end", "\n")
		self.texto.insert("end", nuevo_texto.strip())
		self.texto.see("end")
		self.texto.configure(state="disabled")

	def _salir_fullscreen(self, _event: tk.Event) -> None:
		self.root.attributes("-fullscreen", False)


if __name__ == "__main__":
	ventana = tk.Tk()
	app = InterfazAsistente(ventana)
	ventana.mainloop()
