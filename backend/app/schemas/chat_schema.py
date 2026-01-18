from pydantic import BaseModel, Field
from typing import Dict, Optional

class ChatRequest(BaseModel):
    message: str
    thread_id: str
    features: Dict[str, bool] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    reply: str
    thread_id: str
