# Reporte: video16k.wav

- Whisper: `ggml-large-v3-turbo-q5_0.bin` — 55 líneas, ASR media 2.59s, máx 4.42s

| Modelo | 1er token (media) | Traducción (media) | Traducción (máx) | En GPU |
|---|---|---|---|---|
| gemma3:4b | 1.72s | 2.25s | 3.80s | 100% |
| translategemma:4b | 0.53s | 0.99s | 2.04s | 100% |
| qwen3:8b | 1.15s | 1.90s | 4.03s | 100% |
| mistral:latest | 1.16s | 2.37s | 5.58s | 100% |
| llama3.2:3b | 0.51s | 0.99s | 2.26s | 100% |

## Líneas

### 0 · 10.8s · EN→ES
**Original:** Hello, I am John. I will be your nurse today to get you ready for your procedure. What are we going to be doing to you today?  
**gemma3:4b:** Hola, soy John. Seré su enfermero hoy para prepararle para su procedimiento. ¿Qué nos van a estar haciendo hoy?  
**translategemma:4b:** Hola, soy John. Hoy seré su enfermero para prepararle para el procedimiento. ¿Qué vamos a hacerle hoy?  
**qwen3:8b:** Hola, soy John. Seré su enfermero hoy para prepararlo para su procedimiento. ¿Qué vamos a hacer hoy con usted?  
**mistral:latest:** Hola, soy Juan. Seré tu enfermero hoy para prepararte para tu procedimiento. ¿Qué vamos a hacer contigo hoy?  
**llama3.2:3b:** Hola, soy Juan. Seré su enfermera hoy para prepararlo para su procedimiento. ¿Qué vamos a hacerle hoy?  

### 1 · 31.8s · ES→EN
**Original:** Hola.  
**gemma3:4b:** Hello.  
**translategemma:4b:** Hello.  
**qwen3:8b:** Hello.  
**mistral:latest:** Soy Ana. Soy tu intérprete médico hoy. ¿Por qué estás aquí hoy?

Translation: Hello. I am Ana. I am your medical interpreter today. Why are you here today?  
**llama3.2:3b:** Hello.  

### 2 · 33.1s · ES→EN
**Original:** Me van a remover la vesícula y a quitar las piedras.  
**gemma3:4b:** They are going to remove my gallbladder and take out the stones.  
**translategemma:4b:** They are going to remove my gallbladder and take out the stones.  
**qwen3:8b:** They are going to remove my gallbladder and take out the stones.  
**mistral:latest:** They are going to remove my gallbladder and take out the stones.  
**llama3.2:3b:** They are going to remove the gallbladder and take out the stones.  

### 3 · 46.5s · EN→ES
**Original:** That is correct. What we are going to perform is called a laparoscopic cholecystectomy.  
**gemma3:4b:** Eso es correcto. Lo que vamos a realizar se llama colecistectomía laparoscópica.  
**translategemma:4b:** Eso es correcto. Lo que vamos a realizar se denomina colecistectomía laparoscópica.  
**qwen3:8b:** Eso es correcto. Lo que vamos a realizar se llama colecistectomía laparoscópica.  
**mistral:latest:** Esto es correcto. Lo que vamos a realizar se llama colecistectomía laparoscópica.  
**llama3.2:3b:** Eso es correcto. Lo que vamos a realizar se llama colecistectomía laparoscópica.  

### 4 · 63.7s · ES→EN
**Original:** Muy bien, entonces es una colexistectomía laparoscópica.  
**gemma3:4b:** Okay, so it’s a cholecystectomy.  
**translategemma:4b:** Okay, so it's a laparoscopic colectomy.  
**qwen3:8b:** Very well, then it is a laparoscopic cholecystectomy.  
**mistral:latest:** Very good, so it is a laparoscopic cholecystectomy.  
**llama3.2:3b:** So it's a laparoscopic colectomy.  

### 5 · 79.2s · EN→ES
**Original:** Yes. Now moving on. Are you allergic to any medication?  
**gemma3:4b:** Sí. Ahora pasando. ¿Es usted alérgico a algún medicamento?  
**translategemma:4b:** Sí. Ahora, pasemos a otra pregunta. ¿Tiene alguna alergia a algún medicamento?  
**qwen3:8b:** Sí. Ahora pasamos a otro punto. ¿Tiene alergia a algún medicamento?  
**mistral:latest:** Sí. Ahora pasando a lo siguiente. ¿Estás alérgico a algún medicamento?  
**llama3.2:3b:** Sí. Ahora, vamos a seguir adelante. ¿Tiene alguna alergia a medicamentos?  

