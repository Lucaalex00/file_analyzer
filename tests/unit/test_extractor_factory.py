import pytest

from src.extractors.base import BaseExtractor, RawText
from src.extractors.factory import ExtractorFactory, UnsupportedFileTypeError
from src.extractors.pdf_extractor import PdfExtractor
from src.extractors.text_extractor import TextExtractor


class FakeExtractor(BaseExtractor):
    def __init__(self, extension: str):
        self.extension = extension

    def supports(self, filename, content_type):
        return filename.lower().endswith(self.extension)

    def extract(self, file_bytes, filename):
        return RawText(content="fake", source_filename=filename)


def test_default_factory_selects_pdf_extractor():
    factory = ExtractorFactory()
    extractor = factory.get_extractor("contract.pdf", "application/pdf")
    assert isinstance(extractor, PdfExtractor)


def test_default_factory_selects_text_extractor_for_txt():
    factory = ExtractorFactory()
    extractor = factory.get_extractor("note.txt", "text/plain")
    assert isinstance(extractor, TextExtractor)


def test_default_factory_selects_text_extractor_for_docx():
    factory = ExtractorFactory()
    extractor = factory.get_extractor("note.docx", None)
    assert isinstance(extractor, TextExtractor)


def test_raises_unsupported_file_type_for_unknown_extension():
    factory = ExtractorFactory()

    with pytest.raises(UnsupportedFileTypeError):
        factory.get_extractor("photo.png", "image/png")


def test_uses_injected_extractors_list_and_first_match_wins():
    factory = ExtractorFactory(extractors=[FakeExtractor(".log")])
    extractor = factory.get_extractor("run.log", None)
    assert isinstance(extractor, FakeExtractor)
