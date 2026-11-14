from app.domain.enums.document_type import DocumentType
from app.domain.interfaces.parser import DocumentParser
from app.infrastructure.parsers.docx_parser import DocxParser
from app.infrastructure.parsers.image_parser import ImageParser
from app.infrastructure.parsers.pdf_parser import PdfParser
from app.infrastructure.parsers.xlsx_parser import XlsxParser


def get_parser(document_type: DocumentType) -> DocumentParser:
    parsers: dict[DocumentType, type[DocumentParser]] = {
        DocumentType.PDF: PdfParser,
        DocumentType.DOCX: DocxParser,
        DocumentType.XLSX: XlsxParser,
        DocumentType.PNG: ImageParser,
        DocumentType.JPEG: ImageParser,
        DocumentType.WEBP: ImageParser,
    }
    return parsers[document_type]()
