"""
Pydantic schemas for parking session operations.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ParkingSessionCreate(BaseModel):
    """Schema for creating a new parking session (checking in)."""
    parking_lot_id: int = Field(..., description="ID of the parking lot")

    class Config:
        json_schema_extra = {
            "example": {
                "parking_lot_id": 1
            }
        }


class ParkingSessionResponse(BaseModel):
    """Schema for parking session response."""
    id: str
    parking_lot_id: int
    parking_lot_name: str
    parking_lot_code: str
    checked_in_at: datetime
    checked_out_at: Optional[datetime]
    is_active: bool
    reminder_sent: bool

    @classmethod
    def from_session(cls, session, lot_name: str, lot_code: str) -> "ParkingSessionResponse":
        """Create response from session model with lot details."""
        return cls(
            id=session.id,
            parking_lot_id=session.parking_lot_id,
            parking_lot_name=lot_name,
            parking_lot_code=lot_code,
            checked_in_at=session.checked_in_at,
            checked_out_at=session.checked_out_at,
            is_active=session.is_active,
            reminder_sent=session.reminder_sent,
        )


class CheckoutResponse(BaseModel):
    """Schema for checkout response."""
    success: bool
    message: str
    session_id: str
    checked_out_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully checked out",
                "session_id": "abc123def456",
                "checked_out_at": "2024-01-15T14:30:00Z"
            }
        }
