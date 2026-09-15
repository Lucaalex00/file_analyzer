from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_static_assets_are_served_with_no_cache_so_browsers_always_revalidate():
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"