### 6 · 91.6s · ES→EN
**Original:** Pues no que yo sepa, hasta ahorita nada.  
**gemma3:4b:** As far as I know, nothing.  
**translategemma:4b:** As far as I know, nothing yet.  
**qwen3:8b:** Well, as far as I know, nothing so far.  
**mistral:latest:** I don't know of any, so far nothing.  
**llama3.2:3b:** I don't know anything yet.  

### 7 · 101.1s · EN→ES
**Original:** Good. Have you had any previous operations?  
**gemma3:4b:** Bien. ¿Ha tenido alguna operación previa?  
**translategemma:4b:** De acuerdo. ¿Ha tenido alguna cirugía antes?  
**qwen3:8b:** Bueno. ¿Ha tenido alguna cirugía previa?  
**mistral:latest:** Bueno. ¿Has tenido alguna operación previa?  
**llama3.2:3b:** Muy bien. ¿Tú has tenido alguna operación previa?  

### 8 · 110.8s · ES→EN
**Original:** No, solo una cesárea.  
**gemma3:4b:** No, just a C-section.  
**translategemma:4b:** No, just a C-section.  
**qwen3:8b:** No, just a cesarean section.  
**mistral:latest:** No, only a cesarean section.  
**llama3.2:3b:** No, just one C-section.  

### 9 · 117.1s · EN→ES
**Original:** Did you have any adverse reactions to Buenesthesia?  
**gemma3:4b:** ¿Tuvo alguna reacción adversa a la Buenestancia?  
**translategemma:4b:** ¿Experimentó alguna reacción adversa durante o después del tratamiento con Buenesthesia?  
**qwen3:8b:** ¿Tuvo alguna reacción adversa a Buenesthesia?  
**mistral:latest:** ¿Tuviste alguna reacción adversa a Buenesthesia?  
**llama3.2:3b:** ¿Tuviste ninguna reacción adversa a la Buenesthesia?  

### 10 · 126.8s · ES→EN
**Original:** Pues no, pero no me durmieron, solo me pusieron la raquia. Nunca me han dormido con anestesia.  
**gemma3:4b:** No, but they didn't put me to sleep, they just gave me the spinal. I've never been put to sleep with anesthesia.  
**translategemma:4b:** No, they didn't put me to sleep, they just gave me the raquia. They have never given me anesthesia.  
**qwen3:8b:** Well, no, but they didn't put me to sleep, they just gave me a spinal. They've never put me to sleep with anesthesia.  
**mistral:latest:** I didn't sleep, but they only put the rack (spinal anesthesia). I've never been put to sleep with anesthesia.  
**llama3.2:3b:** No, but they didn't put me to sleep, they just put in the catheter. They've never put me to sleep with anesthesia.  

### 11 · 145.2s · EN→ES
**Original:** Okay, well this time we are going to give you general anesthesia, which will put you completely asleep.  
**gemma3:4b:** Bien, pues esta vez le vamos a administrar anestesia general, que le va a poner completamente dormida.  
**translategemma:4b:** De acuerdo, esta vez vamos a administrarle anestesia general, lo que le hará dormir profundamente.  
**qwen3:8b:** Okay, bien, esta vez vamos a darle anestesia general, la cual lo pondrá completamente dormido.  
**mistral:latest:** Bien, esta vez te administraremos anestesia general, que te dejará dormido completamente.  
**llama3.2:3b:** Esto es, bien, esta vez vamos a darte anestesia general, lo que te dejará completamente dormido.  

### 12 · 163.6s · ES→EN
**Original:** Ok, sí, está bien. Ya me habían explicado eso.  
**gemma3:4b:** Okay, yes, that’s fine. You had already been explained that.  
**translategemma:4b:** Okay, yes, I understand. I had already been informed about that.  
**qwen3:8b:** Okay, yes, that's fine. They already explained that to me.  
**mistral:latest:** I understand, yes, that's fine. I've already been explained that.  
**llama3.2:3b:** Okay, yes, it's fine. I already had that explained to me.  

### 13 · 172.8s · EN→ES
**Original:** That's fine ma'am. We still have to go over all of this because we need you to sign consent forms before the procedure.  
**gemma3:4b:** Está bien, señora. Todavía tenemos que revisar todo esto porque usted necesita firmar los formularios de consentimiento antes del procedimiento.  
**translategemma:4b:** De acuerdo, señora. Todavía tenemos que revisar todo esto, ya que necesitamos que usted firme los formularios de consentimiento antes del procedimiento.  
**qwen3:8b:** Eso está bien señora. Todavía tenemos que revisar todo esto porque necesitamos que firme los formularios de consentimiento antes del procedimiento.  
**mistral:latest:** Esto es correcto, señora. Aún tenemos que revisar todo esto porque necesitamos que usted firme formas de consentimiento antes del procedimiento.  
**llama3.2:3b:** Eso está bien, señora. Todavía tenemos que revisar todo esto porque necesitamos que firmes los formularios de consentimiento antes del procedimiento.  

