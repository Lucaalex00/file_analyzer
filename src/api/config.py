import os
from functools import lru_cache


class Settings:
    def __init__(self):
        self.azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        self.azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
        self.azure_openai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
        self.azure_openai_api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        # Groq: free, no card, no approval wait, OpenAI-compatible API --
        # a real (non-demo) AI provider usable while Azure OpenAI quota is
        # pending. Used only when Azure OpenAI isn't configured.
        self.groq_api_key = os.environ.get("GROQ_API_KEY", "")
        self.groq_model = os.environ.get("GROQ_MODEL") or "openai/gpt-oss-20b"
        self.max_file_size_bytes = int(os.environ.get("MAX_FILE_SIZE_BYTES") or 10 * 1024 * 1024)
        self.rate_limit_per_minute = int(os.environ.get("RATE_LIMIT_PER_MINUTE") or 20)
        self.max_batch_files = int(os.environ.get("MAX_BATCH_FILES") or 5)
        self.report_brand_name = os.environ.get("REPORT_BRAND_NAME") or "File Analyzer"
        self.report_accent_color = os.environ.get("REPORT_ACCENT_COLOR") or "#2563eb"

    @property
    def has_azure_openai(self) -> bool:
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def is_demo_mode(self) -> bool:
        # No real AI provider configured (neither Azure OpenAI nor Groq):
        # the app still starts and every endpoint still works, but the
        # analyzer/comparator use a simulated client
        # (src/analyzer/demo_client.py) instead of erroring out -- a
        # `docker run` with zero setup is always demoable.
        return not (self.has_azure_openai or self.has_groq)

    @property
    def ai_provider(self) -> str:
        # Same precedence as src/api/dependencies.py:_build_ai_client_and_model.
        if self.has_azure_openai:
            return "azure_openai"
        if self.has_groq:
            return "groq"
        return "demo"


@lru_cache
def get_settings() -> Settings:
    return Settings()
