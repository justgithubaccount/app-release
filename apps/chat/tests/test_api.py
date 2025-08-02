from fastapi.testclient import TestClient
from app.main import create_app

# client = TestClient(create_app())

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_chat_endpoint(client, mock_openrouter):
    response = client.post("/api/v1/chat", json={
        "messages": [{"role": "user", "content": "test"}]
    })
    assert response.status_code == 200
    assert "reply" in response.json()