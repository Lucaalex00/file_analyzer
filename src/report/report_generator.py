from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from src.analyzer.schemas import AnalysisResult

_TEMPLATE_DIR = Path(__file__).parent / "templates"


class ReportGenerator:
    def __init__(self):
        # autoescape=True unconditionally: select_autoescape() keys off the template
        # filename, and "report.html.j2" would fall through to no escaping.
        self._env = Environment(
            loader=FileSystemLoader(_TEMPLATE_DIR),
            autoescape=True,
        )
        self._template = self._env.get_template("report.html.j2")

    def render_html(self, analysis: AnalysisResult, original_filename: str) -> str:
        return self._template.render(analysis=analysis, original_filename=original_filename)

    def generate(self, analysis: AnalysisResult, original_filename: str) -> bytes:
        html = self.render_html(analysis, original_filename)
        return HTML(string=html).write_pdf()
