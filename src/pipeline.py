from src.analyzer.document_analyzer import DocumentAnalyzer
from src.analyzer.rule_based_flags import detect_rule_based_flags
from src.analyzer.schemas import AnalysisResult
from src.extractors.base import RawText
from src.extractors.factory import ExtractorFactory
from src.analyzer.schemas import RedFlag
from src.report.report_generator import ReportGenerator

_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}


def _same_passage(left: str, right: str) -> bool:
    """Whether two quotes point at the same piece of the document.

    Titles can't be used for this: the model writes them as free text in the
    requested language, while the rules' are fixed Italian strings, so
    comparing them finds a match in Italian and never in any other language.
    The quoted passage is the one thing both sources express identically.
    """
    left, right = left.strip().lower(), right.strip().lower()
    if not left or not right:
        return False
    return left in right or right in left


def _merge_flags(llm_flags: list[RedFlag], rule_flags: list[RedFlag]) -> list[RedFlag]:
    """Union of both passes, with flags about the same passage collapsed.

    The model's wording survives (it is specific to the document, where the
    rule's is boilerplate), but the higher of the two severities wins: a rule
    that calls a penalty "high" must not be talked down by a model that rated
    the same sentence "low".
    """
    merged = [flag.model_copy() for flag in llm_flags]

    for rule_flag in rule_flags:
        match = next((f for f in merged if _same_passage(f.quote, rule_flag.quote)), None)
        if match is None:
            merged.append(rule_flag)
            continue
        match.source = "both"
        if _SEVERITY_ORDER[rule_flag.severity] > _SEVERITY_ORDER[match.severity]:
            match.severity = rule_flag.severity

    return merged


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
        analysis.red_flags = _merge_flags(analysis.red_flags, detect_rule_based_flags(raw_text.content))

        pdf_bytes = self._report_generator.generate(analysis, original_filename=raw_text.source_filename)
        return analysis, pdf_bytes

    def render_markdown(self, analysis: AnalysisResult, filename: str) -> str:
        return self._report_generator.generate_markdown(analysis, original_filename=filename)
