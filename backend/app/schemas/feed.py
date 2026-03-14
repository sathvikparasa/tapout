"""
Pydantic schemas for the sighting feed.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

from app.schemas.vote import VoteType


class FeedSighting(BaseModel):
    """
    Schema for a sighting in the feed.
    Includes vote counts and the current user's vote.
    """
    id: str
    parking_lot_id: int
    parking_lot_name: str
    parking_lot_code: str
    reported_at: datetime
    notes: Optional[str]
    # Vote information
    upvotes: int = Field(0, description="Number of upvotes")
    downvotes: int = Field(0, description="Number of downvotes")
    net_score: int = Field(0, description="Upvotes minus downvotes")
    user_vote: Optional[VoteType] = Field(None, description="Current user's vote on this sighting")
    # Time context
    minutes_ago: int = Field(..., description="Minutes since the sighting was reported")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "parking_lot_id": 1,
                "parking_lot_name": "Hutchinson Parking Structure",
                "parking_lot_code": "HUTCH",
                "reported_at": "2024-01-15T14:30:00Z",
                "notes": "White truck on level 3",
                "upvotes": 5,
                "downvotes": 1,
                "net_score": 4,
                "user_vote": "upvote",
                "minutes_ago": 45
            }
        }


class FeedResponse(BaseModel):
    """
    Schema for the feed response.
    Groups sightings by parking lot.
    """
    parking_lot_id: int
    parking_lot_name: str
    parking_lot_code: str
    sightings: List[FeedSighting] = Field(default_factory=list)
    total_sightings: int = Field(0, description="Total number of sightings in this lot's feed")

    class Config:
        json_schema_extra = {
            "example": {
                "parking_lot_id": 1,
                "parking_lot_name": "Hutchinson Parking Structure",
                "parking_lot_code": "HUTCH",
                "sightings": [],
                "total_sightings": 0
            }
        }


class AllFeedsResponse(BaseModel):
    """
    Schema for all feeds response.
    Contains feeds for all active parking lots.
    """
    feeds: List[FeedResponse] = Field(default_factory=list)
    total_sightings: int = Field(0, description="Total sightings across all lots")

    class Config:
        json_schema_extra = {
            "example": {
                "feeds": [],
                "total_sightings": 0
            }
        }
