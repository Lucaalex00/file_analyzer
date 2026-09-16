from functools import lru_cache

from openai import AzureOpenAI, OpenAI

from src.analyzer.budgeted_client import BudgetedAIClient
from src.analyzer.demo_client import DemoAIClient
from src.analyzer.document_analyzer import DocumentAnalyzer
from src.analyzer.document_comparator import DocumentComparator
from src.api.ai_budget import AIBudget
from src.api.config import get_settings
from src.extractors.factory import ExtractorFactory
from src.pipeline import DocumentAnalysisPipeline
from src.report.report_generator import ReportGenerator

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


@lru_cache
def get_extractor_factory() -> ExtractorFactory:
    return ExtractorFactory()


@lru_cache
def get_ai_budget() -> AIBudget:
    return AIBudget(max_calls=get_settings().ai_hourly_budget)


def _build_ai_client_and_model():
    # Three providers, tried in this order: a real Azure OpenAI deployment
    # if configured, else Groq (free, no approval wait, OpenAI-compatible --
    # a real AI provider usable while Azure OpenAI quota is pending), else
    # the demo client. Model name is picked together with the client so a
    # Groq model name never accidentally gets sent to Azure OpenAI or vice
    # versa.
    # A real provider is wrapped so it degrades to the demo client once the
    # hourly budget is spent, rather than billing without bound.
    settings = get_settings()

    if settings.has_azure_openai:
        client = AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            # DocumentAnalyzer owns the retry policy; disable the SDK's own
            # retries so the two don't compound, and cap the per-request wait.
            timeout=30.0,
            max_retries=0,
        )
        return BudgetedAIClient(client, get_ai_budget()), settings.azure_openai_deployment

    if settings.has_groq:
        client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=_GROQ_BASE_URL,
            timeout=30.0,
            max_retries=0,
        )
        return BudgetedAIClient(client, get_ai_budget()), settings.groq_model

    return DemoAIClient(), "demo"


@lru_cache
def get_document_analyzer() -> DocumentAnalyzer:
    client, model = _build_ai_client_and_model()
    return DocumentAnalyzer(client=client, deployment=model)


@lru_cache
def get_document_comparator() -> DocumentComparator:
    client, model = _build_ai_client_and_model()
    return DocumentComparator(client=client, deployment=model)


@lru_cache
def get_report_generator() -> ReportGenerator:
    settings = get_settings()
    return ReportGenerator(brand_name=settings.report_brand_name, accent_color=settings.report_accent_color)


@lru_cache
def get_pipeline() -> DocumentAnalysisPipeline:
    return DocumentAnalysisPipeline(
        factory=ExtractorFactory(),
        analyzer=get_document_analyzer(),
        report_generator=get_report_generator(),
    )
