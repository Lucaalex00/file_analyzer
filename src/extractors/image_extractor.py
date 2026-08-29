import io

import pytesseract
from PIL import Image, UnidentifiedImageError

from src.extractors.base import BaseExtractor, ExtractionError, RawText
from src.extractors.ocr_utils import mean_ocr_confidence, preprocess_for_ocr

_SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")

# Below this, Tesseract's own confidence in the words it found is low
# enough that the "text" is more likely hallucinated from a logo, a
# graphic, or decorative typography than genuinely read.
_MIN_MEAN_CONFIDENCE = 40


class ImageExtractor(BaseExtractor):
    def __init__(self, confidence_fn=mean_ocr_confidence):
        self._confidence_fn = confidence_fn

    def supports(self, filename: str, content_type: str | None) -> bool:
        return filename.lower().endswith(_SUPPORTED_EXTENSIONS)

    def extract(self, file_bytes: bytes, filename: str) -> RawText:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            preprocessed = preprocess_for_ocr(image)
            content = pytesseract.image_to_string(preprocessed, lang="ita")
        except UnidentifiedImageError as exc:
            raise ExtractionError(f"Could not read image {filename!r}") from exc

        if not content.strip():
            raise ExtractionError(
                f"No text could be recognized in {filename!r} (the image may not contain readable text)"
            )

        if self._confidence_fn(preprocessed) < _MIN_MEAN_CONFIDENCE:
            raise ExtractionError(
                f"{filename!r} does not look like it contains reliably readable text "
                "(it may be a logo, a graphic, or a decorative image)"
            )

        return RawText(content=content, source_filename=filename)
