"""
Pydantic schemas for notification operations.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: str
    notification_type: str
    title: str
    message: str
    parking_lot_id: Optional[int]
    created_at: datetime
    read_at: Optional[datetime]
    is_read: bool


class NotificationList(BaseModel):
    """Schema for list of notifications."""
    notifications: List[NotificationResponse]
    unread_count: int = Field(0, description="Total number of unread notifications")
    total: int = Field(0, description="Total number of notifications")

    class Config:
        json_schema_extra = {
            "example": {
                "notifications": [
                    {
                        "id": "abc123",
                        "notification_type": "taps_spotted",
                        "title": "TAPS Alert!",
                        "message": "TAPS has been spotted at Hutchinson Parking Structure",
                        "parking_lot_id": 1,
                        "created_at": "2024-01-15T14:30:00Z",
                        "read_at": None,
                        "is_read": False
                    }
                ],
                "unread_count": 1,
                "total": 1
            }
        }


class MarkReadRequest(BaseModel):
    """Schema for marking notifications as read."""
    notification_ids: List[str] = Field(..., min_length=1, description="List of notification IDs to mark as read")

    class Config:
        json_schema_extra = {
            "example": {
                "notification_ids": ["abc123", "def456", "ghi789"]
            }
        }
