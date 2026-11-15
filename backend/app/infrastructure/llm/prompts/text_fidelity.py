TEXT_FIDELITY_RULES = """
## FIDELIDAD TEXTUAL ABSOLUTA

La transcripción literal tiene prioridad sobre cualquier interpretación
o clasificación del contenido.

1. Copia literalmente el texto visible en el documento.
2. No agregues palabras, símbolos, aclaraciones, etiquetas ni explicaciones.
3. No completes frases aunque su significado parezca evidente.
4. No corrijas ortografía, gramática, puntuación ni errores tipográficos.
5. No traduzcas ni reformules el contenido.
6. No agregues indicadores del tipo (V/F), (A/B/C), (Selección múltiple)
   o similares si no aparecen explícitamente en el documento.
7. No incorpores el tipo de pregunta dentro del enunciado.
8. No agregues información obtenida de conocimientos externos.
9. Conserva los signos de interrogación, tildes, mayúsculas y caracteres
   especiales tal como aparecen.
10. Si un carácter es un cuadro o un reemplazo dentro de una palabra
    y las letras restantes dejan una sola lectura, escribe ese carácter.
    "h□bitos" se escribe "hábitos". "□Cu□l" se escribe "¿Cuál".
11. Si hay más de una lectura posible, no sustituyas el carácter.
    Conserva el fragmento legible y marca incierto=true.

IMPORTANTE:
La clasificación de una pregunta es un dato independiente de su transcripción.
Identificar una pregunta como verdadero_falso NO autoriza a modificar
su enunciado ni a agregar "(V/F)".

Ejemplo:
Documento:
"El sol es una estrella."

Resultado:
enunciado: "El sol es una estrella."

INCORRECTO:
enunciado: "El sol es una estrella. (V/F)"

Nunca agregues contenido que no esté presente en el documento.
"""
