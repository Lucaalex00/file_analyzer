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


def _preprocess_for_ocr(image):
    # Payslips are dense tables with thin border lines that Tesseract can
    # misread as stray characters ("[", "|") -- a plain grayscale threshold
    # removes faint lines and background shading while keeping solid text.
    grayscale = image.convert("L")
    return grayscale.point(lambda pixel: 255 if pixel > 150 else 0)


_TABLE_RESOLUTION = 300
_POINTS_PER_INCH = 72
_FOOTER_LABEL = "--- Altro contenuto nella pagina ---"


def _ocr_region(image, bbox, scale, psm=None):
    # bbox is in pdfplumber's top-down point space (same origin as the
    # rendered image); scale converts points to the image's pixel space.
    x0, top, x1, bottom = bbox
    left, upper, right, lower = (round(x0 * scale), round(top * scale), round(x1 * scale), round(bottom * scale))
    if right <= left or lower <= upper:
        return ""
    crop = image.crop((left, upper, right, lower))
    config = f"--psm {psm}" if psm is not None else ""
    return pytesseract.image_to_string(_preprocess_for_ocr(crop), lang="ita", config=config).strip()


def _reconstruct_table_as_grid(image, table, scale):
    # Each detected table is OCR'd cell by cell rather than as one page-wide
    # blob: a single cell is short, unambiguous text, free of the
    # neighbouring borders/side labels that confuse Tesseract when it has
    # to interpret an entire tabular layout in one pass.
    rows_text = []
    for row in table.rows:
        # psm 11 ("sparse text") reliably reads a lone short word/value out
        # of a cell crop; psm 6/7 were observed to return nothing at all on
        # cell-sized crops despite the same crop OCRing fine unconstrained.
        cell_texts = [_ocr_region(image, cell_bbox, scale, psm=11) if cell_bbox else "" for cell_bbox in row.cells]
        rows_text.append(" | ".join(cell_texts))
    return "\n".join(rows_text)


def _ocr_page_with_tables(page, image, scale):
    tables = page.find_tables()
    if not tables:
        return pytesseract.image_to_string(_preprocess_for_ocr(image), lang="ita")

    tables_top_to_bottom = sorted(tables, key=lambda t: t.bbox[1])
    header_bottom = tables_top_to_bottom[0].bbox[1]
    footer_top = max(t.bbox[3] for t in tables_top_to_bottom)

    sections = []

    header_text = _ocr_region(image, (0, 0, page.width, header_bottom), scale)
    if header_text:
        sections.append(header_text)

    for table in tables_top_to_bottom:
        sections.append(_reconstruct_table_as_grid(image, table, scale))

    # Content below the lowest table (bank ads, app promos, software vendor
    # attribution, in every real payslip seen so far) is never discarded --
    # guessing "irrelevant" on a financial/legal document risks losing
    # something that matters. It's kept, just clearly set apart from the
    # reconstructed table data so the two don't visually blend together.
    footer_text = _ocr_region(image, (0, footer_top, page.width, page.height), scale)
    if footer_text:
        sections.append(f"{_FOOTER_LABEL}\n{footer_text}")

    return "\n\n".join(sections)


def _ocr_pdf_pages(file_bytes: bytes) -> str:
    # Renders each page to an image and OCRs it -- reads the actual visual
    # glyphs, sidestepping a broken embedded text encoding entirely.
    scale = _TABLE_RESOLUTION / _POINTS_PER_INCH
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        page_texts = []
        for page in pdf.pages:
            image = page.to_image(resolution=_TABLE_RESOLUTION).original
            # Payslips are Italian documents; the Italian traineddata's
            # language model corrects OCR ambiguities towards Italian
            # vocabulary instead of English.
            page_texts.append(_ocr_page_with_tables(page, image, scale))
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
