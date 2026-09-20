"""Tie a red flag's quote back to the document it claims to come from.

The model is asked for verbatim excerpts and largely obliges, but extracted
text carries hard line breaks (PDF columns, OCR line boxes) that the model
doesn't reproduce in the same places. A plain substring check therefore
rejects genuine quotes: measured on the bundled samples, 9 of 14 quotes
failed it while every one of them was real once whitespace was ignored.

So quotes are matched on whitespace-normalised text, then returned as the
document's *own* substring -- the frontend highlights by searching the raw
extracted text, so a quote that differs by a newline highlights nothing.
"""

import re

_WHITESPACE = re.compile(r"\s+")


def _normalise(text: str) -> tuple[str, list[int]]:
    """Collapse whitespace, keeping each kept character's original index."""
    out: list[str] = []
    origin: list[int] = []
    previous_was_space = True  # trims leading whitespace

    for index, char in enumerate(text):
        if char.isspace():
            if previous_was_space:
                continue
            out.append(" ")
            origin.append(index)
            previous_was_space = True
        else:
            out.append(char)
            origin.append(index)
            previous_was_space = False

    while out and out[-1] == " ":
        out.pop()
        origin.pop()

    return "".join(out), origin


def ground_quote(quote: str, document_text: str) -> str | None:
    """The document's own wording for `quote`, or None if it isn't in there."""
    if not quote.strip():
        return None

    if quote in document_text:
        return quote

    normalised_document, origin = _normalise(document_text)
    normalised_quote = _WHITESPACE.sub(" ", quote).strip()
    if not normalised_quote:
        return None

    position = normalised_document.find(normalised_quote)
    if position == -1:
        return None

    start = origin[position]
    end = origin[position + len(normalised_quote) - 1]
    return document_text[start : end + 1]
