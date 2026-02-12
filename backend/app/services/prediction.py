"""
TAPS risk prediction service.

Determines risk level based on time since the most recent TAPS sighting.
Only considers sightings from today (Pacific time), since TAPS operates 7am-10pm.

Risk rules:
- 0-1 hours ago:  HIGH  (TAPS actively patrolling)
- 1-2 hours ago:  LOW   (TAPS likely moved on)
- 2-4 hours ago:  MEDIUM (Uncertain, could return)
- >4 hours ago:   HIGH  (Overdue, likely coming)
- Not spotted today: MEDIUM (No data, default)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.taps_sighting import TapsSighting
from app.models.parking_lot import ParkingLot
from app.schemas.prediction import PredictionResponse

logger = logging.getLogger(__name__)

# Mapping from risk level to backward-compatible probability
_RISK_TO_PROBABILITY = {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8}

# UC Davis is in Pacific time
_PACIFIC = ZoneInfo("America/Los_Angeles")


class PredictionService:
    """Service for predicting TAPS risk based on time since last sighting."""

    @classmethod
    async def predict(
        cls,
        db: AsyncSession,
        timestamp: Optional[datetime] = None,
    ) -> PredictionResponse:
        now = timestamp or datetime.now(timezone.utc)

        # Calculate start of today in Pacific time so yesterday's sightings
        # don't bleed into today's risk calculation
        now_pacific = now.astimezone(_PACIFIC)
        today_start_pacific = now_pacific.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_utc = today_start_pacific.astimezone(timezone.utc)

        # Find the most recent sighting globally (across all lots) from today
        query = (
            select(TapsSighting, ParkingLot)
            .join(ParkingLot, TapsSighting.parking_lot_id == ParkingLot.id)
            .where(TapsSighting.reported_at >= today_start_utc)
            .order_by(TapsSighting.reported_at.desc())
            .limit(1)
        )

        result = await db.execute(query)
        row = result.first()

        if row is None:
            return cls._build_no_sighting_response(now)

        sighting, lot = row
        hours_ago = (now - sighting.reported_at).total_seconds() / 3600

        return cls._build_sighting_response(now, hours_ago, sighting, lot)

    @classmethod
    def _classify_risk(cls, hours_ago: float) -> str:
        """Returns risk_level string."""
        if hours_ago <= 1.0:
            return "HIGH"
        elif hours_ago <= 2.0:
            return "LOW"
        elif hours_ago <= 4.0:
            return "MEDIUM"
        else:
            return "HIGH"

    @classmethod
    def _format_time_ago(cls, hours_ago: float) -> str:
        if hours_ago < 1:
            minutes_ago = int(hours_ago * 60)
            if minutes_ago <= 1:
                return "just now"
            return f"{minutes_ago} minutes ago"
        hours_int = int(hours_ago)
        minutes_remaining = int((hours_ago - hours_int) * 60)
        if minutes_remaining > 0:
            return f"{hours_int}h {minutes_remaining}m ago"
        return f"{hours_int} hour{'s' if hours_int != 1 else ''} ago"

    @classmethod
    def _build_no_sighting_response(cls, now: datetime) -> PredictionResponse:
        return PredictionResponse(
            risk_level="MEDIUM",
            risk_message="TAPS has not been sighted today",
            last_sighting_lot_name=None,
            last_sighting_lot_code=None,
            last_sighting_at=None,
            hours_since_last_sighting=None,
            parking_lot_id=None,
            parking_lot_name=None,
            parking_lot_code=None,
            probability=_RISK_TO_PROBABILITY["MEDIUM"],
            predicted_for=now,
            confidence=0.0,
        )

    @classmethod
    def _build_sighting_response(
        cls,
        now: datetime,
        hours_ago: float,
        sighting: TapsSighting,
        lot: ParkingLot,
    ) -> PredictionResponse:
        risk_level = cls._classify_risk(hours_ago)
        time_str = cls._format_time_ago(hours_ago)
        risk_message = f"TAPS was last spotted {time_str} at {lot.name}"

        return PredictionResponse(
            risk_level=risk_level,
            risk_message=risk_message,
            last_sighting_lot_name=lot.name,
            last_sighting_lot_code=lot.code,
            last_sighting_at=sighting.reported_at,
            hours_since_last_sighting=round(hours_ago, 2),
            parking_lot_id=lot.id,
            parking_lot_name=lot.name,
            parking_lot_code=lot.code,
            probability=_RISK_TO_PROBABILITY[risk_level],
            predicted_for=now,
            confidence=0.0,
        )
