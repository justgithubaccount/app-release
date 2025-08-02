import logging
from contextvars import ContextVar
from typing import Any, Dict, Optional, cast
from opentelemetry import trace
import structlog

# Context variables для хранения дополнительных атрибутов
log_context: ContextVar[Dict[str, Any]] = ContextVar('log_context', default={})

class EnrichedLogger:
    """
    Logger с автоматическим добавлением OpenTelemetry контекста.
    Совместим с существующим интерфейсом enrich_context.
    """
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
    
    def _add_trace_context(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Добавляет trace_id и span_id из текущего контекста."""
        span = trace.get_current_span()
        if span.is_recording():
            span_context = span.get_span_context()
            event_dict['trace_id'] = format(span_context.trace_id, '032x')
            event_dict['span_id'] = format(span_context.span_id, '016x')
        
        # Добавляем контекстные переменные
        event_dict.update(log_context.get())
        
        return event_dict
    
    def bind(self, **kwargs) -> 'EnrichedLogger':
        """Добавляет контекст к логгеру."""
        # Приводим к нужному типу для MyPy
        bound_logger = cast(structlog.BoundLogger, self.logger.bind(**kwargs))
        return EnrichedLogger(bound_logger)
    
    def info(self, msg: str, **kwargs) -> None:
        kwargs = self._add_trace_context(kwargs)
        self.logger.info(msg, **kwargs)
    
    def error(self, msg: str, **kwargs) -> None:
        kwargs = self._add_trace_context(kwargs)
        self.logger.error(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs) -> None:
        kwargs = self._add_trace_context(kwargs)
        self.logger.warning(msg, **kwargs)
    
    def debug(self, msg: str, **kwargs) -> None:
        kwargs = self._add_trace_context(kwargs)
        self.logger.debug(msg, **kwargs)

# Инициализация structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Базовый логгер
base_logger = structlog.get_logger()

def enrich_context(**kwargs) -> EnrichedLogger:
    """
    Создает логгер с обогащенным контекстом.
    Совместимо с существующим кодом.
    """
    # Приводим к нужному типу для MyPy
    bound_logger = cast(structlog.BoundLogger, base_logger.bind(**kwargs))
    return EnrichedLogger(bound_logger)


def set_request_context(**kwargs) -> None:
    """
    Устанавливает контекст для всего request.
    Используется в middleware или в начале обработки запроса.
    """
    current_context = log_context.get()
    current_context.update(kwargs)
    log_context.set(current_context)