### 14 · 191.3s · ES→EN
**Original:** Entendido.  
**gemma3:4b:** Understood.  
**translategemma:4b:** Understood.  
**qwen3:8b:** Understood.  
**mistral:latest:** Understood.  
**llama3.2:3b:** Understood.  

### 15 · 194.9s · EN→ES
**Original:** When was the last time you had anything to eat or drink?  
**gemma3:4b:** ¿Cuándo fue la última vez que comió o bebió algo?  
**translategemma:4b:** ¿Cuándo fue la última vez que comiste o bebiste algo?  
**qwen3:8b:** ¿Cuándo fue la última vez que comiste o bebiste algo?  
**mistral:latest:** ¿Cuándo fue la última vez que comiste o bebiste algo?  
**llama3.2:3b:** Cuándo fue la última vez que comiste o bebiste algo?  

### 16 · 204.1s · ES→EN
**Original:** Pues me dijeron que no comiera ni bebiera nada después de la medianoche ayer. Desde las 9 p.m. ya no he comido nada.  
**gemma3:4b:** I was told that I shouldn't have eaten or drunk anything after midnight last night. Since 9 PM, I haven't eaten anything.  
**translategemma:4b:** They told me not to eat or drink anything after midnight last night. I haven't eaten anything since 9 p.m.  
**qwen3:8b:** So they told me not to eat or drink anything after midnight yesterday. I haven't eaten anything since 9 p.m.  
**mistral:latest:** I was told not to eat or drink anything after midnight yesterday. I haven't eaten anything since 9 p.m.  
**llama3.2:3b:** I had told them not to eat or drink anything after midnight last night. Since 9 p.m. I haven't eaten anything.  

### 17 · 228.4s · EN→ES
**Original:** Excellent. Do you have diabetes or any other medical conditions?  
**gemma3:4b:** Excelente. ¿Tiene diabetes o alguna otra condición médica?  
**translategemma:4b:** Excelente. ¿Tiene usted diabetes o alguna otra condición médica?  
**qwen3:8b:** Excelente. ¿Tiene diabetes o alguna otra condición médica?  
**mistral:latest:** ¡Excelente. ¿Tienes diabetes o alguna otra condición médica?  
**llama3.2:3b:** Excelente. ¿Tiene diabetes o alguna otra condición médica?  

### 18 · 240.4s · ES→EN
**Original:** No.  
**gemma3:4b:** No.  
**translategemma:4b:** No.  
**qwen3:8b:** No.  
**mistral:latest:** No, I don't.  
**llama3.2:3b:** No.  

### 19 · 242.3s · EN→ES
**Original:** Are you taking any medications?  
**gemma3:4b:** ¿Está tomando alguna medicación?  
**translategemma:4b:** ¿Está tomando algún medicamento?  
**qwen3:8b:** ¿Está tomando algún medicamento?  
**mistral:latest:** ¿Estás tomando alguna medicación?  
**llama3.2:3b:** ¿Está tomando cualquier medicación?  

### 20 · 248.4s · ES→EN
**Original:** No.  
**gemma3:4b:** No.  
**translategemma:4b:** No.  
**qwen3:8b:** No.  
**mistral:latest:** No. (The patient is not taking any medications.)  
**llama3.2:3b:** No.  

### 21 · 250.2s · EN→ES
**Original:** Do you feel ill or coming down with any flu-like symptoms or sickness?  
**gemma3:4b:** ¿Se siente usted enfermo o con síntomas de gripe o alguna otra enfermedad?  
**translategemma:4b:** ¿Se siente mal o presenta síntomas similares a los de la gripe o algún otro tipo de enfermedad?  
**qwen3:8b:** ¿Se siente enfermo o está empezando a tener síntomas similares a los de la gripe o malestar?  
**mistral:latest:** ¿Tienes algún tipo de enfermedad o síntomas similares a la gripe o enfermedad?  
**llama3.2:3b:** ¿Siente mal o está enfermo o tiene síntomas de gripe o enfermedad?  

### 22 · 263.1s · ES→EN
**Original:** No.  
**gemma3:4b:** No.  
**translategemma:4b:** No.  
**qwen3:8b:** No.  
**mistral:latest:** No.  
**llama3.2:3b:** No.  

