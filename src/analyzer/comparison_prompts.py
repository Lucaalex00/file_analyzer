from src.analyzer.prompts import LANGUAGE_NAMES, MAX_DOCUMENT_CHARS

COMPARISON_SYSTEM_PROMPT = """You compare two versions of a document and report what \
changed between them. You must respond with a single JSON object matching exactly \
this schema:

{
  "summary": string,  // 2-4 sentence summary of what changed overall
  "differences": [
    {"title": string, "description": string, "change_type": "added" | "removed" | "modified"}
  ]
}

differences lists concrete clauses, terms, or sections that were added, removed, or \
modified between version A and version B - return an empty list if the two versions \
are effectively identical. Respond with JSON only, no other text."""


def build_comparison_user_prompt(text_a: str, text_b: str, language: str = "it") -> str:
    language_name = LANGUAGE_NAMES.get(language, language)
    truncated_a = text_a[:MAX_DOCUMENT_CHARS]
    truncated_b = text_b[:MAX_DOCUMENT_CHARS]
    return (
        f"Respond in {language_name}.\n\n"
        f"Version A:\n\n{truncated_a}\n\n"
        f"Version B:\n\n{truncated_b}"
    )
