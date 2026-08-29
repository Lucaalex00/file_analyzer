import io
import re

import pdfplumber
import pytesseract

from src.extractors.base import BaseExtractor, ExtractionError, RawText

# Below this space-character density, extracted text is almost certainly
# corrupted rather than genuinely space-free -- real prose in any language
# runs well above this. Some PDF generators (observed against a real
# Italian payslip) embed a font whose ToUnicode CMap maps the space glyph
# to a stray letter instead of an actual space; both pypdf and pdfplumber
# read that same broken mapping, since both extract from the PDF's declared
# text encoding rather than from what's visually rendered.
_MIN_SPACE_DENSITY = 0.06
_MIN_LENGTH_TO_JUDGE = 50

# A document with a corrupted section but otherwise normal, space-heavy
# content (e.g. a clean header/footer around a broken table) can dilute
# the overall space density above _MIN_SPACE_DENSITY even though it's
# unreadable. The reported failure mode always glues a Title-Case word
# directly onto the next one via the stray character, producing a
# lowercase-then-uppercase transition with no space in between -- a
# pattern that almost never occurs in real prose, so its density stays a
# reliable signal even when the space-density check gets diluted.
_MIN_GLUE_DENSITY = 0.01
_LOWER_TO_UPPER_GLUE = re.compile(r"[a-zà-ü][A-ZÀ-Ü]")


def _looks_corrupted(text: str) -> bool:
    if len(text) < _MIN_LENGTH_TO_JUDGE:
        return False
    if (text.count(" ") / len(text)) < _MIN_SPACE_DENSITY:
        return True
    glue_density = len(_LOWER_TO_UPPER_GLUE.findall(text)) / len(text)
    return glue_density > _MIN_GLUE_DENSITY


def _ocr_pdf_pages(file_bytes: bytes) -> str:
    # Renders each page to an image and OCRs it -- reads the actual visual
    # glyphs, sidestepping a broken embedded text encoding entirely.
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        page_texts = []
        for page in pdf.pages:
            image = page.to_image(resolution=200).original
            page_texts.append(pytesseract.image_to_string(image))
    return "\n".join(page_texts)


class PdfExtractor(BaseExtractor):
    def __init__(self, ocr_fn=_ocr_pdf_pages):
        self._ocr_fn = ocr_fn

    def supports(self, filename: str, content_type: str | None) -> bool:
        return filename.lower().endswith(".pdf")

    def extract(self, file_bytes: bytes, filename: str) -> RawText:
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                # pdfplumber reconstructs text by clustering each character's real
                # position on the page rather than following the PDF's internal
                # content stream order -- pypdf's stream-order extraction badly
                # mangles spacing on table-heavy documents (payslips, invoices,
                # forms), inserting stray characters between syllables.
                content = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as exc:  # noqa: BLE001 - pdfplumber/pdfminer don't expose a stable exception type
            raise ExtractionError(f"Could not read PDF {filename!r}") from exc

        if not content.strip() or _looks_corrupted(content):
            ocr_content = self._ocr_fn(file_bytes)
            if ocr_content and ocr_content.strip():
                content = ocr_content

        if not content.strip() or _looks_corrupted(content):
            raise ExtractionError(
                f"No extractable text found in {filename!r} "
                "(it may be a scanned image without OCR support, or use a font "
                "encoding this extractor cannot read reliably)"
            )

        return RawText(content=content, source_filename=filename)
