"""
Pydantic schemas for TAPS sighting operations.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TapsSightingCreate(BaseModel):
    """Schema for reporting a TAPS sighting."""
    parking_lot_id: int = Field(..., description="ID of the parking lot where TAPS was spotted")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about the sighting")

    class Config:
        json_schema_extra = {
            "example": {
                "parking_lot_id": 1,
                "notes": "White TAPS truck on level 3"
            }
        }


class TapsSightingResponse(BaseModel):
    """Schema for TAPS sighting response."""
    id: str
    parking_lot_id: int
    parking_lot_name: str
    parking_lot_code: str
    reported_at: datetime
    notes: Optional[str]

    @classmethod
    def from_sighting(cls, sighting, lot_name: str, lot_code: str) -> "TapsSightingResponse":
        """Create response from sighting model with lot details."""
        return cls(
            id=sighting.id,
            parking_lot_id=sighting.parking_lot_id,
            parking_lot_name=lot_name,
            parking_lot_code=lot_code,
            reported_at=sighting.reported_at,
            notes=sighting.notes,
        )


class TapsSightingWithNotifications(TapsSightingResponse):
    """
    Schema for TAPS sighting response with notification count.
    Returned when a sighting is reported to show impact.
    """
    users_notified: int = Field(0, description="Number of users who were notified")
    was_rate_limited: bool = Field(False, description="True if this report was converted to an upvote (duplicate within 10 min)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "parking_lot_id": 1,
                "parking_lot_name": "Hutchinson Parking Structure",
                "parking_lot_code": "HUTCH",
                "reported_at": "2024-01-15T14:30:00Z",
                "notes": "White TAPS truck on level 3",
                "users_notified": 15,
                "was_rate_limited": False,
            }
        }
