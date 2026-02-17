"""
Pydantic schemas for TAPS risk prediction.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class PredictionRequest(BaseModel):
    """
    Schema for requesting a TAPS probability prediction.
    If timestamp is not provided, uses current time.
    """
    parking_lot_id: int = Field(..., description="ID of the parking lot")
    timestamp: Optional[datetime] = Field(None, description="Time to predict for (defaults to now)")

    class Config:
        json_schema_extra = {
            "example": {
                "parking_lot_id": 1,
                "timestamp": "2024-01-15T14:30:00Z"
            }
        }


class PredictionFactors(BaseModel):
    """
    Schema detailing the factors that contributed to the prediction.
    Kept for backward compatibility with older clients.
    """
    time_of_day_factor: float = Field(..., ge=0.0, le=1.0, description="Contribution from time of day")
    day_of_week_factor: float = Field(..., ge=0.0, le=1.0, description="Contribution from day of week")
    historical_factor: float = Field(..., ge=0.0, le=1.0, description="Contribution from historical sightings")
    recent_sightings_factor: float = Field(..., ge=0.0, le=1.0, description="Contribution from recent sightings")
    academic_calendar_factor: float = Field(..., ge=0.0, le=1.0, description="Contribution from academic calendar")
    weather_factor: Optional[float] = Field(None, ge=0.0, le=1.0, description="Contribution from weather")


class PredictionResponse(BaseModel):
    """Schema for TAPS risk prediction response."""
    # New fields
    risk_level: str = Field(..., description="Risk level: LOW, MEDIUM, HIGH")
    risk_message: str = Field(..., description="Human-readable risk detail message")
    last_sighting_lot_name: Optional[str] = Field(None, description="Name of lot where TAPS was last spotted")
    last_sighting_lot_code: Optional[str] = Field(None, description="Code of lot where TAPS was last spotted")
    last_sighting_at: Optional[datetime] = Field(None, description="When TAPS was last spotted")
    hours_since_last_sighting: Optional[float] = Field(None, description="Hours since TAPS was last spotted")

    # Backward-compatible fields for old clients
    parking_lot_id: Optional[int] = Field(None)
    parking_lot_name: Optional[str] = Field(None)
    parking_lot_code: Optional[str] = Field(None)
    probability: float = Field(0.0, ge=0.0, le=1.0, description="Mapped from risk level for backward compat")
    predicted_for: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    factors: PredictionFactors = Field(
        default_factory=lambda: PredictionFactors(
            time_of_day_factor=0.0,
            day_of_week_factor=0.0,
            historical_factor=0.0,
            recent_sightings_factor=0.0,
            academic_calendar_factor=0.0,
            weather_factor=None,
        ),
        description="Zeroed-out factors for backward compat",
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "risk_level": "HIGH",
                "risk_message": "TAPS was last spotted 45 minutes ago at Pavilion Structure",
                "last_sighting_lot_name": "Pavilion Structure",
                "last_sighting_lot_code": "HUTCH",
                "last_sighting_at": "2024-01-15T13:45:00Z",
                "hours_since_last_sighting": 0.75,
                "parking_lot_id": 1,
                "parking_lot_name": "Pavilion Structure",
                "parking_lot_code": "HUTCH",
                "probability": 0.8,
                "predicted_for": "2024-01-15T14:30:00Z",
                "factors": {
                    "time_of_day_factor": 0.0,
                    "day_of_week_factor": 0.0,
                    "historical_factor": 0.0,
                    "recent_sightings_factor": 0.0,
                    "academic_calendar_factor": 0.0,
                    "weather_factor": None
                },
                "confidence": 0.0
            }
        }
