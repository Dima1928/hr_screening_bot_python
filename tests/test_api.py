from fastapi.testclient import TestClient

from app.main import app, get_history_repository
from app.repositories.history import InMemoryHistoryRepository


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_endpoint_returns_question() -> None:
    app.dependency_overrides[get_history_repository] = lambda: InMemoryHistoryRepository()
    client = TestClient(app)

    response = client.post(
        "/webhook",
        json={
            "candidate_id": "api-cand-1",
            "candidate_name": "Анна",
            "vacancy_id": "python_backend",
            "text": "Здравствуйте, хочу откликнуться",
        },
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload["stage"] == "in_progress"
    assert payload["candidate_id"] == "api-cand-1"
    assert payload["reply"]
