"""
Security tests — auth boundaries, input validation, access control.
"""

import uuid
from datetime import timedelta
from unittest.mock import patch, AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.models.device import Device
from app.models.parking_lot import ParkingLot
from app.models.parking_session import ParkingSession
from app.models.notification import Notification, NotificationType
from app.services.auth import AuthService
from app.services.notification import NotificationService

API = "/api/v1"


async def _create_lot(db: AsyncSession, name: str, code: str) -> ParkingLot:
    lot = ParkingLot(name=name, code=code, latitude=38.54, longitude=-121.76, is_active=True)
    db.add(lot)
    await db.commit()
    await db.refresh(lot)
    return lot


async def _verified_device(db: AsyncSession) -> tuple[Device, dict]:
    device = Device(
        device_id=str(uuid.uuid4()), email_verified=True,
        is_push_enabled=False,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    token = AuthService.create_access_token(device.device_id)
    return device, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Auth Security
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAuthSecurity:

    async def test_no_token_returns_403(self, client: AsyncClient):
        r = await client.get(f"{API}/lots")
        assert r.status_code == 403

    async def test_invalid_token_returns_401(self, client: AsyncClient):
        r = await client.get(f"{API}/lots", headers={"Authorization": "Bearer garbage-token"})
        assert r.status_code == 401

    async def test_expired_token_returns_401(self, client: AsyncClient, db_session: AsyncSession):
        device = Device(device_id=str(uuid.uuid4()), email_verified=True)
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)

        token = AuthService.create_access_token(
            device.device_id, expires_delta=timedelta(seconds=-1),
        )
        r = await client.get(f"{API}/lots", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    async def test_token_for_deleted_device_returns_401(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        device = Device(device_id=str(uuid.uuid4()), email_verified=True)
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)

        token = AuthService.create_access_token(device.device_id)

        # Delete the device
        await db_session.delete(device)
        await db_session.commit()

        r = await client.get(f"{API}/lots", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Input Validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestInputValidation:

    async def test_sighting_notes_max_length(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot, auth_headers: dict,
    ):
        r = await client.post(
            f"{API}/sightings",
            json={"parking_lot_id": test_parking_lot.id, "notes": "x" * 501},
            headers=auth_headers,
        )
        assert r.status_code == 422

    async def test_sighting_notes_at_boundary(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot, auth_headers: dict,
    ):
        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            r = await client.post(
                f"{API}/sightings",
                json={"parking_lot_id": test_parking_lot.id, "notes": "x" * 500},
                headers=auth_headers,
            )
        assert r.status_code == 201

    async def test_email_xss_attempt(self, client: AsyncClient, db_session: AsyncSession):
        device_id = str(uuid.uuid4())
        await client.post(f"{API}/auth/register", json={"device_id": device_id})

        r = await client.post(
            f"{API}/auth/send-otp",
            json={"device_id": device_id, "email": "<script>alert('xss')</script>"},
        )
        assert r.status_code == 422

    async def test_sql_injection_in_lot_code(
        self, client: AsyncClient, db_session: AsyncSession, auth_headers: dict,
    ):
        r = await client.get(
            f"{API}/lots/code/'; DROP TABLE parking_lots;--",
            headers=auth_headers,
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Access Control
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAccessControl:

    async def test_unverified_cannot_checkin(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot, unverified_auth_headers: dict,
    ):
        r = await client.post(
            f"{API}/sessions/checkin",
            json={"parking_lot_id": test_parking_lot.id},
            headers=unverified_auth_headers,
        )
        assert r.status_code == 403

    async def test_unverified_cannot_report_sighting(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot, unverified_auth_headers: dict,
    ):
        r = await client.post(
            f"{API}/sightings",
            json={"parking_lot_id": test_parking_lot.id},
            headers=unverified_auth_headers,
        )
        assert r.status_code == 403

    async def test_cannot_mark_other_device_notifications_read(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        dev_a, h_a = await _verified_device(db_session)
        _, h_b = await _verified_device(db_session)
        lot = await _create_lot(db_session, "AC Lot", "ACL1")

        notif = Notification(
            device_id=dev_a.id,
            notification_type=NotificationType.TAPS_SPOTTED,
            title="Alert",
            message="Test",
            parking_lot_id=lot.id,
        )
        db_session.add(notif)
        await db_session.commit()
        await db_session.refresh(notif)

        # Device B tries to mark A's notification as read
        r = await client.post(
            f"{API}/notifications/read",
            json={"notification_ids": [notif.id]},
            headers=h_b,
        )
        assert r.json()["marked_count"] == 0

        # Notification is still unread for A
        r = await client.get(f"{API}/notifications/unread", headers=h_a)
        assert r.json()["unread_count"] == 1

