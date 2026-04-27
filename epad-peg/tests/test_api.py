"""Test the API health endpoint."""

import pytest
from fastapi.testclient import TestClient

from epad_bot.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = create_app()
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test the health check endpoint returns healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
