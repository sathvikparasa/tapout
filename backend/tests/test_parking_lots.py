"""
Tests for parking lot endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parking_lot import ParkingLot
from app.models.device import Device
from app.models.parking_session import ParkingSession
from app.models.taps_sighting import TapsSighting


class TestParkingLotEndpoints:
    """Tests for parking lot API endpoints."""

    @pytest.mark.asyncio
    async def test_list_parking_lots(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test listing parking lots."""
        response = await client.get(
            "/api/v1/lots",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        lot_codes = [lot["code"] for lot in data]
        assert test_parking_lot.code in lot_codes

    @pytest.mark.asyncio
    async def test_list_parking_lots_requires_auth(
        self,
        client: AsyncClient,
        test_parking_lot: ParkingLot
    ):
        """Test that listing lots requires authentication."""
        response = await client.get("/api/v1/lots")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_parking_lot_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test getting a parking lot by ID."""
        response = await client.get(
            f"/api/v1/lots/{test_parking_lot.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_parking_lot.id
        assert data["name"] == test_parking_lot.name
        assert data["code"] == test_parking_lot.code
        assert "active_parkers" in data
        assert "recent_sightings" in data
        assert "taps_probability" in data

    @pytest.mark.asyncio
    async def test_get_parking_lot_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting non-existent parking lot."""
        response = await client.get(
            "/api/v1/lots/99999",
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_parking_lot_by_code(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test getting a parking lot by code."""
        response = await client.get(
            f"/api/v1/lots/code/{test_parking_lot.code}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_parking_lot.code

    @pytest.mark.asyncio
    async def test_get_parking_lot_by_code_case_insensitive(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test that code lookup is case-insensitive."""
        response = await client.get(
            f"/api/v1/lots/code/{test_parking_lot.code.lower()}",
            headers=auth_headers
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_lots_excludes_inactive(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
    ):
        """Inactive lots are excluded from the listing."""
        inactive_lot = ParkingLot(
            name="Closed Structure",
            code="CLOSED",
            latitude=38.5,
            longitude=-121.7,
            is_active=False,
        )
        db_session.add(inactive_lot)
        await db_session.commit()

        response = await client.get("/api/v1/lots", headers=auth_headers)

        assert response.status_code == 200
        codes = [lot["code"] for lot in response.json()]
        assert "CLOSED" not in codes

    @pytest.mark.asyncio
    async def test_get_parking_lot_by_code_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Non-existent lot code → 404."""
        response = await client.get(
            "/api/v1/lots/code/DOESNOTEXIST",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_parking_lot_stats_active_parkers(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device,
        test_parking_lot: ParkingLot
    ):
        """Test that active parkers count is accurate."""
        # Create an active parking session
        session = ParkingSession(
            device_id=verified_device.id,
            parking_lot_id=test_parking_lot.id,
        )
        db_session.add(session)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/lots/{test_parking_lot.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["active_parkers"] >= 1

    @pytest.mark.asyncio
    async def test_parking_lot_stats_recent_sightings(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test that recent sightings count is accurate."""
        # Create a sighting
        sighting = TapsSighting(parking_lot_id=test_parking_lot.id)
        db_session.add(sighting)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/lots/{test_parking_lot.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["recent_sightings"] >= 1
