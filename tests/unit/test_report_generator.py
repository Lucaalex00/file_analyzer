from src.analyzer.schemas import AnalysisResult, RedFlag
from src.report.report_generator import ReportGenerator


def test_generate_returns_non_empty_pdf_bytes():
    analysis = AnalysisResult(
        detected_context="legal",
        plain_explanation="This document is a rental agreement.",
        summary="A one-year lease between landlord and tenant.",
        red_flags=[
            RedFlag(title="Early termination penalty", description="Costs two months rent.", severity="high")
        ],
    )
    generator = ReportGenerator()

    pdf_bytes = generator.generate(analysis, original_filename="lease.pdf")

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_render_html_uses_the_default_brand_name_and_accent_color():
    analysis = AnalysisResult(
        detected_context="personal", plain_explanation="e", summary="s", red_flags=[]
    )
    generator = ReportGenerator()

    html = generator.render_html(analysis, original_filename="letter.txt")

    assert "File Analyzer" in html
    assert "#2563eb" in html


def test_render_html_uses_a_custom_brand_name_and_accent_color():
    analysis = AnalysisResult(
        detected_context="personal", plain_explanation="e", summary="s", red_flags=[]
    )
    generator = ReportGenerator(brand_name="Acme Reports", accent_color="#00aa55")

    html = generator.render_html(analysis, original_filename="letter.txt")

    assert "Acme Reports" in html
    assert "#00aa55" in html


def test_render_html_escapes_llm_supplied_markup():
    analysis = AnalysisResult(
        detected_context="other",
        plain_explanation="<script>alert(1)</script>",
        summary="<img src=x onerror=alert(1)>",
        red_flags=[
            RedFlag(
                title="<style>@import url(http://evil.example/x.css)</style>",
                description="<iframe src='http://evil.example'></iframe>",
                severity="low",
            )
        ],
    )
    generator = ReportGenerator()

    html = generator.render_html(analysis, original_filename="<b>doc</b>.txt")

    assert "<script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<iframe" not in html
    assert "<style>@import" not in html
    assert "<img" not in html
    assert "<b>doc</b>.txt" not in html


def test_generate_markdown_includes_summary_explanation_and_red_flags():
    analysis = AnalysisResult(
        detected_context="legal",
        plain_explanation="This document is a rental agreement.",
        summary="A one-year lease between landlord and tenant.",
        red_flags=[
            RedFlag(
                title="Early termination penalty",
                description="Costs two months rent.",
                severity="high",
                quote="two months rent",
            )
        ],
    )
    generator = ReportGenerator()

    markdown = generator.generate_markdown(analysis, original_filename="lease.pdf")

    assert "A one-year lease between landlord and tenant." in markdown
    assert "This document is a rental agreement." in markdown
    assert "Early termination penalty" in markdown
    assert "high" in markdown


def test_generate_markdown_escapes_llm_supplied_markup():
    analysis = AnalysisResult(
        detected_context="other",
        plain_explanation="<script>alert(1)</script>",
        summary="A summary.",
        red_flags=[],
    )
    generator = ReportGenerator()

    markdown = generator.generate_markdown(analysis, original_filename="doc.txt")

    assert "<script>" not in markdown


def test_generate_markdown_includes_the_brand_name():
    analysis = AnalysisResult(detected_context="work", plain_explanation="e", summary="s", red_flags=[])
    generator = ReportGenerator(brand_name="Acme Reports")

    markdown = generator.generate_markdown(analysis, original_filename="memo.txt")

    assert "Acme Reports" in markdown


def test_generate_markdown_handles_no_red_flags():
    analysis = AnalysisResult(
        detected_context="personal",
        plain_explanation="A friendly letter.",
        summary="Short personal note.",
        red_flags=[],
    )
    generator = ReportGenerator()

    markdown = generator.generate_markdown(analysis, original_filename="letter.txt")

    assert "Short personal note." in markdown


def test_generate_handles_no_red_flags():
    analysis = AnalysisResult(
        detected_context="personal",
        plain_explanation="A friendly letter.",
        summary="Short personal note.",
        red_flags=[],
    )
    generator = ReportGenerator()

    pdf_bytes = generator.generate(analysis, original_filename="letter.txt")

    assert pdf_bytes.startswith(b"%PDF")
