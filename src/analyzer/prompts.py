SYSTEM_PROMPT = """You are a document analysis assistant. You read a document and \
explain it to a non-expert. You must respond with a single JSON object matching \
exactly this schema:

{
  "detected_context": "legal" | "work" | "personal" | "other",
  "plain_explanation": string,  // clear explanation in plain language, no jargon
  "summary": string,            // 2-4 sentence summary of the document
  "red_flags": [
    {
      "title": string,
      "description": string,
      "severity": "low" | "medium" | "high",
      "quote": string  // the exact excerpt from the document that triggered this flag
    }
  ]
}

detected_context is your best guess at the document's domain based on its content \
(a contract or court notice is "legal", a work email or report is "work", a personal \
letter or medical result is "personal", anything else is "other"). red_flags lists \
concerning clauses, deadlines, unusual requests, or risks a non-expert should notice \
- return an empty list if there are none. quote must be copied verbatim from the \
document (exact substring, not paraphrased) so it can be highlighted back in the \
original text - use an empty string only if no specific excerpt applies. Respond \
with JSON only, no other text."""


# Hard cap on document text sent to the LLM. An accepted upload can be up to
# MAX_FILE_SIZE_BYTES (10MB by default), far past any realistic context window;
# a plain truncation is enough for this MVP.
MAX_DOCUMENT_CHARS = 80_000

LANGUAGE_NAMES = {
    "it": "Italian",
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
}


def build_user_prompt(document_text: str, language: str = "it") -> str:
    language_name = LANGUAGE_NAMES.get(language, language)
    truncated = document_text[:MAX_DOCUMENT_CHARS]
    return (
        f"Respond in {language_name} for plain_explanation, summary, and each red flag's "
        "title/description. detected_context, severity, and quote are not translated "
        f"(quote must stay verbatim in the document's own language).\n\n"
        f"Analyze the following document:\n\n{truncated}"
    )