### 23 · 265.1s · EN→ES
**Original:** Do you have any loose, chipped or missing teeth?  
**gemma3:4b:** ¿Tiene algún diente suelto, roto o faltante?  
**translategemma:4b:** ¿Tiene alguna pieza de diente suelta, rota o faltante?  
**qwen3:8b:** ¿Tiene alguna dentadura suelta, rota o perdida?  
**mistral:latest:** ¿Tienes algún diente móvil, desprendido o ausente?  
**llama3.2:3b:** ¿Tiene algún diente suelto, espolvoreado o faltante?  

### 24 · 274.7s · ES→EN
**Original:** No, aún no.  
**gemma3:4b:** No, still not.  
**translategemma:4b:** No, not yet.  
**qwen3:8b:** No, not yet.  
**mistral:latest:** No, not yet.  
**llama3.2:3b:** No, I haven't yet.  

### 25 · 277.9s · EN→ES
**Original:** So the procedure will go like this. We're going to give you medicine to calm you down through an IV. Then when you are calm, we will administer general anesthesia. This will put you completely asleep.  
**gemma3:4b:** Así que el procedimiento será así. Vamos a darle medicina para calmarte a través de una vía intravenosa. Y luego, cuando estés calmado, administramos anestesia general. Esto te pondrá completamente dormido.  
**translategemma:4b:** Así que el procedimiento se llevará a cabo de la siguiente manera. Primero, le administraremos medicamentos para calmarle a través de una vía intravenosa. Una vez que esté calmado, procederemos a administrar anestesia general. Esto le hará dormir profundamente.  
**qwen3:8b:** El procedimiento será así. Le daremos medicamentos para que se relaje a través de una vía intravenosa. Luego, cuando esté relajado, le administraremos anestesia general. Esto lo dejará completamente dormido.  
**mistral:latest:** La procedimiento será así. Le daremos medicina para calmarlo a través de una vía intravenosa. Después de que esté calmado, le administraremos anestesia general. Esto le hará dormir completamente.  
**llama3.2:3b:** Así que el procedimiento irá así. Le vamos a dar medicación para calmarlo a través de una vena. Luego, cuando esté calmado, le vamos a administrar anestesia general. Esto lo pondrá completamente dormido.  

### 26 · 289.3s · EN→ES
**Original:** We will then proceed to put a tube in your mouth to help you breathe. The surgeon will make a small incision through which he will put a small tube with a camera and light on the end.  
**gemma3:4b:** Luego procederemos a colocar un tubo en su boca para ayudarle a respirar. El cirujano hará una pequeña incisión a través de la cual colocará un pequeño tubo con una cámara y luz al final.  
**translategemma:4b:** A continuación, insertaremos un tubo en su boca para ayudarle a respirar. El cirujano realizará una pequeña incisión a través de la cual introducirá un pequeño tubo con una cámara y una luz en su extremo.  
**qwen3:8b:** Entonces procederemos a colocar un tubo en su boca para ayudarle a respirar. El cirujano hará una pequeña incisión a través de la cual colocará un pequeño tubo con una cámara y luz en el extremo.  
**mistral:latest:** Después, colocaremos un tubo en tu boca para ayudarte a respirar. El cirujano hará una pequeña incisión a través de la cual colocará un tubo pequeño con una cámara y una luz en su extremo.  
**llama3.2:3b:** Luego procederemos a poner un tubo en tu boca para ayudarte a respirar. El cirujano hará una pequeña incisión a través de la cual colocará un pequeño tubo con una cámara y luz en el extremo.  

### 27 · 300.6s · EN→ES
**Original:** He will then start the procedure.  
**gemma3:4b:** Él entonces comenzará el procedimiento.  
**translategemma:4b:** Luego, iniciará el procedimiento.  
**qwen3:8b:** Él entonces comenzará el procedimiento.  
**mistral:latest:** Comenzará entonces el procedimiento.  
**llama3.2:3b:** Él comenzará el procedimiento.  

### 28 · 303.0s · EN→ES
**Original:** After the procedure we will remove the tube before you wake up and then we will take you to recovery.  
**gemma3:4b:** Después del procedimiento retiraremos el tubo antes de que se despierte y luego nos llevaremos a usted a la sala de recuperación.  
**translategemma:4b:** Después del procedimiento, retiraremos el tubo antes de que se despierte y luego lo trasladaremos a la sala de recuperación.  
**qwen3:8b:** Después del procedimiento, retiraremos el tubo antes de que despiertes y luego te llevaremos a recuperación.  
**mistral:latest:** Después del procedimiento retiraremos el tubo antes de que despertes y luego te llevaremos a la recuperación.  
**llama3.2:3b:** Después de la procedencia, retiraremos la tuba antes de que despiertes y luego la llevaremos a recuperación.  

