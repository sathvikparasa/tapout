"""
Tests for authentication endpoints and services.
"""

import uuid
from datetime import timedelta
from unittest.mock import patch, AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.services.auth import AuthService
from app.services.otp import OTPService
from app.services.email import EmailService


class TestAuthService:
    """Tests for AuthService class."""

    def test_is_valid_ucd_email_valid(self):
        """Test valid UC Davis email addresses."""
        valid_emails = [
            "student@ucdavis.edu",
            "john.doe@ucdavis.edu",
            "test123@ucdavis.edu",
            "a@ucdavis.edu",
            "student+test@ucdavis.edu",
        ]
        for email in valid_emails:
            assert AuthService.is_valid_ucd_email(email), f"{email} should be valid"

    def test_is_valid_ucd_email_invalid(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "student@gmail.com",
            "student@ucdavis.org",
            "student@UCDavis.edu.com",
            "@ucdavis.edu",
            "student",
            "student@",
            "",
        ]
        for email in invalid_emails:
            assert not AuthService.is_valid_ucd_email(email), f"{email} should be invalid"

    def test_create_access_token(self):
        """Test JWT token creation."""
        device_id = str(uuid.uuid4())
        token = AuthService.create_access_token(device_id)

        assert token is not None
        assert len(token) > 0

        # Token should be decodable
        decoded_id = AuthService.decode_token(token)
        assert decoded_id == device_id

    def test_decode_invalid_token(self):
        """Test decoding invalid tokens."""
        # Invalid token
        assert AuthService.decode_token("invalid-token") is None

        # Empty token
        assert AuthService.decode_token("") is None

    def test_create_access_token_custom_expiry(self):
        """Test token creation with custom expiration."""
        device_id = str(uuid.uuid4())
        token = AuthService.create_access_token(
            device_id, expires_delta=timedelta(minutes=5)
        )

        decoded_id = AuthService.decode_token(token)
        assert decoded_id == device_id

    def test_decode_expired_token(self):
        """Test that an expired token returns None."""
        device_id = str(uuid.uuid4())
        # Create a token that expired 1 hour ago
        token = AuthService.create_access_token(
            device_id, expires_delta=timedelta(hours=-1)
        )

        assert AuthService.decode_token(token) is None

    @pytest.mark.asyncio
    async def test_get_or_create_device_new(self, db_session: AsyncSession):
        """New device_id creates a Device."""
        device_id = str(uuid.uuid4())
        device = await AuthService.get_or_create_device(db_session, device_id)

        assert device.device_id == device_id
        assert device.email_verified is False
        assert device.id is not None

    @pytest.mark.asyncio
    async def test_get_or_create_device_existing(self, db_session: AsyncSession):
        """Same device_id returns the same Device."""
        device_id = str(uuid.uuid4())
        device1 = await AuthService.get_or_create_device(db_session, device_id)
        device2 = await AuthService.get_or_create_device(db_session, device_id)

        assert device1.id == device2.id

    @pytest.mark.asyncio
    async def test_get_or_create_device_updates_push_token(self, db_session: AsyncSession):
        """Existing device with new push_token updates it."""
        device_id = str(uuid.uuid4())
        await AuthService.get_or_create_device(db_session, device_id)

        device = await AuthService.get_or_create_device(
            db_session, device_id, push_token="new-token-123"
        )

        assert device.push_token == "new-token-123"
        assert device.is_push_enabled is True

    @pytest.mark.asyncio
    async def test_verify_email_success(self, db_session: AsyncSession):
        """Valid UCD email → (True, message)."""
        device_id = str(uuid.uuid4())
        await AuthService.get_or_create_device(db_session, device_id)

        success, msg = await AuthService.verify_email_for_device(
            db_session, device_id, "student@ucdavis.edu"
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_verify_email_invalid_domain(self, db_session: AsyncSession):
        """Non-UCD email → (False, message)."""
        device_id = str(uuid.uuid4())
        await AuthService.get_or_create_device(db_session, device_id)

        success, msg = await AuthService.verify_email_for_device(
            db_session, device_id, "student@gmail.com"
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_verify_email_unregistered_device(self, db_session: AsyncSession):
        """Device not in DB → (False, message)."""
        success, msg = await AuthService.verify_email_for_device(
            db_session, "nonexistent-device", "student@ucdavis.edu"
        )

        assert success is False


class TestAuthEndpoints:
    """Tests for authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_device(self, client: AsyncClient):
        """Test device registration."""
        device_id = str(uuid.uuid4())
        response = await client.post(
            "/api/v1/auth/register",
            json={"device_id": device_id}
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_register_device_with_push_token(self, client: AsyncClient):
        """Test device registration with push token."""
        device_id = str(uuid.uuid4())
        push_token = "abc123pushtoken"

        response = await client.post(
            "/api/v1/auth/register",
            json={"device_id": device_id, "push_token": push_token}
        )

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_register_duplicate_device(self, client: AsyncClient):
        """Test registering same device twice returns token."""
        device_id = str(uuid.uuid4())

        # First registration
        response1 = await client.post(
            "/api/v1/auth/register",
            json={"device_id": device_id}
        )
        assert response1.status_code == 201

        # Second registration should also succeed (idempotent)
        response2 = await client.post(
            "/api/v1/auth/register",
            json={"device_id": device_id}
        )
        assert response2.status_code == 201

    @pytest.mark.asyncio
    async def test_send_otp_valid_email(self, client: AsyncClient, test_device):
        """Test sending OTP to valid UC Davis email."""
        with patch.object(EmailService, "send_otp_email", new_callable=AsyncMock):
            response = await client.post(
                "/api/v1/auth/send-otp",
                json={
                    "device_id": test_device.device_id,
                    "email": "student@ucdavis.edu"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_send_otp_invalid_domain(self, client: AsyncClient, test_device):
        """Test sending OTP to non-UC Davis email."""
        response = await client.post(
            "/api/v1/auth/send-otp",
            json={
                "device_id": test_device.device_id,
                "email": "student@gmail.com"
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_send_otp_unregistered_device(self, client: AsyncClient):
        """Test sending OTP for unregistered device."""
        response = await client.post(
            "/api/v1/auth/send-otp",
            json={
                "device_id": str(uuid.uuid4()),
                "email": "student@ucdavis.edu"
            }
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_verify_otp_success(self, client: AsyncClient, test_device):
        """Test OTP verification with correct code."""
        with patch.object(OTPService, "generate_otp", return_value="123456"), \
             patch.object(EmailService, "send_otp_email", new_callable=AsyncMock):
            await client.post(
                "/api/v1/auth/send-otp",
                json={
                    "device_id": test_device.device_id,
                    "email": "student@ucdavis.edu"
                }
            )

        response = await client.post(
            "/api/v1/auth/verify-otp",
            json={
                "device_id": test_device.device_id,
                "email": "student@ucdavis.edu",
                "otp_code": "123456"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["email_verified"] is True
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_verify_otp_wrong_code(self, client: AsyncClient, test_device):
        """Test OTP verification with wrong code."""
        with patch.object(OTPService, "generate_otp", return_value="123456"), \
             patch.object(EmailService, "send_otp_email", new_callable=AsyncMock):
            await client.post(
                "/api/v1/auth/send-otp",
                json={
                    "device_id": test_device.device_id,
                    "email": "student@ucdavis.edu"
                }
            )

        response = await client.post(
            "/api/v1/auth/verify-otp",
            json={
                "device_id": test_device.device_id,
                "email": "student@ucdavis.edu",
                "otp_code": "000000"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_verify_otp_unregistered_device(self, client: AsyncClient):
        """Test OTP verification for unregistered device."""
        response = await client.post(
            "/api/v1/auth/verify-otp",
            json={
                "device_id": str(uuid.uuid4()),
                "email": "student@ucdavis.edu",
                "otp_code": "123456"
            }
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_device_info(self, client: AsyncClient, auth_headers):
        """Test getting current device info."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "device_id" in data
        assert data["email_verified"] is True

    @pytest.mark.asyncio
    async def test_get_device_info_unauthorized(self, client: AsyncClient):
        """Test getting device info without auth."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403  # No auth header

    @pytest.mark.asyncio
    async def test_get_device_info_invalid_token(self, client: AsyncClient):
        """Test getting device info with a garbage token → 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer totally-invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_device(self, client: AsyncClient, auth_headers):
        """Test updating device settings."""
        response = await client.patch(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={"is_push_enabled": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_push_enabled"] is True

    @pytest.mark.asyncio
    async def test_update_device_push_token(self, client: AsyncClient, auth_headers):
        """Test updating device push token."""
        response = await client.patch(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={"push_token": "new-fcm-token:abc123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "device_id" in data
