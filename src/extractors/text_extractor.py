import io
from zipfile import BadZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from src.extractors.base import BaseExtractor, ExtractionError, RawText

_SUPPORTED_EXTENSIONS = (".txt", ".docx")


class TextExtractor(BaseExtractor):
    def supports(self, filename: str, content_type: str | None) -> bool:
        return filename.lower().endswith(_SUPPORTED_EXTENSIONS)

    def extract(self, file_bytes: bytes, filename: str) -> RawText:
        if filename.lower().endswith(".docx"):
            content = self._extract_docx(file_bytes)
        else:
            content = self._extract_txt(file_bytes)

        if not content.strip():
            raise ExtractionError(f"No readable text found in {filename!r}")

        return RawText(content=content, source_filename=filename)

    def _extract_txt(self, file_bytes: bytes) -> str:
        return file_bytes.decode("utf-8", errors="ignore")

    def _extract_docx(self, file_bytes: bytes) -> str:
        try:
            document = Document(io.BytesIO(file_bytes))
        except (PackageNotFoundError, BadZipFile) as exc:
            raise ExtractionError("File is not a valid .docx document") from exc

        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
