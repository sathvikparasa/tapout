"""
Tests for TAPS risk prediction service and endpoints.

The prediction service uses time-since-last-sighting to classify risk:
  0-1h → HIGH, 1-2h → LOW, 2-4h → MEDIUM, >4h → HIGH
  No sighting today → MEDIUM
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parking_lot import ParkingLot
from app.models.taps_sighting import TapsSighting
from app.services.prediction import PredictionService


# ---------------------------------------------------------------------------
# Unit tests: _classify_risk
# ---------------------------------------------------------------------------

class TestClassifyRisk:
    """Pure unit tests for the risk classification logic."""

    def test_classify_risk_very_recent(self):
        """Sighting 30 min ago → HIGH (actively patrolling)."""
        assert PredictionService._classify_risk(0.5) == "HIGH"

    def test_classify_risk_zero(self):
        """Sighting just now (0 hours) → HIGH."""
        assert PredictionService._classify_risk(0.0) == "HIGH"

    def test_classify_risk_boundary_one_hour(self):
        """Exactly 1 hour → HIGH (<=1 is HIGH)."""
        assert PredictionService._classify_risk(1.0) == "HIGH"

    def test_classify_risk_low_range(self):
        """Sighting 1.5h ago → LOW (likely moved on)."""
        assert PredictionService._classify_risk(1.5) == "LOW"

    def test_classify_risk_boundary_two_hours(self):
        """Exactly 2 hours → LOW (<=2 is LOW)."""
        assert PredictionService._classify_risk(2.0) == "LOW"

    def test_classify_risk_medium_range(self):
        """Sighting 3h ago → MEDIUM (uncertain)."""
        assert PredictionService._classify_risk(3.0) == "MEDIUM"

    def test_classify_risk_boundary_four_hours(self):
        """Exactly 4 hours → MEDIUM (<=4 is MEDIUM)."""
        assert PredictionService._classify_risk(4.0) == "MEDIUM"

    def test_classify_risk_old(self):
        """Sighting 6h ago → HIGH (overdue, likely returning)."""
        assert PredictionService._classify_risk(6.0) == "HIGH"


# ---------------------------------------------------------------------------
# Unit tests: _format_time_ago
# ---------------------------------------------------------------------------

class TestFormatTimeAgo:
    """Pure unit tests for time formatting."""

    def test_format_just_now(self):
        """Very recent sighting (<=1 min) → 'just now'."""
        result = PredictionService._format_time_ago(0.01)
        assert result == "just now"

    def test_format_minutes_ago(self):
        """Half hour ago → '30 minutes ago'."""
        result = PredictionService._format_time_ago(0.5)
        assert "30 minutes ago" in result

    def test_format_one_hour_exact(self):
        """Exactly 1 hour → '1 hour ago'."""
        result = PredictionService._format_time_ago(1.0)
        assert "1 hour ago" in result

    def test_format_hours_and_minutes(self):
        """1.5 hours → '1h 30m ago'."""
        result = PredictionService._format_time_ago(1.5)
        assert "1h 30m ago" in result

    def test_format_multiple_hours(self):
        """3 hours exact → '3 hours ago'."""
        result = PredictionService._format_time_ago(3.0)
        assert "3 hours ago" in result


# ---------------------------------------------------------------------------
# Unit tests: response builders
# ---------------------------------------------------------------------------

class TestBuildResponses:
    """Tests for the response-building helpers."""

    def test_build_no_sighting_response(self):
        """No sighting today → MEDIUM risk, descriptive message."""
        now = datetime(2024, 10, 15, 14, 0, 0, tzinfo=timezone.utc)
        resp = PredictionService._build_no_sighting_response(now)

        assert resp.risk_level == "MEDIUM"
        assert resp.risk_message == "No TAPS in the last hour."
        assert resp.last_sighting_at is None
        assert resp.hours_since_last_sighting is None
        assert resp.predicted_for == now

    def test_build_no_sighting_response_with_lot_name(self):
        """No sighting with lot filter → message includes lot name."""
        now = datetime(2024, 10, 15, 14, 0, 0, tzinfo=timezone.utc)
        resp = PredictionService._build_no_sighting_response(now, lot_name="Pavilion Structure")

        assert "Pavilion Structure" in resp.risk_message
        assert resp.risk_level == "MEDIUM"

    def test_build_sighting_response(self):
        """With a recent sighting → correct risk, lot info, time_ago."""
        now = datetime(2024, 10, 15, 14, 0, 0, tzinfo=timezone.utc)
        sighting = TapsSighting(
            id=1,
            parking_lot_id=1,
            reported_at=now - timedelta(minutes=30),
        )
        lot = ParkingLot(
            id=1,
            name="Test Lot",
            code="TST",
            latitude=38.0,
            longitude=-121.0,
            is_active=True,
        )
        hours_ago = 0.5

        resp = PredictionService._build_sighting_response(now, hours_ago, sighting, lot)

        assert resp.risk_level == "HIGH"  # 0.5h → HIGH
        assert "Test Lot" in resp.risk_message
        assert resp.last_sighting_lot_name == "Test Lot"
        assert resp.last_sighting_lot_code == "TST"
        assert resp.hours_since_last_sighting == 0.5
        assert resp.parking_lot_id == 1
        assert resp.predicted_for == now


# ---------------------------------------------------------------------------
# Async tests: PredictionService.predict()
# ---------------------------------------------------------------------------

class TestPredict:
    """Integration tests for the predict() method using a test DB."""

    @pytest.mark.asyncio
    async def test_predict_no_sightings_today(
        self, db_session: AsyncSession, test_parking_lot: ParkingLot
    ):
        """No sightings at all → MEDIUM risk, no-sighting response."""
        prediction = await PredictionService.predict(db=db_session)

        assert prediction.risk_level == "MEDIUM"
        assert prediction.last_sighting_at is None

    @pytest.mark.asyncio
    async def test_predict_with_recent_sighting(
        self, db_session: AsyncSession, test_parking_lot: ParkingLot
    ):
        """Sighting 30 min ago → HIGH risk."""
        now = datetime.now(timezone.utc)
        sighting = TapsSighting(
            parking_lot_id=test_parking_lot.id,
            reported_at=now - timedelta(minutes=30),
        )
        db_session.add(sighting)
        await db_session.commit()

        prediction = await PredictionService.predict(db=db_session, timestamp=now)

        assert prediction.risk_level == "HIGH"
        assert prediction.last_sighting_lot_name == test_parking_lot.name

    @pytest.mark.asyncio
    async def test_predict_with_old_sighting(
        self, db_session: AsyncSession, test_parking_lot: ParkingLot
    ):
        """Sighting 3h ago → MEDIUM risk."""
        now = datetime.now(timezone.utc)
        sighting = TapsSighting(
            parking_lot_id=test_parking_lot.id,
            reported_at=now - timedelta(hours=3),
        )
        db_session.add(sighting)
        await db_session.commit()

        prediction = await PredictionService.predict(db=db_session, timestamp=now)

        assert prediction.risk_level == "MEDIUM"

    @pytest.mark.asyncio
    async def test_predict_specific_lot(
        self, db_session: AsyncSession, test_parking_lot: ParkingLot
    ):
        """Filtering by lot_id returns sighting at that lot."""
        now = datetime.now(timezone.utc)
        sighting = TapsSighting(
            parking_lot_id=test_parking_lot.id,
            reported_at=now - timedelta(minutes=10),
        )
        db_session.add(sighting)
        await db_session.commit()

        prediction = await PredictionService.predict(
            db=db_session, timestamp=now, lot_id=test_parking_lot.id
        )

        assert prediction.risk_level == "HIGH"
        assert prediction.parking_lot_id == test_parking_lot.id

    @pytest.mark.asyncio
    async def test_predict_nonexistent_lot(self, db_session: AsyncSession):
        """Querying a lot that has no sightings → MEDIUM, no-sighting response."""
        prediction = await PredictionService.predict(
            db=db_session, lot_id=99999
        )

        assert prediction.risk_level == "MEDIUM"
        assert prediction.last_sighting_at is None

    @pytest.mark.asyncio
    async def test_predict_custom_timestamp(
        self, db_session: AsyncSession, test_parking_lot: ParkingLot
    ):
        """Passing a specific timestamp uses it for time-since calculation."""
        # Sighting at 10:00 UTC today
        now = datetime.now(timezone.utc)
        today_10am = now.replace(hour=10, minute=0, second=0, microsecond=0)
        sighting = TapsSighting(
            parking_lot_id=test_parking_lot.id,
            reported_at=today_10am,
        )
        db_session.add(sighting)
        await db_session.commit()

        # Query at 10:30 → 0.5h ago → HIGH
        query_time = today_10am + timedelta(minutes=30)
        prediction = await PredictionService.predict(
            db=db_session, timestamp=query_time
        )

        assert prediction.risk_level == "HIGH"
        assert prediction.predicted_for == query_time


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------

class TestPredictionEndpoints:
    """HTTP endpoint tests for the predictions API."""

    @pytest.mark.asyncio
    async def test_get_global_prediction(
        self, client: AsyncClient, auth_headers: dict
    ):
        """GET /api/v1/predictions → 200, has risk_level."""
        response = await client.get(
            "/api/v1/predictions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")
        assert "risk_message" in data

    @pytest.mark.asyncio
    async def test_get_lot_prediction(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot,
    ):
        """GET /api/v1/predictions/{lot_id} → 200, has risk_level."""
        response = await client.get(
            f"/api/v1/predictions/{test_parking_lot.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    @pytest.mark.asyncio
    async def test_post_prediction_specific_time(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot,
    ):
        """POST /api/v1/predictions with timestamp → 200."""
        response = await client.post(
            "/api/v1/predictions",
            headers=auth_headers,
            json={
                "parking_lot_id": test_parking_lot.id,
                "timestamp": "2024-10-15T10:00:00Z",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH")
        assert "predicted_for" in data
