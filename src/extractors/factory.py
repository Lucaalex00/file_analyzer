from src.extractors.base import BaseExtractor
from src.extractors.pdf_extractor import PdfExtractor
from src.extractors.text_extractor import TextExtractor


class UnsupportedFileTypeError(Exception):
    pass


class ExtractorFactory:
    def __init__(self, extractors: list[BaseExtractor] | None = None):
        self._extractors = extractors if extractors is not None else [PdfExtractor(), TextExtractor()]

    def get_extractor(self, filename: str, content_type: str | None) -> BaseExtractor:
        for extractor in self._extractors:
            if extractor.supports(filename, content_type):
                return extractor
        raise UnsupportedFileTypeError(f"No extractor available for {filename!r}")
