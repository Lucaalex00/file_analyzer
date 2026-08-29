import os
from functools import lru_cache


class Settings:
    def __init__(self):
        self.azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        self.azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
        self.azure_openai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        self.azure_openai_api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        self.max_file_size_bytes = int(os.environ.get("MAX_FILE_SIZE_BYTES") or 10 * 1024 * 1024)
        self.rate_limit_per_minute = int(os.environ.get("RATE_LIMIT_PER_MINUTE") or 20)

    def validate(self) -> None:
        missing = [
            name
            for name, value in (
                ("AZURE_OPENAI_ENDPOINT", self.azure_openai_endpoint),
                ("AZURE_OPENAI_API_KEY", self.azure_openai_api_key),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required settings: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
