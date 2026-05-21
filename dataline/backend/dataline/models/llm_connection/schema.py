from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class LlmConnectionCreate(BaseModel):
    provider: str
    model: str
    api_key: str | None = None
    base_url: str | None = None
    is_default: bool = False

class LlmConnectionUpdate(BaseModel):
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    is_default: bool | None = None

class LlmConnectionOut(BaseModel):
    id: UUID
    provider: str
    model: str
    base_url: str | None = None
    is_default: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
