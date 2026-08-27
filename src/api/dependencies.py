from functools import lru_cache

from openai import AzureOpenAI

from src.analyzer.document_analyzer import DocumentAnalyzer
from src.api.config import get_settings
from src.extractors.factory import ExtractorFactory
from src.pipeline import DocumentAnalysisPipeline
from src.report.report_generator import ReportGenerator


@lru_cache
def get_pipeline() -> DocumentAnalysisPipeline:
    settings = get_settings()
    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    return DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=DocumentAnalyzer(client=client, deployment=settings.azure_openai_deployment),
        report_generator=ReportGenerator(),
    )
