from src.analyzer.document_analyzer import DocumentAnalyzer
from src.analyzer.rule_based_flags import detect_rule_based_flags
from src.analyzer.schemas import AnalysisResult
from src.extractors.base import RawText
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

    def run(
        self, file_bytes: bytes, filename: str, content_type: str | None, language: str = "it"
    ) -> bytes:
        _, pdf_bytes = self.run_with_analysis(file_bytes, filename, content_type, language=language)
        return pdf_bytes

    def run_with_analysis(
        self, file_bytes: bytes, filename: str, content_type: str | None, language: str = "it"
    ) -> tuple[AnalysisResult, bytes]:
        extractor = self._factory.get_extractor(filename, content_type)
        raw_text = extractor.extract(file_bytes, filename)
        return self._analyze_raw_text(raw_text, language=language)

    def run_with_analysis_from_text(
        self, text: str, filename: str, language: str = "it"
    ) -> tuple[AnalysisResult, bytes]:
        """Same as run_with_analysis, but for text already extracted elsewhere
        (e.g. the frontend's preview call) -- skips extraction entirely so the
        document isn't re-OCR'd/re-parsed a second time."""
        raw_text = RawText(content=text, source_filename=filename)
        return self._analyze_raw_text(raw_text, language=language)

    def _analyze_raw_text(self, raw_text: RawText, language: str) -> tuple[AnalysisResult, bytes]:
        analysis = self._analyzer.analyze(raw_text, language=language)

        rule_based_flags = detect_rule_based_flags(raw_text.content)
        existing_titles = {flag.title for flag in analysis.red_flags}
        analysis.red_flags = analysis.red_flags + [
            flag for flag in rule_based_flags if flag.title not in existing_titles
        ]

        pdf_bytes = self._report_generator.generate(analysis, original_filename=raw_text.source_filename)
        return analysis, pdf_bytes

    def render_markdown(self, analysis: AnalysisResult, filename: str) -> str:
        return self._report_generator.generate_markdown(analysis, original_filename=filename)
