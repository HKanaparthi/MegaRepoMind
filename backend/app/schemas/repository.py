from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from app.models.repository import RepoStatus


class AddRepositoryRequest(BaseModel):
    github_url: str


class RepositoryOut(BaseModel):
    id: str
    name: str
    github_url: str
    description: Optional[str]
    status: RepoStatus
    file_count: int
    chunk_count: int
    summary: Optional[str]
    tech_stack: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    indexed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class FileOut(BaseModel):
    id: str
    file_path: str
    language: str
    size: int
    line_count: int

    model_config = {"from_attributes": True}
