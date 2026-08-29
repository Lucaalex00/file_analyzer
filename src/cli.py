"""Standalone CLI: runs the same pipeline as the API, no server needed.

Usage:
    python -m src.cli extract contract.pdf
    python -m src.cli analyze contract.pdf --language en --format markdown
    python -m src.cli compare v1.txt v2.txt

Requires the same environment variables as the API (see .env.example) --
at minimum AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY for `analyze`
and `compare` (`extract` needs neither, it never calls the LLM).
"""

import argparse
import sys
from pathlib import Path

from src.api.dependencies import get_document_comparator, get_extractor_factory, get_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="file-analyzer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract raw text from a file, no LLM call")
    extract_parser.add_argument("file", type=Path)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a file and write a report")
    analyze_parser.add_argument("file", type=Path)
    analyze_parser.add_argument("--language", default="it")
    analyze_parser.add_argument("--format", choices=["pdf", "markdown"], default="pdf")
    analyze_parser.add_argument("--output", type=Path, default=None)

    compare_parser = subparsers.add_parser("compare", help="Compare two versions of a document")
    compare_parser.add_argument("file_a", type=Path)
    compare_parser.add_argument("file_b", type=Path)
    compare_parser.add_argument("--language", default="it")

    return parser


def run_extract(args: argparse.Namespace, factory) -> str:
    file_bytes = args.file.read_bytes()
    extractor = factory.get_extractor(args.file.name, None)
    return extractor.extract(file_bytes, args.file.name).content


def run_analyze(args: argparse.Namespace, pipeline) -> Path:
    file_bytes = args.file.read_bytes()

    if args.format == "pdf":
        content = pipeline.run(
            file_bytes=file_bytes, filename=args.file.name, content_type=None, language=args.language
        )
        output_path = args.output or args.file.with_suffix(".report.pdf")
        output_path.write_bytes(content)
    else:
        analysis, _ = pipeline.run_with_analysis(
            file_bytes=file_bytes, filename=args.file.name, content_type=None, language=args.language
        )
        markdown = pipeline.render_markdown(analysis, args.file.name)
        output_path = args.output or args.file.with_suffix(".report.md")
        output_path.write_text(markdown, encoding="utf-8")

    return output_path


def run_compare(args: argparse.Namespace, comparator, factory) -> str:
    text_a = factory.get_extractor(args.file_a.name, None).extract(args.file_a.read_bytes(), args.file_a.name).content
    text_b = factory.get_extractor(args.file_b.name, None).extract(args.file_b.read_bytes(), args.file_b.name).content
    result = comparator.compare(text_a, text_b, language=args.language)
    return result.model_dump_json(indent=2)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    factory = get_extractor_factory()

    if args.command == "extract":
        print(run_extract(args, factory))
    elif args.command == "analyze":
        output_path = run_analyze(args, get_pipeline())
        print(f"Wrote {output_path}")
    elif args.command == "compare":
        print(run_compare(args, get_document_comparator(), factory))


if __name__ == "__main__":
    sys.exit(main())
