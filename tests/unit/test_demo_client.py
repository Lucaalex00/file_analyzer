from src.analyzer.demo_client import DemoAIClient
from src.analyzer.document_analyzer import DocumentAnalyzer
from src.analyzer.document_comparator import DocumentComparator
from src.extractors.base import RawText


class TestDemoAnalysis:
    def test_reuses_real_rule_based_flags_from_the_actual_document(self):
        analyzer = DocumentAnalyzer(client=DemoAIClient(), deployment="demo")
        raw_text = RawText(
            content="This lease renews automatically unless cancelled by either party.",
            source_filename="lease.txt",
        )

        result = analyzer.analyze(raw_text)

        titles = [flag.title for flag in result.red_flags]
        assert "Rinnovo automatico" in titles

    def test_does_not_flag_a_document_with_no_matching_patterns(self):
        analyzer = DocumentAnalyzer(client=DemoAIClient(), deployment="demo")
        raw_text = RawText(content="Just a friendly note about lunch plans.", source_filename="note.txt")

        result = analyzer.analyze(raw_text)

        assert result.red_flags == []

    def test_explanation_clearly_labels_the_output_as_simulated(self):
        analyzer = DocumentAnalyzer(client=DemoAIClient(), deployment="demo")
        raw_text = RawText(content="Some document text.", source_filename="doc.txt")

        result = analyzer.analyze(raw_text)

        assert "demo" in result.plain_explanation.lower()

    def test_responds_in_the_requested_language(self):
        analyzer = DocumentAnalyzer(client=DemoAIClient(), deployment="demo")
        raw_text = RawText(content="Some document text.", source_filename="doc.txt")

        result_en = analyzer.analyze(raw_text, language="en")
        result_it = analyzer.analyze(raw_text, language="it")

        assert result_en.plain_explanation != result_it.plain_explanation
        assert "demo mode" in result_en.plain_explanation.lower()
        assert "modalità demo" in result_it.plain_explanation.lower()

    def test_result_is_a_valid_analysis_result_schema(self):
        analyzer = DocumentAnalyzer(client=DemoAIClient(), deployment="demo")
        raw_text = RawText(content="A contract between two parties.", source_filename="doc.txt")

        result = analyzer.analyze(raw_text)

        assert result.detected_context in {"legal", "work", "personal", "other"}
        assert isinstance(result.summary, str) and result.summary


class TestDemoComparison:
    def test_summary_clearly_labels_the_output_as_simulated(self):
        comparator = DocumentComparator(client=DemoAIClient(), deployment="demo")

        result = comparator.compare("Version A text", "Version B text")

        assert "demo" in result.summary.lower()

    def test_responds_in_the_requested_language(self):
        comparator = DocumentComparator(client=DemoAIClient(), deployment="demo")

        result_en = comparator.compare("A", "B", language="en")
        result_it = comparator.compare("A", "B", language="it")

        assert result_en.summary != result_it.summary
