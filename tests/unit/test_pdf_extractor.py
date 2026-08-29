import io
from unittest.mock import MagicMock

import pytest
from pypdf import PdfWriter

import src.extractors.pdf_extractor as pdf_extractor_module
from src.extractors.base import ExtractionError
from src.extractors.pdf_extractor import PdfExtractor, _looks_corrupted, _ocr_pdf_pages


def make_pdf_bytes(pages_text: list[str]) -> bytes:
    writer = PdfWriter()
    for text in pages_text:
        writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class TestSupports:
    def test_supports_pdf_extension(self):
        extractor = PdfExtractor()
        assert extractor.supports("contract.PDF", "application/pdf") is True

    def test_does_not_support_txt_extension(self):
        extractor = PdfExtractor()
        assert extractor.supports("contract.txt", "text/plain") is False


def _build_minimal_pdf(stream_content: bytes) -> bytes:
    # Hand-crafted single-page PDF with correctly computed xref offsets --
    # enough object/xref structure for pdfplumber (and pypdf) to parse.
    pdf_content = b"%PDF-1.4\n"
    offset_obj1 = len(pdf_content)

    obj1 = b"1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n"
    pdf_content += obj1
    offset_obj2 = len(pdf_content)

    obj2 = b"2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n"
    pdf_content += obj2
    offset_obj3 = len(pdf_content)

    obj3 = (
        b"3 0 obj\n<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]/"
        b"Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>\nendobj\n"
    )
    pdf_content += obj3
    offset_obj4 = len(pdf_content)

    obj4 = b"4 0 obj\n<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>\nendobj\n"
    pdf_content += obj4
    offset_obj5 = len(pdf_content)

    obj5 = (
        b"5 0 obj\n<</Length "
        + str(len(stream_content)).encode()
        + b">>\nstream\n"
        + stream_content
        + b"\nendstream\nendobj\n"
    )
    pdf_content += obj5

    xref_offset = len(pdf_content)
    xref_table = (
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        + f"{offset_obj1:010d} 00000 n \n".encode()
        + f"{offset_obj2:010d} 00000 n \n".encode()
        + f"{offset_obj3:010d} 00000 n \n".encode()
        + f"{offset_obj4:010d} 00000 n \n".encode()
        + f"{offset_obj5:010d} 00000 n \n".encode()
    )
    pdf_content += xref_table
    pdf_content += b"trailer\n<</Size 6/Root 1 0 R>>\n"
    pdf_content += b"startxref\n" + str(xref_offset).encode() + b"\n%%EOF"
    return pdf_content


class TestExtract:
    def test_raises_extraction_error_on_corrupt_pdf(self):
        extractor = PdfExtractor()

        with pytest.raises(ExtractionError):
            extractor.extract(b"not a real pdf", "broken.pdf")

    def test_raises_extraction_error_on_blank_pdf(self):
        extractor = PdfExtractor()
        pdf_bytes = make_pdf_bytes(["", ""])

        with pytest.raises(ExtractionError):
            extractor.extract(pdf_bytes, "blank.pdf")

    def test_extracts_text_from_real_pdf(self):
        stream_content = b"BT /F1 12 Tf 10 100 Td (Hello Contract) Tj ET\n"
        pdf_content = _build_minimal_pdf(stream_content)

        extractor = PdfExtractor()
        raw = extractor.extract(pdf_content, "contract.pdf")

        assert "Hello Contract" in raw.content
        assert raw.source_filename == "contract.pdf"

    def test_keeps_a_space_between_separately_positioned_table_like_cells(self):
        # Two text runs positioned side by side (like two cells in the same
        # table row), each written with its own Td move rather than a
        # shared text run with a literal space. Naive stream-order text
        # extraction can glue these into "CodiceAzienda" with no space at
        # all -- the exact failure mode reported against a real payslip PDF.
        stream_content = b"BT /F1 12 Tf 10 100 Td (Codice) Tj 80 0 Td (Azienda) Tj ET\n"
        pdf_content = _build_minimal_pdf(stream_content)

        extractor = PdfExtractor()
        raw = extractor.extract(pdf_content, "form.pdf")

        assert "Codice Azienda" in raw.content
        assert "CodiceAzienda" not in raw.content


