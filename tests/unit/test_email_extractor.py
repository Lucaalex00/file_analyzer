from email.message import EmailMessage

import pytest

from src.extractors.base import ExtractionError
from src.extractors.email_extractor import EmailExtractor


def make_eml_bytes(subject: str, sender: str, to: str, body: str) -> bytes:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to
    message.set_content(body)
    return message.as_bytes()


class TestSupports:
    def test_supports_eml_extension(self):
        extractor = EmailExtractor()
        assert extractor.supports("notice.EML", "message/rfc822") is True

    def test_does_not_support_txt_extension(self):
        extractor = EmailExtractor()
        assert extractor.supports("notice.txt", "text/plain") is False


class TestExtract:
    def test_extracts_subject_sender_and_body(self):
        extractor = EmailExtractor()
        eml_bytes = make_eml_bytes(
            subject="Urgent: staging credentials",
            sender="it@example.com",
            to="team@example.com",
            body="Please rotate the shared staging password by Friday.",
        )

        raw = extractor.extract(eml_bytes, "notice.eml")

        assert "Urgent: staging credentials" in raw.content
        assert "it@example.com" in raw.content
        assert "Please rotate the shared staging password by Friday." in raw.content
        assert raw.source_filename == "notice.eml"

    def test_raises_extraction_error_on_corrupt_email(self):
        extractor = EmailExtractor()

        with pytest.raises(ExtractionError):
            extractor.extract(b"", "broken.eml")

    def test_raises_extraction_error_when_body_is_empty(self):
        extractor = EmailExtractor()
        eml_bytes = make_eml_bytes(subject="Empty", sender="a@example.com", to="b@example.com", body="")

        with pytest.raises(ExtractionError):
            extractor.extract(eml_bytes, "empty.eml")
