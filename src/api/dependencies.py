from functools import lru_cache

from openai import AzureOpenAI

from src.analyzer.document_analyzer import DocumentAnalyzer
from src.analyzer.document_comparator import DocumentComparator
from src.api.config import get_settings
from src.extractors.factory import ExtractorFactory
from src.pipeline import DocumentAnalysisPipeline
from src.report.report_generator import ReportGenerator


@lru_cache
def get_extractor_factory() -> ExtractorFactory:
    return ExtractorFactory()


def _build_azure_client() -> AzureOpenAI:
    settings = get_settings()
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        # DocumentAnalyzer owns the retry policy; disable the SDK's own retries
        # so the two don't compound, and cap the per-request wait.
        timeout=30.0,
        max_retries=0,
    )


@lru_cache
def get_document_analyzer() -> DocumentAnalyzer:
    settings = get_settings()
    return DocumentAnalyzer(client=_build_azure_client(), deployment=settings.azure_openai_deployment)


@lru_cache
def get_document_comparator() -> DocumentComparator:
    settings = get_settings()
    return DocumentComparator(client=_build_azure_client(), deployment=settings.azure_openai_deployment)


@lru_cache
def get_pipeline() -> DocumentAnalysisPipeline:
    return DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=get_document_analyzer(),
        report_generator=ReportGenerator(),
    )
