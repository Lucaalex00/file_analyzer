from src.analyzer.document_analyzer import DocumentAnalyzer
from src.analyzer.schemas import AnalysisResult
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
        _, pdf_bytes = self.run_with_analysis(file_bytes, filename, content_type)
        return pdf_bytes

    def run_with_analysis(
        self, file_bytes: bytes, filename: str, content_type: str | None
    ) -> tuple[AnalysisResult, bytes]:
        extractor = self._factory.get_extractor(filename, content_type)
        raw_text = extractor.extract(file_bytes, filename)
        analysis = self._analyzer.analyze(raw_text)
        pdf_bytes = self._report_generator.generate(analysis, original_filename=filename)
        return analysis, pdf_bytes
