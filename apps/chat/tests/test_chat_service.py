import pytest
from unittest.mock import AsyncMock
from app.services.chat_service import ChatService
from app.schemas import Message

@pytest.mark.asyncio
async def test_chat_service_reply():
    service = ChatService()
    # Mock LLM client
    service.llm_client.generate_reply = AsyncMock(return_value="Hello!")
    
    messages = [Message(role="user", content="test")]
    reply = await service.get_ai_reply(messages)
    assert reply == "Hello!"