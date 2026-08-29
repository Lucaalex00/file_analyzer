from email import message_from_bytes, policy

from src.extractors.base import BaseExtractor, ExtractionError, RawText

_SUPPORTED_EXTENSIONS = (".eml",)


class EmailExtractor(BaseExtractor):
    def supports(self, filename: str, content_type: str | None) -> bool:
        return filename.lower().endswith(_SUPPORTED_EXTENSIONS)

    def extract(self, file_bytes: bytes, filename: str) -> RawText:
        try:
            message = message_from_bytes(file_bytes, policy=policy.default)
        except Exception as exc:  # noqa: BLE001 - the stdlib parser doesn't document its exceptions
            raise ExtractionError(f"Could not parse email {filename!r}") from exc

        body_part = message.get_body(preferencelist=("plain", "html"))
        body = body_part.get_content().strip() if body_part else ""

        if not body:
            raise ExtractionError(f"No readable content found in {filename!r}")

        header_lines = [
            f"Subject: {message.get('Subject', '')}",
            f"From: {message.get('From', '')}",
            f"To: {message.get('To', '')}",
        ]
        content = "\n".join(header_lines) + "\n\n" + body

        return RawText(content=content, source_filename=filename)