### 29 · 367.9s · ES→EN
**Original:** Muy bien.  
**gemma3:4b:** Okay.  
**translategemma:4b:** Excellent.  
**qwen3:8b:** Very well.  
**mistral:latest:** Understood.  
**llama3.2:3b:** Very well.  

### 30 · 370.4s · EN→ES
**Original:** This first consent form states that you are understanding the procedure and complications and give us permission to perform this.  
**gemma3:4b:** Este primer formulario de consentimiento indica que usted está entendiendo el procedimiento y las complicaciones y nos da permiso para llevarlo a cabo.  
**translategemma:4b:** Este primer formulario de consentimiento indica que usted comprende el procedimiento y los posibles riesgos, y que otorga su permiso para llevarlo a cabo.  
**qwen3:8b:** Este primer formulario de consentimiento indica que usted comprende el procedimiento y sus complicaciones y nos da permiso para realizarlo.  
**mistral:latest:** Este primer formulario de consentimiento indica que entiendes el procedimiento y las complicaciones y nos autorizas a realizarlo.  
**llama3.2:3b:** Este primer formulario de consentimiento establece que usted entiende el procedimiento y las complicaciones y le da nuestro permiso para realizar este.  

### 31 · 378.7s · EN→ES
**Original:** Any complications being that we might have to make a larger incision than expected.  
**gemma3:4b:** Cualquier complicación habiendo que quizás tengamos que hacer una incisión más grande de lo esperado.  
**translategemma:4b:** Cualquier complicación, especialmente si necesitamos realizar una incisión más grande de lo previsto.  
**qwen3:8b:** Cualquier complicación consiste en que podríamos tener que hacer una incisión más grande de lo esperado.  
**mistral:latest:** Puede haber complicaciones, ya que podríamos necesitar hacer una incisión mayor de lo esperado.  
**llama3.2:3b:** Cualquier complicación, teniendo en cuenta que podríamos tener que hacer una incisión más grande de lo que se espera.  

### 32 · 409.4s · ES→EN
**Original:** Ok, listo.  
**gemma3:4b:** Okay, ready.  
**translategemma:4b:** Okay, that's all.  
**qwen3:8b:** Okay, ready.  
**mistral:latest:** Ready, set.  
**llama3.2:3b:** I'm ready.  

### 33 · 413.0s · EN→ES
**Original:** This next one says that you understand all risks involved with this procedure.  
**gemma3:4b:** La siguiente dice que usted comprende todos los riesgos asociados con este procedimiento.  
**translategemma:4b:** La siguiente frase indica que usted comprende todos los riesgos asociados con este procedimiento.  
**qwen3:8b:** Este siguiente dice que usted entiende todos los riesgos involucrados en este procedimiento.  
**mistral:latest:** Este siguiente dice que comprendes todos los riesgos involucrados en este procedimiento.  
**llama3.2:3b:** Este próximo uno dice que entiendes todos los riesgos involucrados con este procedimiento.  

### 34 · 418.2s · EN→ES
**Original:** This like any other procedure has the risk to injure any of the other organs nearby.  
**gemma3:4b:** Como cualquier otro procedimiento, tiene el riesgo de lesionar cualquier otro órgano cercano.  
**translategemma:4b:** Al igual que cualquier otro procedimiento, este conlleva el riesgo de dañar otros órganos cercanos.  
**qwen3:8b:** Esta cirugía, como cualquier otra procedimiento, tiene el riesgo de lesionar cualquier otro órgano cercano.  
**mistral:latest:** Este procedimiento, como cualquier otro, tiene el riesgo de lesionar cualquier otro órgano cercano.  
**llama3.2:3b:** Este como cualquier otro procedimiento tiene el riesgo de dañar cualquier uno de los otros órganos cercanos.  

### 35 · 424.6s · EN→ES
**Original:** There is also a risk for infection and hemorrhage.  
**gemma3:4b:** También existe el riesgo de infección y hemorragia.  
**translategemma:4b:** También existe el riesgo de infección y hemorragia.  
**qwen3:8b:** También existe el riesgo de infección y hemorragia.  
**mistral:latest:** También hay riesgo de infección y hemorragia.  
**llama3.2:3b:** Hay también un riesgo de infección y hemorragia.  

