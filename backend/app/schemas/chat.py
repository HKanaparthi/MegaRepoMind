from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from app.models.chat import MessageRole


class CreateSessionRequest(BaseModel):
    title: str = "New Chat"


class SessionOut(BaseModel):
    id: str
    repository_id: str
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    content: str


class CitationOut(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    snippet: str


class MessageOut(BaseModel):
    id: str
    role: MessageRole
    content: str
    citations: Optional[List[Any]]
    created_at: datetime

    model_config = {"from_attributes": True}
