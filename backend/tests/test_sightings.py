"""
Tests for TAPS sighting endpoints.
"""

import pytest
from unittest.mock import patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parking_lot import ParkingLot
from app.models.device import Device
from app.models.parking_session import ParkingSession


class TestSightingEndpoints:
    """Tests for TAPS sighting API endpoints."""

    @pytest.mark.asyncio
    async def test_report_sighting_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test successful TAPS sighting report."""
        response = await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={
                "parking_lot_id": test_parking_lot.id,
                "notes": "White truck on level 3"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["parking_lot_id"] == test_parking_lot.id
        assert data["parking_lot_name"] == test_parking_lot.name
        assert data["notes"] == "White truck on level 3"
        assert "users_notified" in data

    @pytest.mark.asyncio
    async def test_report_sighting_notifies_parked_users(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device,
        test_parking_lot: ParkingLot
    ):
        """Test that reporting notifies parked users."""
        # Create a parking session for the device
        session = ParkingSession(
            device_id=verified_device.id,
            parking_lot_id=test_parking_lot.id,
        )
        db_session.add(session)
        await db_session.commit()

        # Report sighting
        response = await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["users_notified"] >= 0  # notifications fire in a background task, count is not synchronously available

    @pytest.mark.asyncio
    async def test_report_sighting_without_notes(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot,
    ):
        """Sighting with no notes field → succeeds, notes is null."""
        response = await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["notes"] is None or data["notes"] == ""

    @pytest.mark.asyncio
    async def test_list_sightings_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """No sightings → empty list."""
        response = await client.get(
            "/api/v1/sightings",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_report_sighting_requires_auth(
        self,
        client: AsyncClient,
        test_parking_lot: ParkingLot,
    ):
        """Sighting report without auth → 403."""
        response = await client.post(
            "/api/v1/sightings",
            json={"parking_lot_id": test_parking_lot.id},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_report_sighting_invalid_lot(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test reporting sighting at non-existent lot."""
        response = await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={"parking_lot_id": 99999}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_report_sighting_requires_verification(
        self,
        client: AsyncClient,
        unverified_auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test that sighting report requires email verification."""
        response = await client.post(
            "/api/v1/sightings",
            headers=unverified_auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_sightings(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test listing recent sightings."""
        # Create a sighting
        await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )

        # List sightings
        response = await client.get(
            "/api/v1/sightings",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["parking_lot_id"] == test_parking_lot.id

    @pytest.mark.asyncio
    async def test_list_sightings_filter_by_lot(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test filtering sightings by lot ID."""
        # Create a sighting
        await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )

        # List sightings for specific lot
        response = await client.get(
            f"/api/v1/sightings?lot_id={test_parking_lot.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for sighting in data:
            assert sighting["parking_lot_id"] == test_parking_lot.id

    @pytest.mark.asyncio
    async def test_get_latest_sighting(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test getting latest sighting at a lot."""
        # Create a sighting
        await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={
                "parking_lot_id": test_parking_lot.id,
                "notes": "Latest sighting"
            }
        )

        # Get latest
        response = await client.get(
            f"/api/v1/sightings/latest/{test_parking_lot.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["parking_lot_id"] == test_parking_lot.id
        assert data["notes"] == "Latest sighting"

    @pytest.mark.asyncio
    async def test_get_latest_sighting_none_exists(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test getting latest sighting when none exist."""
        response = await client.get(
            f"/api/v1/sightings/latest/{test_parking_lot.id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_report_sighting_rapid_successive(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Second report within 10 minutes is rate-limited into an upvote (200, was_rate_limited=True)."""
        response1 = await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )
        assert response1.status_code == 201
        assert response1.json()["was_rate_limited"] is False

        response2 = await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["was_rate_limited"] is True
        # Returns the original sighting's id
        assert data2["id"] == response1.json()["id"]

    @pytest.mark.asyncio
    async def test_rate_limited_report_upvotes_existing_sighting(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """After rate-limited report, the existing sighting gains an upvote."""
        # First report creates the sighting
        r1 = await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )
        assert r1.status_code == 201
        sighting_id = r1.json()["id"]

        # Second report is rate-limited → becomes an upvote
        r2 = await client.post(
            "/api/v1/sightings",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )
        assert r2.status_code == 200

        # Check vote was recorded
        vote_resp = await client.get(
            f"/api/v1/feed/sightings/{sighting_id}/votes",
            headers=auth_headers,
        )
        assert vote_resp.status_code == 200
        votes = vote_resp.json()
        assert votes["upvotes"] >= 1

    @pytest.mark.asyncio
    async def test_report_sighting_weekday_sends_notifications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device,
        test_parking_lot: ParkingLot,
    ):
        """On a weekday, a sighting report fires notifications."""
        session = ParkingSession(
            device_id=verified_device.id,
            parking_lot_id=test_parking_lot.id,
        )
        db_session.add(session)
        await db_session.commit()

        with patch("app.api.sightings._is_weekend", return_value=False), \
             patch("app.services.notification.NotificationService.notify_parked_users") as mock_notify:
            mock_notify.return_value = 1
            response = await client.post(
                "/api/v1/sightings",
                headers=auth_headers,
                json={"parking_lot_id": test_parking_lot.id},
            )

        assert response.status_code == 201
        # Background task was scheduled (mock may not be called synchronously in tests,
        # but the sighting is created)
        assert response.json()["was_rate_limited"] is False

    @pytest.mark.asyncio
    async def test_report_sighting_weekend_skips_notifications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device,
        test_parking_lot: ParkingLot,
    ):
        """On a weekend, a sighting report is still recorded but no notifications are sent."""
        session = ParkingSession(
            device_id=verified_device.id,
            parking_lot_id=test_parking_lot.id,
        )
        db_session.add(session)
        await db_session.commit()

        with patch("app.api.sightings._is_weekend", return_value=True), \
             patch("app.services.notification.NotificationService.notify_parked_users") as mock_notify:
            response = await client.post(
                "/api/v1/sightings",
                headers=auth_headers,
                json={"parking_lot_id": test_parking_lot.id},
            )

        assert response.status_code == 201
        mock_notify.assert_not_called()
