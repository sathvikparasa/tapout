"""
Pydantic schemas for global chat endpoints.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, field_validator


class ChatMessageCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        if len(v) > 280:
            raise ValueError("Message cannot exceed 280 characters")
        return v


class ChatMessageResponse(BaseModel):
    id: int
    content: str
    sent_at: datetime
    minutes_ago: int

    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    messages: List[ChatMessageResponse]
