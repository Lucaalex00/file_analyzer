from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_lists_the_example_documents_that_exist():
    response = client.get("/api/examples")

    assert response.status_code == 200
    examples = response.json()["examples"]
    ids = [example["id"] for example in examples]
    assert "lease" in ids
    assert "memo" in ids
    # Every entry offered must be downloadable.
    for example in examples:
        assert client.get(f"/api/examples/{example['id']}").status_code == 200


def test_serves_an_example_with_its_filename_and_type():
    response = client.get("/api/examples/lease")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "sample_lease_contract.txt" in response.headers.get("content-disposition", "")
    assert b"LEASE" in response.content.upper()


def test_unknown_example_is_a_404():
    assert client.get("/api/examples/not-a-real-example").status_code == 404


def test_path_traversal_attempts_are_not_resolved_to_files():
    for attempt in ["../README", "..%2F..%2Fetc%2Fpasswd", "....//pytest.ini"]:
        response = client.get(f"/api/examples/{attempt}")
        assert response.status_code in (404, 422), attempt
        assert "root:" not in response.text
