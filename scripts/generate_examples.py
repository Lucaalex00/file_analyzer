"""Regenerate the example PDF reports committed in examples/.

Runs the real pipeline against every bundled sample, so the repo shows real
output to someone browsing it without any credentials configured. Needs a
working .env with real Azure OpenAI or Groq credentials -- a manual step,
never run in CI.

The sample list comes from src/api/example_documents.py, the same allowlist
the web UI offers, so the two can't drift apart.

Usage: docker compose exec api python -m scripts.generate_examples
"""

from src.api.dependencies import get_pipeline
from src.api.example_documents import list_examples


def main() -> None:
    pipeline = get_pipeline()

    for example in list_examples():
        pdf_bytes = pipeline.run(
            file_bytes=example.path.read_bytes(),
            filename=example.filename,
            content_type=example.media_type,
        )

        output_path = example.path.with_suffix(".report.pdf")
        output_path.write_bytes(pdf_bytes)
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
