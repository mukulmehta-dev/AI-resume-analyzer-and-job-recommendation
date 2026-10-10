import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    mime: str
    size: int
    created_at: datetime
    latest_score: Optional[int] = None
    analyses_count: int = 0


class ResumeDetailResponse(ResumeResponse):
    extracted_text: str
