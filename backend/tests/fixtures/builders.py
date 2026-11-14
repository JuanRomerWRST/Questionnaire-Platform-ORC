import io

import pymupdf
from docx import Document
from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFont

from app.core.config import get_settings


def pdf_bytes(lines: list[str]) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=12)
        y += 18
        if y > 780:
            page = document.new_page()
            y = 72
    buffer = io.BytesIO()
    document.save(buffer)
    document.close()
    return buffer.getvalue()


def docx_bytes(paragraphs: list[str], table: list[list[str]] | None = None) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    if table:
        grid = document.add_table(rows=len(table), cols=len(table[0]))
        for row_index, row in enumerate(table):
            for col_index, value in enumerate(row):
                grid.rows[row_index].cells[col_index].text = value
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def xlsx_bytes(sheets: dict[str, list[list[str]]]) -> bytes:
    workbook = Workbook()
    first = True
    for name, rows in sheets.items():
        sheet = workbook.active if first else workbook.create_sheet(name)
        sheet.title = name
        first = False
        for row in rows:
            sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def image_bytes(lines: list[str], *, rotate: bool = False) -> bytes:
    image = Image.new("RGB", (1400, 1800), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=32)
    y = 40
    for line in lines:
        draw.text((40, y), line, fill="black", font=font)
        y += 48
    if rotate:
        image = image.rotate(90, expand=True)
        exif = image.getexif()
        exif[274] = 6
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


SPANISH_LINES = [
    "Cuestionario de hábitos de estudio",
    "1. ¿Cuál es el resultado de 2 + 2?",
    "A) 3",
    "B) 4",
    "C) 5",
    "Respuesta correcta: B",
    "2. El sol es una estrella. (V/F)",
    "Respuesta correcta: V",
    "3. Describa una estrategia que usa para concentrarse.",
    "4. Me resulta fácil empezar las tareas difíciles.",
    "Nunca",
    "A veces",
    "A menudo",
    "Siempre",
    "5. Relaciona cada ciudad con su país.",
    "1 | Roma | A | Italia",
    "2 | Lima | B | Perú",
]


def sample_settings():
    return get_settings()
