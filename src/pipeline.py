from src.analyzer.document_analyzer import DocumentAnalyzer
from src.extractors.factory import ExtractorFactory
from src.report.report_generator import ReportGenerator


class DocumentAnalysisPipeline:
    def __init__(
        self,
        factory: ExtractorFactory,
        analyzer: DocumentAnalyzer,
        report_generator: ReportGenerator,
    ):
        self._factory = factory
        self._analyzer = analyzer
        self._report_generator = report_generator

    def run(self, file_bytes: bytes, filename: str, content_type: str | None) -> bytes:
        extractor = self._factory.get_extractor(filename, content_type)
        raw_text = extractor.extract(file_bytes, filename)
        analysis = self._analyzer.analyze(raw_text)
        return self._report_generator.generate(analysis, original_filename=filename)
