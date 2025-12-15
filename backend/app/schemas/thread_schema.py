from pydantic import BaseModel
from typing import Optional

class ThreadCreate(BaseModel):
    title: Optional[str] = "New Thread"

class ThreadResponse(BaseModel):
    thread_id: str
    title: str
    created_at: str
