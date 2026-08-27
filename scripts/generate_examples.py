"""Regenerate the example PDF reports in examples/ by running the real pipeline
against the sample input files. Requires a working .env with real Azure OpenAI
credentials — this is a manual/local step, not run in CI.

Usage: python scripts/generate_examples.py
"""

from pathlib import Path

from src.api.dependencies import get_pipeline

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"

SAMPLE_FILES = [
    "sample_lease_contract.txt",
    "sample_work_memo.txt",
]


def main() -> None:
    pipeline = get_pipeline()

    for filename in SAMPLE_FILES:
        source_path = EXAMPLES_DIR / filename
        file_bytes = source_path.read_bytes()

        pdf_bytes = pipeline.run(file_bytes=file_bytes, filename=filename, content_type="text/plain")

        output_path = source_path.with_suffix(".report.pdf")
        output_path.write_bytes(pdf_bytes)
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
