import io

import pdfplumber

from src.extractors.base import BaseExtractor, ExtractionError, RawText


class PdfExtractor(BaseExtractor):
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

        if not content.strip():
            raise ExtractionError(
                f"No extractable text found in {filename!r} "
                "(it may be a scanned image without OCR support)"
            )

        return RawText(content=content, source_filename=filename)
