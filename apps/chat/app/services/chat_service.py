from typing import List, Optional
import time

from ..schemas import Message
from ..core.llm_client import OpenRouterClient  
from app.logger import enrich_context  # логгер с контекстом

class ChatService:
    """
    ChatService инкапсулирует бизнес-логику чата.
    """

    def __init__(self, llm_client: Optional[OpenRouterClient] = None):
        self.llm_client = llm_client or OpenRouterClient()
        enrich_context(event="chat_service_init").info("Chat service initialized")

    async def get_ai_reply(
        self,
        messages: List[Message],
        user_api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> str:
        user_message = messages[-1].content if messages else ""
        model = getattr(self.llm_client, "model_name", "unknown")

        log = enrich_context(
            event="llm_request",
            project_id=project_id,
            user_message=user_message,
            model=model,
            trace_id=trace_id,
            job="chat"  # 👈 добавлено: метка job для Vector → Loki
        )

        log.bind(event="llm_request").info("LLM request initiated")

        try:
            start = time.time()
            reply = await self.llm_client.generate_reply(
                messages, user_api_key, project_id, trace_id
            )
            duration = time.time() - start

            log.bind(
                event="llm_response",
                ai_reply=reply,
                latency=duration,
            ).info("LLM response received")

            return reply

        except Exception as e:
            log.bind(
                event="llm_error",
                error=str(e),
            ).error("LLM call failed")
            raise
