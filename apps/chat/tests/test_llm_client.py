from app.core.llm_client import OpenRouterClient

def test_openrouter_client_init():
    client = OpenRouterClient()
    assert client.api_url == "https://openrouter.ai/api/v1/chat/completions"