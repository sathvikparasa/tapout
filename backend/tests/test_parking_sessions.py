"""
Tests for parking session endpoints.
"""

import pytest

from app.models.parking_lot import ParkingLot


class TestParkingSessionEndpoints:
    """Tests for parking session API endpoints."""

    @pytest.mark.asyncio
    async def test_check_in_success(
        self,
        client,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test successful check-in to a parking lot."""
        response = client.post(
            "/api/v1/sessions/checkin",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["parking_lot_id"] == test_parking_lot.id
        assert data["parking_lot_name"] == test_parking_lot.name
        assert data["is_active"] is True
        assert data["checked_out_at"] is None

    @pytest.mark.asyncio
    async def test_check_in_requires_verification(
        self,
        client,
        unverified_auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test that check-in requires email verification."""
        response = client.post(
            "/api/v1/sessions/checkin",
            headers=unverified_auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_check_in_invalid_lot(
        self,
        client,
        auth_headers: dict
    ):
        """Test check-in to non-existent parking lot."""
        response = client.post(
            "/api/v1/sessions/checkin",
            headers=auth_headers,
            json={"parking_lot_id": 99999}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_check_in_already_parked(
        self,
        client,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test that you can't check in when already parked."""
        # First check-in
        response1 = client.post(
            "/api/v1/sessions/checkin",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )
        assert response1.status_code == 201

        # Second check-in should fail
        response2 = client.post(
            "/api/v1/sessions/checkin",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )
        assert response2.status_code == 400

    @pytest.mark.asyncio
    async def test_check_out_success(
        self,
        client,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test successful checkout."""
        # First check in
        client.post(
            "/api/v1/sessions/checkin",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )

        # Then check out
        response = client.post(
            "/api/v1/sessions/checkout",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "checked_out_at" in data

    @pytest.mark.asyncio
    async def test_check_out_not_parked(
        self,
        client,
        auth_headers: dict
    ):
        """Test checkout when not parked."""
        response = client.post(
            "/api/v1/sessions/checkout",
            headers=auth_headers
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_current_session_when_parked(
        self,
        client,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test getting current session when parked."""
        # Check in
        client.post(
            "/api/v1/sessions/checkin",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )

        # Get current session
        response = client.get(
            "/api/v1/sessions/current",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["parking_lot_id"] == test_parking_lot.id
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_current_session_when_not_parked(
        self,
        client,
        auth_headers: dict
    ):
        """Test getting current session when not parked."""
        response = client.get(
            "/api/v1/sessions/current",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.get_json() is None

    @pytest.mark.asyncio
    async def test_get_session_history(
        self,
        client,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test getting session history."""
        # Create a session
        client.post(
            "/api/v1/sessions/checkin",
            headers=auth_headers,
            json={"parking_lot_id": test_parking_lot.id}
        )
        client.post(
            "/api/v1/sessions/checkout",
            headers=auth_headers
        )

        # Get history
        response = client.get(
            "/api/v1/sessions/history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["parking_lot_id"] == test_parking_lot.id
        assert data[0]["is_active"] is False

    @pytest.mark.asyncio
    async def test_check_out_requires_auth(
        self,
        client,
    ):
        """Checkout without auth → 403."""
        response = client.post("/api/v1/sessions/checkout")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_session_history_ordered_most_recent_first(
        self,
        client,
        auth_headers: dict,
        test_parking_lot: ParkingLot,
    ):
        """Session history returns most recent sessions first."""
        # Create two completed sessions
        for _ in range(2):
            client.post(
                "/api/v1/sessions/checkin",
                headers=auth_headers,
                json={"parking_lot_id": test_parking_lot.id},
            )
            client.post(
                "/api/v1/sessions/checkout",
                headers=auth_headers,
            )

        response = client.get(
            "/api/v1/sessions/history",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        # Most recent session first
        assert data[0]["checked_in_at"] >= data[1]["checked_in_at"]

    @pytest.mark.asyncio
    async def test_checkin_requires_auth(
        self,
        client,
        test_parking_lot: ParkingLot,
    ):
        """Checkin without auth → 403."""
        response = client.post(
            "/api/v1/sessions/checkin",
            json={"parking_lot_id": test_parking_lot.id},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_session_history_limit(
        self,
        client,
        auth_headers: dict,
        test_parking_lot: ParkingLot
    ):
        """Test session history respects limit parameter."""
        # Create multiple sessions
        for _ in range(3):
            client.post(
                "/api/v1/sessions/checkin",
                headers=auth_headers,
                json={"parking_lot_id": test_parking_lot.id}
            )
            client.post(
                "/api/v1/sessions/checkout",
                headers=auth_headers
            )

        # Get history with limit
        response = client.get(
            "/api/v1/sessions/history?limit=2",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
