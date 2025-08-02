from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

# Импортируем Role из schemas, избегаем дублирования
from ..schemas.chat import Role

class StoredChatMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    role: Role
    content: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatHistory(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str = Field(..., examples=["proj-123"])
    messages: List[StoredChatMessage]
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)