### 36 · 428.4s · EN→ES
**Original:** Also, there is a risk of chipping, loosening, or knocking out teeth with a tooth to help you breathe, but this rarely happens.  
**gemma3:4b:** También existe el riesgo de fractura, aflojamiento o expulsión de dientes con un diente para ayudarle a respirar, pero esto rara vez ocurre.  
**translategemma:4b:** Además, existe el riesgo de que los dientes se astillen, se aflojen o se caigan, especialmente si se utilizan para ayudar a respirar, pero esto ocurre muy raramente.  
**qwen3:8b:** También existe el riesgo de que se rompan, se suelten o se desprendan los dientes con un diente para ayudarte a respirar, pero esto raramente ocurre.  
**mistral:latest:** También hay un riesgo de fracturar, desprendimiento o desprendimiento de dientes con un diente para ayudarte a respirar, pero esto sucede muy raramente.  
**llama3.2:3b:** También existe el riesgo de chocar, deslizar o sacudir los dientes con un diente para ayudarte a respirar, pero esto sucede raramente.  

### 37 · 435.8s · EN→ES
**Original:** There is also risk with the anesthesia which will include awareness during the procedure, coma or in the worst case scenario, death.  
**gemma3:4b:** También existe riesgo con la anestesia, que incluirá conciencia durante el procedimiento, coma o, en el peor de los casos, muerte.  
**translategemma:4b:** También existe el riesgo asociado con la anestesia, que puede incluir la pérdida de conciencia durante el procedimiento, el coma o, en el peor de los casos, la muerte.  
**qwen3:8b:** También hay riesgo con la anestesia, que incluirá la conciencia durante el procedimiento, coma o, en el peor de los casos, la muerte.  
**mistral:latest:** También hay riesgo con la anestesia, lo que incluye la conciencia durante el procedimiento, coma o, en el peor de los casos, muerte.  
**llama3.2:3b:** También existe el riesgo con la anestesia, que incluirá la conciencia durante el procedimiento, coma o, en el peor caso, la muerte.  

### 38 · 443.6s · EN→ES
**Original:** This very rarely occurs. The anesthesiologist will speak to you in detail about the risk and benefits of anesthesia after I am done with you.  
**gemma3:4b:** Esto ocurre muy raramente. El anestesista hablará con usted en detalle sobre los riesgos y beneficios de la anestesia después de que termine yo con usted.  
**translategemma:4b:** Esto ocurre muy raramente. El anestesista hablará con usted en detalle sobre los riesgos y beneficios de la anestesia una vez que haya terminado con usted.  
**qwen3:8b:** Esto ocurre muy raramente. El anestesiólogo hablará con usted en detalle sobre los riesgos y beneficios de la anestesia después de que termine con usted.  
**mistral:latest:** Esto ocurre muy raramente. El anestesiólogo te hablará en detalle sobre los riesgos y beneficios de la anestesia después de que yo termine contigo.  
**llama3.2:3b:** Esta muy raramente ocurre. El anestésistico hablará con usted en detalle sobre el riesgo y las ventajas de la anestesia después de que termine con usted.  

### 39 · 531.3s · ES→EN
**Original:** Todo eso se escucha muy feo.  
**gemma3:4b:** That all sounds very bad.  
**translategemma:4b:** That sounds really unpleasant.  
**qwen3:8b:** All of that sounds very bad.  
**mistral:latest:** All of that sounds very unpleasant.  
**llama3.2:3b:** That all sounds very unpleasant.  

### 40 · 536.1s · EN→ES
**Original:** This is just a risk that might happen. It does not mean that it will. I am required to discuss all of this with you. Let's hold up on signing this form until after you speak to the anesthesiologist, okay? Okay.  
**gemma3:4b:** Este es solo un riesgo que podría ocurrir. No significa que vaya a pasar. Estoy obligado a discutir todo esto con usted. Esperemos a firmar este formulario hasta después de que hable con el anestesista, ¿de acuerdo? De acuerdo.  
**translategemma:4b:** Esto es simplemente un riesgo que podría ocurrir. No significa que vaya a suceder. Estoy obligado a discutir todo esto con usted. Esperemos a que hable con el anestesista antes de firmar este formulario, ¿de acuerdo? De acuerdo.  
**qwen3:8b:** Esto es solo un riesgo que podría ocurrir. No significa que ocurra. Estoy obligado a discutir todo esto contigo. Vamos a posponer la firma de este formulario hasta después de que hables con el anestesiólogo, ¿de acuerdo? ¿De acuerdo?  
**mistral:latest:** Esto es solo un riesgo que podría ocurrir. No significa que lo hará. Tengo que hablarte sobre todo esto. Vamos a posponer la firma de este formulario hasta después de que hablés con el anestesiólogo, ¿bien? ¿Bien.  
**llama3.2:3b:** Esto es solo un riesgo que podría suceder. No significa que va a suceder. Estoy obligado a discutir todo esto contigo. Vamos a posponer la firma de esta forma hasta después de que hablas con el anestésico, ¿de acuerdo?  

