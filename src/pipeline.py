from src.analyzer.document_analyzer import AnalysisRefusedError, DocumentAnalyzer
from src.analyzer.rule_based_flags import detect_rule_based_flags
from src.analyzer.schemas import AnalysisResult, RedFlag
from src.extractors.base import RawText
from src.extractors.factory import ExtractorFactory
from src.report.report_generator import ReportGenerator

_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}

# Shown when the provider declines to analyze a document. It has to say so
# plainly: a report whose explanation looked normal would imply an AI read
# the document when none did.
_REFUSED_EXPLANATION = {
    "it": (
        "Il provider AI ha rifiutato di analizzare questo documento, di norma perché il suo "
        "filtro di sicurezza lo ha giudicato un tentativo di manipolare l'assistente. "
        "L'analisi in linguaggio naturale non è disponibile; i punti di attenzione qui sotto "
        "vengono dai controlli automatici basati su regole, eseguiti sul testo reale."
    ),
    "en": (
        "The AI provider refused to analyze this document, typically because its safety "
        "filter judged it an attempt to manipulate the assistant. The plain-language "
        "analysis is unavailable; the points of attention below come from the rule-based "
        "checks, run against the real text."
    ),
    "fr": (
        "Le fournisseur d'IA a refusé d'analyser ce document, généralement parce que son "
        "filtre de sécurité y a vu une tentative de manipulation de l'assistant. L'analyse "
        "en langage clair est indisponible ; les points d'attention ci-dessous proviennent "
        "des contrôles automatiques basés sur des règles."
    ),
    "de": (
        "Der KI-Anbieter hat die Analyse dieses Dokuments abgelehnt, in der Regel weil sein "
        "Sicherheitsfilter einen Manipulationsversuch erkannt hat. Die Erklärung in "
        "einfacher Sprache ist nicht verfügbar; die Hinweise unten stammen aus den "
        "regelbasierten Prüfungen."
    ),
    "es": (
        "El proveedor de IA se negó a analizar este documento, normalmente porque su filtro "
        "de seguridad lo consideró un intento de manipular al asistente. El análisis en "
        "lenguaje claro no está disponible; los puntos de atención siguientes provienen de "
        "las comprobaciones automáticas basadas en reglas."
    ),
}

_REFUSED_SUMMARY = {
    "it": "Analisi AI non disponibile: documento rifiutato dal provider.",
    "en": "AI analysis unavailable: the provider refused this document.",
    "fr": "Analyse IA indisponible : document refusé par le fournisseur.",
    "de": "KI-Analyse nicht verfügbar: Dokument vom Anbieter abgelehnt.",
    "es": "Análisis de IA no disponible: documento rechazado por el proveedor.",
}


def _rule_only_result(raw_text: RawText, language: str) -> AnalysisResult:
    """What to report when the provider won't look at the document.

    The deterministic pass still runs, and on a refused document it is the
    pass that matters most: what usually triggers the refusal is an injection
    attempt, which is exactly what the rules detect.
    """
    return AnalysisResult(
        # Nothing classified the document, so claiming a context would be
        # inventing one.
        detected_context="other",
        plain_explanation=_REFUSED_EXPLANATION.get(language, _REFUSED_EXPLANATION["en"]),
        summary=_REFUSED_SUMMARY.get(language, _REFUSED_SUMMARY["en"]),
        red_flags=detect_rule_based_flags(raw_text.content),
    )


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
        match.rule_id = rule_flag.rule_id
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
        try:
            analysis = self._analyzer.analyze(raw_text, language=language)
        except AnalysisRefusedError:
            # A refusal is a verdict, not an outage: degrade to the
            # deterministic checks rather than hand back nothing. An ordinary
            # AnalysisError still propagates, so a broken provider stays loud.
            analysis = _rule_only_result(raw_text, language)
        else:
            analysis.red_flags = _merge_flags(analysis.red_flags, detect_rule_based_flags(raw_text.content))

        pdf_bytes = self._report_generator.generate(analysis, original_filename=raw_text.source_filename)
        return analysis, pdf_bytes

    def render_markdown(self, analysis: AnalysisResult, filename: str) -> str:
        return self._report_generator.generate_markdown(analysis, original_filename=filename)
