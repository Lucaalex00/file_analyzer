from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from src.analyzer.schemas import AnalysisResult

_TEMPLATE_DIR = Path(__file__).parent / "templates"


class ReportGenerator:
    def __init__(self):
        self._env = Environment(
            loader=FileSystemLoader(_TEMPLATE_DIR),
            autoescape=select_autoescape(["html"]),
        )
        self._template = self._env.get_template("report.html.j2")

    def generate(self, analysis: AnalysisResult, original_filename: str) -> bytes:
        html = self._template.render(analysis=analysis, original_filename=original_filename)
        return HTML(string=html).write_pdf()
