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
