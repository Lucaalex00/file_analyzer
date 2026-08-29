import io
from unittest.mock import MagicMock

import pytest
from PIL import Image, ImageDraw, ImageFont

from src.extractors.base import ExtractionError
from src.extractors.image_extractor import ImageExtractor


def make_image_bytes(text: str) -> bytes:
    image = Image.new("RGB", (600, 150), color="white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=40)
    draw.text((10, 40), text, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class TestSupports:
    def test_supports_png_extension(self):
        extractor = ImageExtractor()
        assert extractor.supports("scan.PNG", "image/png") is True

    def test_supports_jpg_and_jpeg_extensions(self):
        extractor = ImageExtractor()
        assert extractor.supports("scan.jpg", "image/jpeg") is True
        assert extractor.supports("scan.jpeg", "image/jpeg") is True

    def test_does_not_support_pdf_extension(self):
        extractor = ImageExtractor()
        assert extractor.supports("scan.pdf", "application/pdf") is False


class TestExtract:
    def test_extracts_real_text_from_an_image_via_ocr(self):
        extractor = ImageExtractor()
        image_bytes = make_image_bytes("HELLO WORLD")

        raw = extractor.extract(image_bytes, "scan.png")

        assert "HELLO WORLD" in raw.content.upper()
        assert raw.source_filename == "scan.png"

    def test_raises_extraction_error_on_corrupt_image(self):
        extractor = ImageExtractor()

        with pytest.raises(ExtractionError):
            extractor.extract(b"not a real image", "scan.png")

    def test_raises_extraction_error_when_no_text_recognized(self):
        extractor = ImageExtractor()
        blank_image = Image.new("RGB", (100, 100), color="white")
        buffer = io.BytesIO()
        blank_image.save(buffer, format="PNG")

        with pytest.raises(ExtractionError):
            extractor.extract(buffer.getvalue(), "blank.png")

    def test_raises_extraction_error_when_ocr_confidence_is_low(self):
        # Simulates a logo/decorative graphic: OCR produced *some* text
        # (otherwise the empty-content check above would already catch it)
        # but Tesseract's own confidence in it is too low to trust.
        fake_confidence = MagicMock(return_value=10.0)
        extractor = ImageExtractor(confidence_fn=fake_confidence)
        image_bytes = make_image_bytes("HELLO WORLD")

        with pytest.raises(ExtractionError):
            extractor.extract(image_bytes, "logo.png")

    def test_does_not_raise_when_ocr_confidence_is_high(self):
        fake_confidence = MagicMock(return_value=90.0)
        extractor = ImageExtractor(confidence_fn=fake_confidence)
        image_bytes = make_image_bytes("HELLO WORLD")

        raw = extractor.extract(image_bytes, "scan.png")

        assert "HELLO WORLD" in raw.content.upper()
