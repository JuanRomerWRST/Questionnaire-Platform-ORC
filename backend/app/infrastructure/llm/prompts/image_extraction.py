IMAGE_HINT = """
Analiza visualmente la imagen del cuestionario y extrae su contenido
respetando fielmente la información visible y su estructura espacial.

## 1. ESTRUCTURA VISUAL
- Respeta el orden de lectura de la imagen.
- Identifica correctamente columnas, tablas, filas y bloques de contenido.
- Conserva la relación entre cada enunciado y sus alternativas.
- No asignes alternativas a preguntas diferentes.
- Identifica correctamente la numeración y los identificadores originales.
- Considera la posición de casillas, círculos, marcas y resaltados.
- Si una pregunta continúa en otra sección de la imagen, conserva su relación.

## 2. TEXTO Y LEGIBILIDAD
- Transcribe el texto visible.
- Un cuadro o un glifo ausente dentro de una palabra se completa
  cuando las letras restantes dejan una sola lectura.
- No completes una palabra que admita varias lecturas ni una a la
  que le falte la mayor parte de las letras.
- Conserva los fragmentos legibles de cada ítem.
- Si un fragmento afecta la interpretación del ítem, marca incierto=true.
- No descartes un ítem completo porque una parte de su contenido sea ilegible.
- No corrijas ni reformules errores ortográficos del documento.

## 3. ALTERNATIVAS Y RESPUESTAS
- Conserva todas las alternativas identificables y sus identificadores.
- No inventes alternativas faltantes.
- No deduzcas respuestas correctas mediante conocimientos externos.
- Identifica una respuesta correcta únicamente cuando exista una marca o indicación explícita e inequívoca.
- No confundas resaltados decorativos, tachaduras o anotaciones con respuestas correctas.
- Si no puedes determinar con certeza una respuesta, utiliza null.

## 4. CASOS ESPECIALES
- Verdadero/Falso: si únicamente aparecen V/F, Verdadero/Falso o True/False, incluye exactamente dos alternativas con valores V y F.
- Emparejamiento: identifica ambas columnas y conserva las correspondencias únicamente cuando sean explícitas.
- Selección múltiple: conserva las alternativas y las marcas visibles.
- Escala Likert: conserva el orden y los valores originales de la escala.
- Desarrollo: conserva el enunciado sin inventar alternativas.

## 5. INCERTIDUMBRE
- Marca incierto=true cuando exista texto ilegible, numeración ambigua,
  relación espacial dudosa o clasificación incierta.
- Un ítem incierto no debe afectar la extracción de los demás.
- Prioriza conservar información parcial antes que inventar información.

La fidelidad visual y documental tiene prioridad sobre la completitud.
No inventes preguntas, alternativas ni respuestas.
Un cuadro dentro de una palabra sí puede restaurarse cuando solo
una lectura completa esa palabra.
"""
