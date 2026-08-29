import io

import pytesseract
from PIL import Image, UnidentifiedImageError

from src.extractors.base import BaseExtractor, ExtractionError, RawText

_SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")


class ImageExtractor(BaseExtractor):
    def supports(self, filename: str, content_type: str | None) -> bool:
        return filename.lower().endswith(_SUPPORTED_EXTENSIONS)

    def extract(self, file_bytes: bytes, filename: str) -> RawText:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            content = pytesseract.image_to_string(image)
        except UnidentifiedImageError as exc:
            raise ExtractionError(f"Could not read image {filename!r}") from exc

        if not content.strip():
            raise ExtractionError(
                f"No text could be recognized in {filename!r} (the image may not contain readable text)"
            )

        return RawText(content=content, source_filename=filename)