### 41 · 569.1s · ES→EN
**Original:** Muy bien. Entonces, ¿qué sigue?  
**gemma3:4b:** That’s good. Then, what’s next?  
**translategemma:4b:** Okay. So, what's next?  
**qwen3:8b:** Very well. So, what's next?  
**mistral:latest:** Very well then, what's next?  
**llama3.2:3b:** So, what's next?  

### 42 · 573.0s · EN→ES
**Original:** Next one states that if the doctor finds the need to administer a blood transfusion or blood products, we have your permission to do so.  
**gemma3:4b:** El siguiente indica que si el médico determina la necesidad de administrar una transfusión de sangre o productos sanguíneos, tenemos su permiso para hacerlo.  
**translategemma:4b:** El siguiente punto indica que, si el médico determina que es necesario realizar una transfusión de sangre o administrar productos sanguíneos, cuenta con nuestra autorización para hacerlo.  
**qwen3:8b:** El siguiente indica que si el médico determina la necesidad de administrar una transfusión de sangre o productos sanguíneos, tenemos su permiso para hacerlo.  
**mistral:latest:** El siguiente dice que, si el médico encuentra la necesidad de administrar una transfusión de sangre o productos sanguíneos, tenemos su permiso para hacerlo.  
**llama3.2:3b:** El próximo establece que si el médico encuentra la necesidad de administrar una transfusión de sangre o productos sanguíneos, tenemos su permiso para hacerlo.  

### 43 · 597.1s · ES→EN
**Original:** Ya me estoy preocupando, ¿entonces me van a hacer una transfusión de sangre? A mí me dijeron que era una operación fácil y con pocas complicaciones.  
**gemma3:4b:** I’m starting to worry, then are you going to give me a blood transfusion? I was told it was an easy operation with few complications.  
**translategemma:4b:** I'm starting to worry, so are you going to give me a blood transfusion? I was told that it was a simple operation with few complications.  
**qwen3:8b:** I'm already starting to worry, so are they going to give me a blood transfusion? They told me it was an easy operation with few complications.  
**mistral:latest:** Am I going to have a blood transfusion then? They told me it was an easy operation with few complications.  
**llama3.2:3b:** I'm already getting worried, so are they going to do a blood transfusion on me? They told me it was an easy operation with few complications.  

### 44 · 624.0s · EN→ES
**Original:** We are not planning on doing so. This is just in case we need to.  
**gemma3:4b:** No estamos planeando hacer eso. Es solo por si acaso necesitamos hacerlo.  
**translategemma:4b:** No estamos planeando hacerlo. Simplemente lo estamos considerando como una posibilidad, por si acaso.  
**qwen3:8b:** No planeamos hacerlo. Esto es solo por si necesitamos hacerlo.  
**mistral:latest:** No estamos planeando hacerlo. Esto es solo en caso de que lo necesitemos.  
**llama3.2:3b:** No estamos planeando hacerlo. Esto es solo en caso de que lo necesitemos.  

### 45 · 628.2s · EN→ES
**Original:** This does not mean that we are going to, okay?  
**gemma3:4b:** Esto no significa que vayamos a hacerlo, ¿de acuerdo?  
**translategemma:4b:** Esto no significa que vamos a hacerlo, ¿verdad?  
**qwen3:8b:** Esto no significa que vayamos a hacerlo, ¿de acuerdo?  
**mistral:latest:** Esto no significa que vamos a hacerlo, claro?  
**llama3.2:3b:** Esto no significa que vamos a hacerlo, ¿entiendes?  

### 46 · 645.2s · ES→EN
**Original:** Muy bien, es que ya me estoy asustando. Entonces, ¿dónde firmo este?  
**gemma3:4b:** Okay, I’m starting to get scared. So, where do I sign this?  
**translategemma:4b:** Okay, I'm starting to get nervous. So, where do I sign this?  
**qwen3:8b:** Okay, I'm getting a little scared. Then, where do I sign this?  
**mistral:latest:** Very well, it's just that I'm getting scared now. So, where do I sign this?  
**llama3.2:3b:** I'm getting a little anxious, so where do I sign?  

### 47 · 657.6s · EN→ES
**Original:** Right there at the bottom ma'am. It's perfectly normal to feel nervous before any procedure.  
**gemma3:4b:** Allá abajo, abajo, señora. Es perfectamente normal sentirse nervioso antes de cualquier procedimiento.  
**translategemma:4b:** Exactamente, en la parte inferior, señora. Es completamente normal sentirse nervioso antes de cualquier procedimiento.  
**qwen3:8b:** Justo ahí en la parte inferior, señora. Es perfectamente normal sentirse nervioso antes de cualquier procedimiento.  
**mistral:latest:** Allí, en el fondo. Es normal sentirse nervioso antes de cualquier procedimiento.  
**llama3.2:3b:** Está justo abajo, señora. Es completamente normal sentirse nerviosa antes de cualquier procedimiento.  

