from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import List, Optional

class Role(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"

class Message(BaseModel):
    role: Role = Field(..., examples=["user"])
    content: str = Field(..., examples=["Hello"])

class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    messages: List[Message] = Field(..., examples=[[{"role": "user", "content": "Hi"}]])
    user_api_key: Optional[str] = Field(None, alias="userApiKey", examples=["sk-..."])

class ChatResponse(BaseModel):
    reply: str = Field(..., examples=["Hello from AI"])