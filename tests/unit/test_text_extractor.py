import io

import pytest
from docx import Document

from src.extractors.base import ExtractionError
from src.extractors.text_extractor import TextExtractor


def make_docx_bytes(paragraphs: list[str]) -> bytes:
    doc = Document()
    for paragraph in paragraphs:
        doc.add_paragraph(paragraph)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


class TestSupports:
    def test_supports_txt_extension(self):
        extractor = TextExtractor()
        assert extractor.supports("contract.txt", "text/plain") is True

    def test_supports_docx_extension(self):
        extractor = TextExtractor()
        assert extractor.supports("contract.DOCX", None) is True

    def test_does_not_support_pdf_extension(self):
        extractor = TextExtractor()
        assert extractor.supports("contract.pdf", "application/pdf") is False


class TestExtractTxt:
    def test_extracts_plain_text_content(self):
        extractor = TextExtractor()
        raw = extractor.extract(b"Hello, this is a contract.", "note.txt")

        assert raw.content == "Hello, this is a contract."
        assert raw.source_filename == "note.txt"

    def test_raises_extraction_error_on_empty_txt(self):
        extractor = TextExtractor()

        with pytest.raises(ExtractionError):
            extractor.extract(b"   \n  ", "empty.txt")


class TestExtractDocx:
    def test_extracts_docx_paragraphs_joined(self):
        extractor = TextExtractor()
        docx_bytes = make_docx_bytes(["First paragraph.", "Second paragraph."])

        raw = extractor.extract(docx_bytes, "contract.docx")

        assert raw.content == "First paragraph.\nSecond paragraph."
        assert raw.source_filename == "contract.docx"

    def test_raises_extraction_error_on_empty_docx(self):
        extractor = TextExtractor()
        docx_bytes = make_docx_bytes([])

        with pytest.raises(ExtractionError):
            extractor.extract(docx_bytes, "empty.docx")

    def test_raises_extraction_error_on_corrupt_docx(self):
        extractor = TextExtractor()

        with pytest.raises(ExtractionError):
            extractor.extract(b"not a real docx file", "broken.docx")
