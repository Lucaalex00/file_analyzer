from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_lists_the_viewable_documents():
    response = client.get("/api/docs")

    assert response.status_code == 200
    ids = [doc["id"] for doc in response.json()["documents"]]
    assert ids == ["readme", "overview", "limitations"]


def test_renders_the_readme_as_html():
    response = client.get("/api/docs/readme")

    assert response.status_code == 200
    body = response.json()
    assert body["title"]
    assert "<h1" in body["html"]
    assert "File Analyzer" in body["html"]


def test_limitations_returns_only_that_section():
    response = client.get("/api/docs/limitations")

    assert response.status_code == 200
    html = response.json()["html"]
    assert "OCR on non-document images" in html
    # The rest of the README must not come along for the ride.
    assert "Quick start" not in html


def test_unknown_document_is_a_404():
    response = client.get("/api/docs/changelog")

    assert response.status_code == 404


def test_path_traversal_attempts_are_not_resolved_to_files():
    # The id is a key into an allowlist, never a path -- so these are simply
    # unknown documents, not reads of arbitrary files.
    for attempt in ["../README", "..%2F..%2Fetc%2Fpasswd", "....//README.md"]:
        response = client.get(f"/api/docs/{attempt}")
        assert response.status_code in (404, 422), attempt
        assert "root:" not in response.text


def test_relative_links_are_rewritten_to_github_so_they_still_work():
    html = client.get("/api/docs/readme").json()["html"]

    assert "https://github.com/Lucaalex00/file_analyzer/blob/master/infra/" in html
    assert 'href="infra/' not in html
