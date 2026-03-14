"""
Pydantic schemas for voting operations.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class VoteType(str, Enum):
    """Types of votes users can cast."""
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


class VoteCreate(BaseModel):
    """Schema for casting a vote on a sighting."""
    vote_type: VoteType = Field(..., description="Type of vote (upvote or downvote)")

    class Config:
        json_schema_extra = {
            "example": {
                "vote_type": "upvote"
            }
        }


class VoteResponse(BaseModel):
    """Schema for vote response."""
    id: str
    sighting_id: str
    vote_type: VoteType
    created_at: datetime
    updated_at: datetime


class VoteResult(BaseModel):
    """Schema for vote action result."""
    success: bool
    action: str = Field(..., description="Action taken: created, updated, or removed")
    vote_type: Optional[VoteType] = Field(None, description="Current vote type (null if removed)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "action": "created",
                "vote_type": "upvote"
            }
        }
