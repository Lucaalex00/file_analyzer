from src.analyzer.schemas import AnalysisResult, RedFlag


def test_red_flag_quote_defaults_to_empty_string_when_omitted():
    flag = RedFlag(title="Early termination", description="Costs two months rent.", severity="high")

    assert flag.quote == ""


def test_red_flag_accepts_an_explicit_quote():
    flag = RedFlag(
        title="Early termination",
        description="Costs two months rent.",
        severity="high",
        quote="a penalty equal to two (2) months of rent",
    )

    assert flag.quote == "a penalty equal to two (2) months of rent"


def test_analysis_result_serializes_quote_field():
    result = AnalysisResult(
        detected_context="legal",
        plain_explanation="explanation",
        summary="summary",
        red_flags=[RedFlag(title="t", description="d", severity="low", quote="exact excerpt")],
    )

    assert result.model_dump()["red_flags"][0]["quote"] == "exact excerpt"
