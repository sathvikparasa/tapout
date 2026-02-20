"""
Pydantic schemas for parking lot operations.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ParkingLotCreate(BaseModel):
    """Schema for creating a new parking lot."""
    name: str = Field(..., min_length=1, max_length=255, description="Parking lot name")
    code: str = Field(..., min_length=1, max_length=50, description="Short code for the lot")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    is_active: bool = Field(True, description="Whether the lot is active")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Hutchinson Parking Structure",
                "code": "HUTCH",
                "latitude": 38.5382,
                "longitude": -121.7617,
                "is_active": True
            }
        }


class ParkingLotResponse(BaseModel):
    """Schema for parking lot response."""
    id: int
    name: str
    code: str
    latitude: Optional[float]
    longitude: Optional[float]
    is_active: bool

    class Config:
        from_attributes = True


class ParkingLotWithStats(ParkingLotResponse):
    """
    Schema for parking lot with additional statistics.
    Used for displaying lot information with real-time data.
    """
    active_parkers: int = Field(0, description="Number of users currently parked")
    recent_sightings: int = Field(0, description="TAPS sightings in last hour")
    taps_probability: float = Field(0.0, ge=0.0, le=1.0, description="Predicted probability of TAPS presence")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Hutchinson Parking Structure",
                "code": "HUTCH",
                "latitude": 38.5382,
                "longitude": -121.7617,
                "is_active": True,
                "active_parkers": 42,
                "recent_sightings": 3,
                "taps_probability": 0.35
            }
        }
