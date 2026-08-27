import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from src.extractors.base import BaseExtractor, ExtractionError, RawText


class PdfExtractor(BaseExtractor):
    def supports(self, filename: str, content_type: str | None) -> bool:
        return filename.lower().endswith(".pdf")

    def extract(self, file_bytes: bytes, filename: str) -> RawText:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        except (PdfReadError, ValueError) as exc:
            raise ExtractionError(f"Could not read PDF {filename!r}") from exc

        if not content.strip():
            raise ExtractionError(
                f"No extractable text found in {filename!r} "
                "(it may be a scanned image without OCR support)"
            )

        return RawText(content=content, source_filename=filename)