class TestLooksCorrupted:
    def test_detects_the_space_replaced_by_stray_character_pattern(self):
        # The exact real-world failure mode: every space in the source PDF's
        # embedded font encoding maps to a stray letter instead of a space,
        # so the extracted text has almost no real whitespace at all.
        text = "PERIODOsDIsRETRIBUZIONEsCODICEsAZIENDAsRAGIONEsSOCIALEsINDIRIZZOsCODICEsFISCALE"
        assert _looks_corrupted(text) is True

    def test_does_not_flag_normal_prose(self):
        text = "This is a normal sentence with completely ordinary spacing between each word."
        assert _looks_corrupted(text) is False

    def test_does_not_flag_short_text(self):
        # Short strings naturally have fewer spaces relative to length;
        # judging them by the same density threshold would false-positive.
        assert _looks_corrupted("Hello Contract") is False

    def test_detects_glued_words_even_when_diluted_by_normal_prose(self):
        # Real payslips mix a clean, space-heavy header/footer with a
        # corrupted table -- the overall space density can stay above the
        # threshold even though a whole section is unreadable. The glued
        # Title-Case words (no space, single stray letter) must still be
        # caught via the lowercase-to-uppercase transition signal.
        prefix = (
            "Questo documento contiene diverse informazioni scritte con "
            "normale spaziatura tra le parole italiane comuni. "
        )
        corrupted_section = (
            "PeriodosDisRetribuzionesCodicesAziendasRagionesSocialesIndirizzosCodicesFiscale"
        )
        text = prefix + corrupted_section

        # Sanity check: the diluted whole-text space density alone would
        # NOT have crossed the old threshold -- proving this needs the
        # glue-based signal, not just a lower space-density threshold.
        assert (text.count(" ") / len(text)) >= 0.06

        assert _looks_corrupted(text) is True


class TestOcrPdfPagesReal:
    def test_real_ocr_reads_the_rendered_page_content(self):
        # No mocking here: proves the page.to_image() + pytesseract plumbing
        # itself actually works, complementing the mocked branching tests
        # below (which can't forge a genuinely broken font encoding by hand).
        stream_content = b"BT /F1 24 Tf 10 100 Td (HELLO OCR) Tj ET\n"
        pdf_content = _build_minimal_pdf(stream_content)

        result = _ocr_pdf_pages(pdf_content)

        assert "HELLO" in result.upper()

    def test_ocr_reads_with_italian_language_pack(self, monkeypatch):
        # Payslips are Italian documents -- Tesseract's default (English)
        # language model biases word correction towards English vocabulary,
        # degrading accuracy on Italian text. Verifies the OCR call actually
        # requests the Italian traineddata rather than relying on the default.
        stream_content = b"BT /F1 24 Tf 10 100 Td (HELLO OCR) Tj ET\n"
        pdf_content = _build_minimal_pdf(stream_content)
        fake_image_to_string = MagicMock(return_value="")
        monkeypatch.setattr(pdf_extractor_module.pytesseract, "image_to_string", fake_image_to_string)

        _ocr_pdf_pages(pdf_content)

        fake_image_to_string.assert_called_once()
        assert fake_image_to_string.call_args.kwargs.get("lang") == "ita"


class TestOcrFallback:
    def test_falls_back_to_ocr_when_the_text_layer_looks_corrupted(self):
        garbled_stream = b"BT /F1 12 Tf 10 100 Td (PERIODOsDIsRETRIBUZIONEsCODICEsAZIENDAsRAGIONEsSOCIALE) Tj ET\n"
        pdf_content = _build_minimal_pdf(garbled_stream)
        fake_ocr = MagicMock(return_value="PERIODO DI RETRIBUZIONE CODICE AZIENDA RAGIONE SOCIALE")

        extractor = PdfExtractor(ocr_fn=fake_ocr)
        raw = extractor.extract(pdf_content, "payslip.pdf")

        fake_ocr.assert_called_once()
        assert raw.content == "PERIODO DI RETRIBUZIONE CODICE AZIENDA RAGIONE SOCIALE"

    def test_does_not_fall_back_when_the_text_layer_looks_fine(self):
        stream_content = b"BT /F1 12 Tf 10 100 Td (Hello Contract) Tj ET\n"
        pdf_content = _build_minimal_pdf(stream_content)
        fake_ocr = MagicMock(return_value="should not be used")

        extractor = PdfExtractor(ocr_fn=fake_ocr)
        raw = extractor.extract(pdf_content, "contract.pdf")

        fake_ocr.assert_not_called()
        assert "Hello Contract" in raw.content

    def test_raises_extraction_error_when_ocr_fallback_also_finds_nothing(self):
        garbled_stream = b"BT /F1 12 Tf 10 100 Td (AsBsCsDsEsFsGsHsIsJsKsLsMsNsOsPsQsRsSsTsUsVsWsXsYsZ) Tj ET\n"
        pdf_content = _build_minimal_pdf(garbled_stream)
        fake_ocr = MagicMock(return_value="")

        extractor = PdfExtractor(ocr_fn=fake_ocr)

        with pytest.raises(ExtractionError):
            extractor.extract(pdf_content, "blank-scan.pdf")