### 48 · 663.1s · EN→ES
**Original:** But just know you are in good hands. Do you have any questions or concerns?  
**gemma3:4b:** Pero solo sabe que está usted en buenas manos. ¿Tiene alguna pregunta o inquietud?  
**translategemma:4b:** Pero, por favor, tengan la seguridad de que están en buenas manos. ¿Tienen alguna pregunta o inquietud?  
**qwen3:8b:** Pero sé que estás en buenas manos. ¿Tienes alguna pregunta o inquietud?  
**mistral:latest:** Está en buenas manos. ¿Tienes alguna pregunta o preocupación?  
**llama3.2:3b:** Pero solo sepas que estás en buenas manos. ¿Tienes alguna pregunta o inquietud?  

### 49 · 685.1s · ES→EN
**Original:** No, solo que estoy muy nerviosa.  
**gemma3:4b:** No, just that I’m very nervous.  
**translategemma:4b:** No, I'm just very nervous.  
**qwen3:8b:** No, just that I'm very nervous.  
**mistral:latest:** I'm just very nervous.  
**llama3.2:3b:** No, I'm just very nervous.  

### 50 · 688.3s · ES→EN
**Original:** Eso es todo. Ya van a empezar.  
**gemma3:4b:** That’s it. They’re about to start.  
**translategemma:4b:** That's it. They're about to begin.  
**qwen3:8b:** That's all. They are about to start.  
**mistral:latest:** That's all. They are about to start now.  
**llama3.2:3b:** That's all. They're about to start.  

### 51 · 700.9s · EN→ES
**Original:** Try not to worry so much ma'am. The surgeons are very experienced and will know what to do in case of any complications.  
**gemma3:4b:** No se preocupe tanto, señora. Los cirujanos son muy experimentados y sabrán qué hacer en caso de cualquier complicación.  
**translategemma:4b:** Intente no preocuparse tanto, señora. Los cirujanos son muy experimentados y sabrán qué hacer en caso de cualquier complicación.  
**qwen3:8b:** Trate de no preocuparse tanto señora. Los cirujanos son muy experimentados y sabrán qué hacer en caso de cualquier complicación.  
**mistral:latest:** No te preocupes tanto, señora. Los cirujanos son muy experimentados y sabrán qué hacer en caso de cualquier complicación.  
**llama3.2:3b:** No se preocupe tanto, señora. Los cirujanos son muy experimentados y sabrán qué hacer en caso de cualquier complicación.  

### 52 · 707.9s · EN→ES
**Original:** Well, that's it for me, ma'am. You have to wait for the anesthesiologist to come and discuss with you important information about anesthesia and sign more consent forms.  
**gemma3:4b:** Bueno, eso es todo por mi parte, señora. Tiene que esperar a que venga el anestesiólogo para que le explique información importante sobre la anestesia y firme más formularios de consentimiento.  
**translategemma:4b:** Bueno, eso es todo por mi parte, señora. Tendrá que esperar a que llegue el anestesista para que le explique detalladamente sobre la anestesia y que firme más formularios de consentimiento.  
**qwen3:8b:** Bueno, eso es todo por mi, señora. Usted tiene que esperar a que llegue el anestesiólogo para que le discuta información importante sobre la anestesia y firme más formularios de consentimiento.  
**mistral:latest:** Bien, eso es todo para mí, señora. Tendrás que esperar a que el anestesiólogo venga y te disculpe información importante sobre la anestesia y que tengas que firmar más formularios de consentimiento.  
**llama3.2:3b:** Bueno, eso es todo para mí, señora. Debe esperar a que venga el anestésistico y discuta con usted información importante sobre anestesia y firmar más formularios de consentimiento.  

### 53 · 751.3s · ES→EN
**Original:** Muchas gracias.  
**gemma3:4b:** Thank you very much.  
**translategemma:4b:** Thank you very much.  
**qwen3:8b:** Thank you very much.  
**mistral:latest:** Thank you.  
**llama3.2:3b:** Thank you very much.  

### 54 · 754.9s · EN→ES
**Original:** You are very welcome, ma'am.  
**gemma3:4b:** De nada, señora.  
**translategemma:4b:** Con mucho gusto, señora.  
**qwen3:8b:** Le está muy bien dicho, señora.  
**mistral:latest:** Bienvenida, señora.  
**llama3.2:3b:** Está muy bienvenido, señora.  
