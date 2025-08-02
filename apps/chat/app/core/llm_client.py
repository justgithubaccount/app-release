import os
import httpx
import time
from typing import Dict, List, Optional
from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Инструментируем httpx для автоматического трейсинга HTTP запросов
HTTPXClientInstrumentor().instrument()

# Получаем tracer и meter
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Метрики
llm_request_counter = meter.create_counter(
    name="llm_requests_total",
    description="Total number of LLM requests",
    unit="1"
)

llm_request_duration = meter.create_histogram(
    name="llm_request_duration_seconds",
    description="LLM request duration in seconds",
    unit="s"
)

llm_tokens_counter = meter.create_counter(
    name="llm_tokens_total",
    description="Total tokens used",
    unit="1"
)

class OpenRouterClient:
    def __init__(self):
        # Из секрета
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Из конфига
        self.api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
        self.default_model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-opus-4")
        self.http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "")
        self.x_title = os.getenv("OPENROUTER_X_TITLE", "")
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Отправка запроса к OpenRouter API с полным OpenTelemetry трейсингом.
        """
        model_name = model or self.default_model
        
        # Создаем span для всей операции
        with tracer.start_as_current_span(
            "openrouter_chat_completion",
            attributes={
                "llm.model": model_name,
                "llm.provider": "openrouter",
                "llm.message_count": len(messages),
            }
        ) as span:
            start_time = time.time()
            
            try:
                # Подготовка заголовков
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                
                # Опциональные заголовки для OpenRouter
                if self.http_referer:
                    headers["HTTP-Referer"] = self.http_referer
                    span.set_attribute("llm.http_referer", self.http_referer)
                if self.x_title:
                    headers["X-Title"] = self.x_title
                    span.set_attribute("llm.x_title", self.x_title)
                
                # Подготовка запроса
                request_body = {
                    "model": model_name,
                    "messages": messages,
                    **kwargs
                }
                
                # Логируем размер запроса
                request_size = len(str(messages))
                span.set_attribute("llm.request_size", request_size)
                
                # Создаем отдельный span для HTTP запроса
                with tracer.start_as_current_span("http_request") as http_span:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            self.api_url,
                            headers=headers,
                            json=request_body,
                            timeout=60.0
                        )
                        response.raise_for_status()
                        result = response.json()
                
                # Обработка успешного ответа
                duration = time.time() - start_time
                
                # Извлекаем метрики из ответа
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
                
                # Устанавливаем атрибуты span
                span.set_attribute("llm.prompt_tokens", prompt_tokens)
                span.set_attribute("llm.completion_tokens", completion_tokens)
                span.set_attribute("llm.total_tokens", total_tokens)
                span.set_attribute("llm.duration_seconds", duration)
                span.set_attribute("llm.response_id", result.get("id", ""))
                
                # Записываем метрики
                labels = {"model": model_name, "status": "success"}
                llm_request_counter.add(1, labels)
                llm_request_duration.record(duration, labels)
                llm_tokens_counter.add(total_tokens, {"model": model_name, "type": "total"})
                llm_tokens_counter.add(prompt_tokens, {"model": model_name, "type": "prompt"})
                llm_tokens_counter.add(completion_tokens, {"model": model_name, "type": "completion"})
                
                span.set_status(Status(StatusCode.OK))
                return result
                
            except httpx.HTTPStatusError as e:
                # Обработка HTTP ошибок
                duration = time.time() - start_time
                
                span.set_attribute("http.status_code", e.response.status_code)
                span.set_attribute("error.type", "http_error")
                span.set_attribute("error.message", str(e))
                span.set_status(
                    Status(StatusCode.ERROR, f"HTTP {e.response.status_code}: {str(e)}")
                )
                
                # Метрики для ошибок
                labels = {"model": model_name, "status": "error", "error_type": "http"}
                llm_request_counter.add(1, labels)
                llm_request_duration.record(duration, labels)
                
                # Добавляем событие в span
                span.add_event(
                    "HTTP Error",
                    attributes={
                        "status_code": e.response.status_code,
                        "response_body": e.response.text[:500]  # Первые 500 символов
                    }
                )
                # Возвращаем error response вместо raise
                return {
                    "error": f"HTTP {e.response.status_code}: {str(e)}",
                    "choices": [{"message": {"content": f"HTTP ошибка: {e.response.status_code}"}}]
                }
                
            except Exception as e:
                # Обработка других ошибок
                duration = time.time() - start_time
                
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.set_status(Status(StatusCode.ERROR, str(e)))
                
                # Метрики для ошибок
                labels = {"model": model_name, "status": "error", "error_type": "exception"}
                llm_request_counter.add(1, labels)
                llm_request_duration.record(duration, labels)
                
                # Добавляем событие в span
                span.add_event(
                    "Exception occurred",
                    attributes={
                        "exception.type": type(e).__name__,
                        "exception.message": str(e)
                    }
                )
                # Возвращаем error response вместо raise
                return {
                    "error": str(e),
                    "choices": [{"message": {"content": f"Ошибка: {str(e)}"}}]
                }

    async def generate_reply(
        self,
        messages: List,  # List[Message] из schemas
        user_api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> str:
        """
        Метод для совместимости с ChatService.
        Преобразует список Message объектов в формат OpenRouter.
        """
        # Добавляем атрибуты в текущий span если есть
        current_span = trace.get_current_span()
        if current_span.is_recording():
            if project_id:
                current_span.set_attribute("project.id", project_id)
            if trace_id:
                current_span.set_attribute("external.trace_id", trace_id)
        
        # Преобразуем Message объекты в dict для OpenRouter
        openrouter_messages = []
        for msg in messages:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                # Если это объект Message
                openrouter_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg, dict):
                # Если уже dict
                openrouter_messages.append(msg)
            else:
                # Fallback
                openrouter_messages.append({
                    "role": "user",
                    "content": str(msg)
                })
        
        # Используем переданный API ключ если есть
        original_key = self.api_key
        if user_api_key:
            self.api_key = user_api_key
        
        try:
            # Вызываем основной метод
            response = await self.chat_completion(
                messages=openrouter_messages,
                model=self.default_model
            )
            
            # Проверяем на ошибки
            if "error" in response:
                return f"Ошибка API: {response['error']}"
            
            # Извлекаем текст ответа
            return response["choices"][0]["message"]["content"]
            
        finally:
            # Восстанавливаем оригинальный ключ
            if user_api_key:
                self.api_key = original_key
    
    @property
    def model_name(self) -> str:
        """Свойство для совместимости с ChatService."""
        return self.default_model