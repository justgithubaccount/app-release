import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

@pytest.fixture
def mock_openrouter(monkeypatch):
    async def mock_generate_reply(*args, **kwargs):
        return "Mocked response from AI"
    
    monkeypatch.setattr(
        "app.core.llm_client.OpenRouterClient.generate_reply", 
        mock_generate_reply
    )