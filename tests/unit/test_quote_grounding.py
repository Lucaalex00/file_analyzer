from src.analyzer.quote_grounding import ground_quote

DOCUMENT = (
    "Early termination: If the Tenant terminates this lease before the end of the term,\n"
    "the Tenant must pay a penalty equal to two (2) months of rent.\n"
)


def test_returns_an_exact_quote_unchanged():
    assert ground_quote("two (2) months of rent", DOCUMENT) == "two (2) months of rent"


def test_realigns_a_quote_whose_line_breaks_differ():
    # Extracted text carries hard line breaks the model doesn't reproduce in
    # the same places. The quote is genuine, so it must be recovered -- and
    # returned as the document's own text, since that is what the frontend
    # searches for when highlighting.
    quoted_by_model = "before the end of the term, the Tenant must pay a penalty"

    grounded = ground_quote(quoted_by_model, DOCUMENT)

    assert grounded in DOCUMENT
    assert "end of the term,\nthe Tenant must pay a penalty" in grounded


def test_collapses_repeated_whitespace_too():
    assert ground_quote("Early    termination:", DOCUMENT) == "Early termination:"


def test_returns_none_for_a_quote_the_document_never_contained():
    assert ground_quote("a sentence that was never written", DOCUMENT) is None


def test_returns_none_for_an_empty_quote():
    assert ground_quote("", DOCUMENT) is None


def test_ignores_surrounding_whitespace_in_the_model_quote():
    assert ground_quote("  two (2) months  ", DOCUMENT) == "two (2) months"
