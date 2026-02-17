"""
Integration tests — cross-module data flow verification.

Tests that exercise multiple API endpoints and services together to verify
end-to-end behavior including checkin/checkout stats, sighting→prediction→notification
flows, feed+voting, and auth lifecycle.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.parking_lot import ParkingLot
from app.models.parking_session import ParkingSession
from app.models.taps_sighting import TapsSighting
from app.models.notification import Notification, NotificationType
from app.services.auth import AuthService
from app.services.notification import NotificationService
from app.services.reminder import ReminderService
from app.services.otp import OTPService
from app.services.email import EmailService

API = "/api/v1"


async def create_verified_device_with_headers(
    db_session: AsyncSession,
    push_token: str | None = None,
    is_push_enabled: bool = False,
) -> tuple[Device, dict]:
    """Create a verified device and return (device, auth_headers)."""
    device = Device(
        device_id=str(uuid.uuid4()),
        email_verified=True,
        is_push_enabled=is_push_enabled,
        push_token=push_token,
    )
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    token = AuthService.create_access_token(device.device_id)
    return device, {"Authorization": f"Bearer {token}"}


async def _create_lot(db: AsyncSession, name: str, code: str) -> ParkingLot:
    lot = ParkingLot(name=name, code=code, latitude=38.54, longitude=-121.76, is_active=True)
    db.add(lot)
    await db.commit()
    await db.refresh(lot)
    return lot


# ---------------------------------------------------------------------------
# Checkin / Checkout → Lot Stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestCheckinCheckoutLotStats:

    async def test_checkin_increases_active_parkers(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot, auth_headers: dict,
    ):
        r = await client.get(f"{API}/lots/{test_parking_lot.id}", headers=auth_headers)
        assert r.json()["active_parkers"] == 0

        r = await client.post(
            f"{API}/sessions/checkin",
            json={"parking_lot_id": test_parking_lot.id},
            headers=auth_headers,
        )
        assert r.status_code == 201

        r = await client.get(f"{API}/lots/{test_parking_lot.id}", headers=auth_headers)
        assert r.json()["active_parkers"] == 1

    async def test_checkout_decreases_active_parkers(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot, auth_headers: dict,
    ):
        await client.post(
            f"{API}/sessions/checkin",
            json={"parking_lot_id": test_parking_lot.id},
            headers=auth_headers,
        )
        r = await client.get(f"{API}/lots/{test_parking_lot.id}", headers=auth_headers)
        assert r.json()["active_parkers"] == 1

        await client.post(f"{API}/sessions/checkout", headers=auth_headers)

        r = await client.get(f"{API}/lots/{test_parking_lot.id}", headers=auth_headers)
        assert r.json()["active_parkers"] == 0

    async def test_multiple_users_parked_at_lot(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot,
    ):
        devices = [await create_verified_device_with_headers(db_session) for _ in range(3)]

        for _, hdrs in devices:
            r = await client.post(
                f"{API}/sessions/checkin",
                json={"parking_lot_id": test_parking_lot.id},
                headers=hdrs,
            )
            assert r.status_code == 201

        r = await client.get(f"{API}/lots/{test_parking_lot.id}", headers=devices[0][1])
        assert r.json()["active_parkers"] == 3

        await client.post(f"{API}/sessions/checkout", headers=devices[0][1])

        r = await client.get(f"{API}/lots/{test_parking_lot.id}", headers=devices[1][1])
        assert r.json()["active_parkers"] == 2

    async def test_checkin_only_affects_target_lot(
        self, client: AsyncClient, db_session: AsyncSession, auth_headers: dict,
    ):
        lot_a = await _create_lot(db_session, "Lot A", "LOTA")
        lot_b = await _create_lot(db_session, "Lot B", "LOTB")

        await client.post(
            f"{API}/sessions/checkin",
            json={"parking_lot_id": lot_a.id},
            headers=auth_headers,
        )

        r = await client.get(f"{API}/lots/{lot_a.id}", headers=auth_headers)
        assert r.json()["active_parkers"] == 1

        r = await client.get(f"{API}/lots/{lot_b.id}", headers=auth_headers)
        assert r.json()["active_parkers"] == 0

    async def test_checkout_after_lot_switch(
        self, client: AsyncClient, db_session: AsyncSession, auth_headers: dict,
    ):
        lot_a = await _create_lot(db_session, "Lot A", "LOTA")
        lot_b = await _create_lot(db_session, "Lot B", "LOTB")

        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot_a.id}, headers=auth_headers)
        await client.post(f"{API}/sessions/checkout", headers=auth_headers)
        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot_b.id}, headers=auth_headers)

        r = await client.get(f"{API}/lots/{lot_a.id}", headers=auth_headers)
        assert r.json()["active_parkers"] == 0

        r = await client.get(f"{API}/lots/{lot_b.id}", headers=auth_headers)
        assert r.json()["active_parkers"] == 1


# ---------------------------------------------------------------------------
# Sighting → Prediction / Lot Stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSightingPredictionLotStats:

    async def test_sighting_updates_lot_risk_level(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot, auth_headers: dict,
    ):
        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            r = await client.post(
                f"{API}/sightings",
                json={"parking_lot_id": test_parking_lot.id},
                headers=auth_headers,
            )
            assert r.status_code == 201

        r = await client.get(f"{API}/predictions/{test_parking_lot.id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["probability"] == 0.8

    async def test_sighting_updates_prediction_endpoint(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot, auth_headers: dict,
    ):
        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(
                f"{API}/sightings",
                json={"parking_lot_id": test_parking_lot.id},
                headers=auth_headers,
            )

        r = await client.get(f"{API}/predictions/{test_parking_lot.id}", headers=auth_headers)
        assert r.json()["risk_level"] == "HIGH"

    async def test_sighting_increments_recent_sightings_count(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot,
    ):
        devs = [await create_verified_device_with_headers(db_session) for _ in range(2)]

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            for _, hdrs in devs:
                r = await client.post(
                    f"{API}/sightings",
                    json={"parking_lot_id": test_parking_lot.id},
                    headers=hdrs,
                )
                assert r.status_code == 201

        r = await client.get(f"{API}/lots/{test_parking_lot.id}", headers=devs[0][1])
        assert r.json()["recent_sightings"] == 2

    async def test_sighting_at_lot_a_does_not_affect_lot_b_prediction(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot_a = await _create_lot(db_session, "Lot A", "LOTA")
        lot_b = await _create_lot(db_session, "Lot B", "LOTB")
        _, hdrs = await create_verified_device_with_headers(db_session)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot_a.id}, headers=hdrs)

        r = await client.get(f"{API}/predictions/{lot_a.id}", headers=hdrs)
        assert r.json()["risk_level"] == "HIGH"

        r = await client.get(f"{API}/predictions/{lot_b.id}", headers=hdrs)
        assert r.json()["risk_level"] == "MEDIUM"

    async def test_prediction_changes_as_sighting_ages(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Age Lot", "AGEL")
        dev, hdrs = await create_verified_device_with_headers(db_session)

        pacific = ZoneInfo("America/Los_Angeles")
        now_pacific = datetime.now(pacific)
        base_pacific = now_pacific.replace(hour=10, minute=0, second=0, microsecond=0)
        base_time = base_pacific.astimezone(timezone.utc)

        sighting = TapsSighting(
            parking_lot_id=lot.id,
            reported_by_device_id=dev.id,
            reported_at=base_time,
        )
        db_session.add(sighting)
        await db_session.commit()

        offsets_expected = [
            (timedelta(hours=0.5), "HIGH"),
            (timedelta(hours=1.5), "LOW"),
            (timedelta(hours=3), "MEDIUM"),
            (timedelta(hours=5), "HIGH"),
        ]
        for offset, expected_level in offsets_expected:
            ts = (base_time + offset).isoformat()
            r = await client.post(
                f"{API}/predictions",
                json={"parking_lot_id": lot.id, "timestamp": ts},
                headers=hdrs,
            )
            assert r.status_code == 200, f"offset={offset}"
            assert r.json()["risk_level"] == expected_level, (
                f"offset={offset}: expected {expected_level}, got {r.json()['risk_level']}"
            )

    async def test_newer_sighting_overrides_older_for_prediction(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Override Lot", "OVER")
        dev, hdrs = await create_verified_device_with_headers(db_session)

        old = TapsSighting(
            parking_lot_id=lot.id,
            reported_by_device_id=dev.id,
            reported_at=datetime.now(timezone.utc) - timedelta(hours=3),
        )
        db_session.add(old)
        await db_session.commit()

        r = await client.get(f"{API}/predictions/{lot.id}", headers=hdrs)
        assert r.json()["risk_level"] == "MEDIUM"

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=hdrs)

        r = await client.get(f"{API}/predictions/{lot.id}", headers=hdrs)
        assert r.json()["risk_level"] == "HIGH"

    async def test_prediction_no_sighting_default(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Empty Lot", "EMPT")
        _, hdrs = await create_verified_device_with_headers(db_session)

        r = await client.get(f"{API}/predictions/{lot.id}", headers=hdrs)
        assert r.json()["risk_level"] == "MEDIUM"


# ---------------------------------------------------------------------------
# Sighting → Notification Flow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSightingNotificationFlow:

    async def test_sighting_creates_notifications_for_parked_users(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Notif Lot", "NTF1")
        d1, h1 = await create_verified_device_with_headers(db_session)
        d2, h2 = await create_verified_device_with_headers(db_session)
        _, reporter_h = await create_verified_device_with_headers(db_session)

        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=h1)
        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=h2)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=reporter_h)

        r1 = await client.get(f"{API}/notifications/unread", headers=h1)
        r2 = await client.get(f"{API}/notifications/unread", headers=h2)
        assert r1.json()["unread_count"] >= 1
        assert r2.json()["unread_count"] >= 1

    async def test_reporter_also_gets_notified(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        """Reporter who is also parked DOES receive a notification (actual behavior)."""
        lot = await _create_lot(db_session, "Reporter Lot", "RPT1")
        dev, hdrs = await create_verified_device_with_headers(db_session)

        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=hdrs)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=hdrs)

        r = await client.get(f"{API}/notifications/unread", headers=hdrs)
        assert r.json()["unread_count"] >= 1

    async def test_checked_out_user_not_notified(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Checkout Lot", "CKO1")
        d_a, h_a = await create_verified_device_with_headers(db_session)
        _, h_b = await create_verified_device_with_headers(db_session)

        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=h_a)
        await client.post(f"{API}/sessions/checkout", headers=h_a)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=h_b)

        r = await client.get(f"{API}/notifications/unread", headers=h_a)
        assert r.json()["unread_count"] == 0

    async def test_checkin_sighting_checkout_sighting_sequence(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Seq Lot", "SEQ1")
        d_a, h_a = await create_verified_device_with_headers(db_session)
        _, h_r1 = await create_verified_device_with_headers(db_session)
        _, h_r2 = await create_verified_device_with_headers(db_session)

        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=h_a)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=h_r1)

        r = await client.get(f"{API}/notifications/unread", headers=h_a)
        assert r.json()["unread_count"] == 1

        await client.post(f"{API}/sessions/checkout", headers=h_a)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=h_r2)

        r = await client.get(f"{API}/notifications/unread", headers=h_a)
        assert r.json()["unread_count"] == 1  # still 1, not 2

    async def test_notification_targets_only_users_at_sighted_lot(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot1 = await _create_lot(db_session, "Target 1", "TGT1")
        lot2 = await _create_lot(db_session, "Target 2", "TGT2")
        d_a, h_a = await create_verified_device_with_headers(db_session)
        d_b, h_b = await create_verified_device_with_headers(db_session)
        _, h_r = await create_verified_device_with_headers(db_session)

        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot1.id}, headers=h_a)
        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot2.id}, headers=h_b)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot1.id}, headers=h_r)

        r_a = await client.get(f"{API}/notifications/unread", headers=h_a)
        r_b = await client.get(f"{API}/notifications/unread", headers=h_b)
        assert r_a.json()["unread_count"] >= 1
        assert r_b.json()["unread_count"] == 0

    async def test_sighting_notification_count_matches_parked_users(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Count Lot", "CNT1")
        devs = [await create_verified_device_with_headers(db_session) for _ in range(5)]
        _, h_reporter = await create_verified_device_with_headers(db_session)

        for _, h in devs:
            await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=h)

        # 2 check out
        await client.post(f"{API}/sessions/checkout", headers=devs[0][1])
        await client.post(f"{API}/sessions/checkout", headers=devs[1][1])

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            r = await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=h_reporter)

        assert r.status_code == 201
        assert r.json()["users_notified"] == 3


# ---------------------------------------------------------------------------
# Checkin Reminder → Notification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestCheckinReminderNotification:

    async def test_full_reminder_flow(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        dev, hdrs = await create_verified_device_with_headers(db_session)
        lot = await _create_lot(db_session, "Rem Lot", "REM1")

        session = ParkingSession(
            device_id=dev.id,
            parking_lot_id=lot.id,
            checked_in_at=datetime.now(timezone.utc) - timedelta(hours=4),
            reminder_sent=False,
        )
        db_session.add(session)
        await db_session.commit()

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            count = await ReminderService.process_pending_reminders(db_session)
        assert count == 1

        r = await client.get(f"{API}/notifications/unread", headers=hdrs)
        assert r.json()["unread_count"] == 1

        await db_session.refresh(session)
        assert session.reminder_sent is True

        # Process again → no duplicate
        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            count = await ReminderService.process_pending_reminders(db_session)
        assert count == 0

    async def test_checkout_before_reminder_prevents_notification(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        dev, hdrs = await create_verified_device_with_headers(db_session)
        lot = await _create_lot(db_session, "Rem2 Lot", "REM2")

        session = ParkingSession(
            device_id=dev.id,
            parking_lot_id=lot.id,
            checked_in_at=datetime.now(timezone.utc) - timedelta(hours=4),
            checked_out_at=datetime.now(timezone.utc) - timedelta(hours=2),
            reminder_sent=False,
        )
        db_session.add(session)
        await db_session.commit()

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            count = await ReminderService.process_pending_reminders(db_session)
        assert count == 0

    async def test_reminder_does_not_fire_for_recent_session(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        dev, _ = await create_verified_device_with_headers(db_session)
        lot = await _create_lot(db_session, "Rem3 Lot", "REM3")

        session = ParkingSession(
            device_id=dev.id,
            parking_lot_id=lot.id,
            checked_in_at=datetime.now(timezone.utc) - timedelta(hours=2),
            reminder_sent=False,
        )
        db_session.add(session)
        await db_session.commit()

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            count = await ReminderService.process_pending_reminders(db_session)
        assert count == 0

    async def test_multiple_users_get_independent_reminders(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot1 = await _create_lot(db_session, "MR Lot1", "MRL1")
        lot2 = await _create_lot(db_session, "MR Lot2", "MRL2")
        d1, _ = await create_verified_device_with_headers(db_session)
        d2, _ = await create_verified_device_with_headers(db_session)

        for dev, lot in [(d1, lot1), (d2, lot2)]:
            s = ParkingSession(
                device_id=dev.id,
                parking_lot_id=lot.id,
                checked_in_at=datetime.now(timezone.utc) - timedelta(hours=4),
                reminder_sent=False,
            )
            db_session.add(s)
        await db_session.commit()

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            count = await ReminderService.process_pending_reminders(db_session)
        assert count == 2


# ---------------------------------------------------------------------------
# Voting → Feed Display
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestVotingFeedDisplay:

    async def _create_sighting_at(self, client, db_session, lot_id, headers):
        """Helper: report a sighting and return its id."""
        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            r = await client.post(
                f"{API}/sightings",
                json={"parking_lot_id": lot_id},
                headers=headers,
            )
        assert r.status_code == 201
        return r.json()["id"]

    async def test_vote_reflected_in_feed(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Vote Lot", "VT01")
        _, hdrs = await create_verified_device_with_headers(db_session)

        sid = await self._create_sighting_at(client, db_session, lot.id, hdrs)

        r = await client.get(f"{API}/feed/{lot.id}", headers=hdrs)
        s = r.json()["sightings"][0]
        assert s["upvotes"] == 0 and s["downvotes"] == 0

        await client.post(f"{API}/feed/sightings/{sid}/vote", json={"vote_type": "upvote"}, headers=hdrs)

        r = await client.get(f"{API}/feed/{lot.id}", headers=hdrs)
        s = r.json()["sightings"][0]
        assert s["upvotes"] == 1 and s["downvotes"] == 0

    async def test_vote_change_reflected_in_feed(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "VChg Lot", "VT02")
        _, hdrs = await create_verified_device_with_headers(db_session)
        sid = await self._create_sighting_at(client, db_session, lot.id, hdrs)

        await client.post(f"{API}/feed/sightings/{sid}/vote", json={"vote_type": "upvote"}, headers=hdrs)

        # Voting differently updates the vote
        await client.post(f"{API}/feed/sightings/{sid}/vote", json={"vote_type": "downvote"}, headers=hdrs)

        r = await client.get(f"{API}/feed/{lot.id}", headers=hdrs)
        s = r.json()["sightings"][0]
        assert s["upvotes"] == 0 and s["downvotes"] == 1

    async def test_remove_vote_reflected_in_feed(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "VRem Lot", "VT03")
        _, hdrs = await create_verified_device_with_headers(db_session)
        sid = await self._create_sighting_at(client, db_session, lot.id, hdrs)

        await client.post(f"{API}/feed/sightings/{sid}/vote", json={"vote_type": "upvote"}, headers=hdrs)
        await client.delete(f"{API}/feed/sightings/{sid}/vote", headers=hdrs)

        r = await client.get(f"{API}/feed/{lot.id}", headers=hdrs)
        s = r.json()["sightings"][0]
        assert s["upvotes"] == 0 and s["downvotes"] == 0

    async def test_vote_tallies_with_multiple_voters(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "VTally Lot", "VT04")
        voters = [await create_verified_device_with_headers(db_session) for _ in range(3)]
        sid = await self._create_sighting_at(client, db_session, lot.id, voters[0][1])

        # 2 upvote, 1 downvote
        await client.post(f"{API}/feed/sightings/{sid}/vote", json={"vote_type": "upvote"}, headers=voters[0][1])
        await client.post(f"{API}/feed/sightings/{sid}/vote", json={"vote_type": "upvote"}, headers=voters[1][1])
        await client.post(f"{API}/feed/sightings/{sid}/vote", json={"vote_type": "downvote"}, headers=voters[2][1])

        r = await client.get(f"{API}/feed/{lot.id}", headers=voters[0][1])
        s = r.json()["sightings"][0]
        assert s["upvotes"] == 2
        assert s["downvotes"] == 1

    async def test_votes_isolated_per_sighting(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "VIso Lot", "VT05")
        d1, h1 = await create_verified_device_with_headers(db_session)
        d2, h2 = await create_verified_device_with_headers(db_session)
        sid_a = await self._create_sighting_at(client, db_session, lot.id, h1)
        sid_b = await self._create_sighting_at(client, db_session, lot.id, h2)

        await client.post(f"{API}/feed/sightings/{sid_a}/vote", json={"vote_type": "upvote"}, headers=h1)
        await client.post(f"{API}/feed/sightings/{sid_b}/vote", json={"vote_type": "downvote"}, headers=h1)

        r = await client.get(f"{API}/feed/{lot.id}", headers=h1)
        sightings = {s["id"]: s for s in r.json()["sightings"]}
        assert sightings[sid_a]["upvotes"] == 1 and sightings[sid_a]["downvotes"] == 0
        assert sightings[sid_b]["upvotes"] == 0 and sightings[sid_b]["downvotes"] == 1

    async def test_feed_shows_current_user_vote_status(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "VUser Lot", "VT06")
        _, h_a = await create_verified_device_with_headers(db_session)
        _, h_b = await create_verified_device_with_headers(db_session)
        sid = await self._create_sighting_at(client, db_session, lot.id, h_a)

        await client.post(f"{API}/feed/sightings/{sid}/vote", json={"vote_type": "upvote"}, headers=h_a)

        r = await client.get(f"{API}/feed/{lot.id}", headers=h_a)
        assert r.json()["sightings"][0]["user_vote"] == "upvote"

        r = await client.get(f"{API}/feed/{lot.id}", headers=h_b)
        assert r.json()["sightings"][0]["user_vote"] is None


# ---------------------------------------------------------------------------
# Sighting Feed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSightingFeed:

    async def test_new_sighting_appears_in_feed(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Feed Lot", "FD01")
        _, hdrs = await create_verified_device_with_headers(db_session)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=hdrs)

        r = await client.get(f"{API}/feed/{lot.id}", headers=hdrs)
        assert r.json()["total_sightings"] == 1

    async def test_sighting_disappears_from_feed_after_3_hours(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Old Feed", "FD02")
        dev, hdrs = await create_verified_device_with_headers(db_session)

        sighting = TapsSighting(
            parking_lot_id=lot.id,
            reported_by_device_id=dev.id,
            reported_at=datetime.now(timezone.utc) - timedelta(hours=4),
        )
        db_session.add(sighting)
        await db_session.commit()

        r = await client.get(f"{API}/feed/{lot.id}", headers=hdrs)
        assert r.json()["total_sightings"] == 0

    async def test_sighting_at_lot_a_not_in_lot_b_feed(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot_a = await _create_lot(db_session, "Feed A", "FDA1")
        lot_b = await _create_lot(db_session, "Feed B", "FDB1")
        _, hdrs = await create_verified_device_with_headers(db_session)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot_a.id}, headers=hdrs)

        r = await client.get(f"{API}/feed/{lot_a.id}", headers=hdrs)
        assert r.json()["total_sightings"] == 1

        r = await client.get(f"{API}/feed/{lot_b.id}", headers=hdrs)
        assert r.json()["total_sightings"] == 0

    async def test_all_feeds_groups_by_lot(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot_a = await _create_lot(db_session, "Group A", "GRA1")
        lot_b = await _create_lot(db_session, "Group B", "GRB1")
        devs = [await create_verified_device_with_headers(db_session) for _ in range(3)]

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot_a.id}, headers=devs[0][1])
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot_b.id}, headers=devs[1][1])
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot_b.id}, headers=devs[2][1])

        r = await client.get(f"{API}/feed", headers=devs[0][1])
        data = r.json()
        feeds = {f["parking_lot_id"]: f for f in data["feeds"]}
        assert feeds[lot_a.id]["total_sightings"] == 1
        assert feeds[lot_b.id]["total_sightings"] == 2


# ---------------------------------------------------------------------------
# Auth Flow → Protected Endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAuthFlowProtectedEndpoints:

    async def test_full_registration_to_action_flow(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "Auth Lot", "AUTH")
        device_id = str(uuid.uuid4())

        # Register
        r = await client.post(f"{API}/auth/register", json={"device_id": device_id})
        assert r.status_code == 201
        token = r.json()["access_token"]
        hdrs = {"Authorization": f"Bearer {token}"}

        # Unverified → 403 on checkin
        r = await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=hdrs)
        assert r.status_code == 403

        # Verify email via OTP
        with patch.object(OTPService, "generate_otp", return_value="123456"), \
             patch.object(EmailService, "send_otp_email", new_callable=AsyncMock):
            r = await client.post(
                f"{API}/auth/send-otp",
                json={"device_id": device_id, "email": "test@ucdavis.edu"},
            )
            assert r.status_code == 200

        r = await client.post(
            f"{API}/auth/verify-otp",
            json={"device_id": device_id, "email": "test@ucdavis.edu", "otp_code": "123456"},
        )
        assert r.status_code == 200
        assert r.json()["email_verified"] is True

        # Now checkin works
        r = await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=hdrs)
        assert r.status_code == 201

        # Checkout before sighting (avoid duplicate session issues)
        await client.post(f"{API}/sessions/checkout", headers=hdrs)

        # Sighting works
        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            r = await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=hdrs)
        assert r.status_code == 201

    async def test_token_persistence_across_re_registration(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        device_id = str(uuid.uuid4())

        r1 = await client.post(f"{API}/auth/register", json={"device_id": device_id})
        token_a = r1.json()["access_token"]

        r2 = await client.post(f"{API}/auth/register", json={"device_id": device_id})
        token_b = r2.json()["access_token"]

        # Both tokens work and reference the same device
        me_a = await client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token_a}"})
        me_b = await client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token_b}"})
        assert me_a.status_code == 200
        assert me_b.status_code == 200
        assert me_a.json()["id"] == me_b.json()["id"]


# ---------------------------------------------------------------------------
# Notification Lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestNotificationLifecycle:

    async def test_notification_lifecycle(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "NLC Lot", "NLC1")
        d_parker, h_parker = await create_verified_device_with_headers(db_session)
        _, h_reporter = await create_verified_device_with_headers(db_session)

        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=h_parker)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=h_reporter)

        # Unread = 1
        r = await client.get(f"{API}/notifications/unread", headers=h_parker)
        assert r.json()["unread_count"] == 1
        nid = r.json()["notifications"][0]["id"]

        # Mark read
        await client.post(f"{API}/notifications/read", json={"notification_ids": [nid]}, headers=h_parker)

        # Unread = 0
        r = await client.get(f"{API}/notifications/unread", headers=h_parker)
        assert r.json()["unread_count"] == 0

        # Still visible in all notifications
        r = await client.get(f"{API}/notifications", headers=h_parker)
        assert r.json()["total"] >= 1

    async def test_mark_all_read_clears_unread_count(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        dev, hdrs = await create_verified_device_with_headers(db_session)
        lot = await _create_lot(db_session, "MAR Lot", "MAR1")

        for i in range(3):
            n = Notification(
                device_id=dev.id,
                notification_type=NotificationType.TAPS_SPOTTED,
                title=f"Alert {i}",
                message=f"Test {i}",
                parking_lot_id=lot.id,
            )
            db_session.add(n)
        await db_session.commit()

        r = await client.get(f"{API}/notifications/unread", headers=hdrs)
        assert r.json()["unread_count"] == 3

        await client.post(f"{API}/notifications/read/all", headers=hdrs)

        r = await client.get(f"{API}/notifications/unread", headers=hdrs)
        assert r.json()["unread_count"] == 0

    async def test_new_notification_after_mark_read(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        lot = await _create_lot(db_session, "NNew Lot", "NNW1")
        d_parker, h_parker = await create_verified_device_with_headers(db_session)
        _, h_r1 = await create_verified_device_with_headers(db_session)
        _, h_r2 = await create_verified_device_with_headers(db_session)

        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=h_parker)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=h_r1)

        await client.post(f"{API}/notifications/read/all", headers=h_parker)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True):
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=h_r2)

        r = await client.get(f"{API}/notifications/unread", headers=h_parker)
        assert r.json()["unread_count"] == 1


# ---------------------------------------------------------------------------
# Push Token → Notification Delivery
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestPushTokenNotificationDelivery:

    async def test_push_token_update_affects_notification_delivery(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        # Device without push token
        dev, hdrs = await create_verified_device_with_headers(db_session)
        lot = await _create_lot(db_session, "Push Lot", "PSH1")
        _, h_r1 = await create_verified_device_with_headers(db_session)
        _, h_r2 = await create_verified_device_with_headers(db_session)

        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=hdrs)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True) as mock_push:
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=h_r1)
            mock_push.assert_not_called()

        # Add push token
        await client.patch(
            f"{API}/auth/me",
            json={"push_token": "fake-fcm-token:abc123", "is_push_enabled": True},
            headers=hdrs,
        )

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True) as mock_push:
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=h_r2)
            mock_push.assert_called()

    async def test_push_disabled_skips_push_but_creates_in_app(
        self, client: AsyncClient, db_session: AsyncSession,
    ):
        dev, hdrs = await create_verified_device_with_headers(
            db_session, push_token="fake-token:xyz", is_push_enabled=False,
        )
        lot = await _create_lot(db_session, "PushDis Lot", "PDIS")
        _, h_reporter = await create_verified_device_with_headers(db_session)

        await client.post(f"{API}/sessions/checkin", json={"parking_lot_id": lot.id}, headers=hdrs)

        with patch.object(NotificationService, "send_push_notification", new_callable=AsyncMock, return_value=True) as mock_push:
            await client.post(f"{API}/sightings", json={"parking_lot_id": lot.id}, headers=h_reporter)
            mock_push.assert_not_called()

        r = await client.get(f"{API}/notifications/unread", headers=hdrs)
        assert r.json()["unread_count"] >= 1


# ---------------------------------------------------------------------------
# Session State / Current Endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSessionStateCurrentEndpoint:

    async def test_current_session_reflects_checkin(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot, auth_headers: dict,
    ):
        r = await client.get(f"{API}/sessions/current", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() is None

        await client.post(
            f"{API}/sessions/checkin",
            json={"parking_lot_id": test_parking_lot.id},
            headers=auth_headers,
        )

        r = await client.get(f"{API}/sessions/current", headers=auth_headers)
        data = r.json()
        assert data is not None
        assert data["is_active"] is True

    async def test_current_session_reflects_checkout(
        self, client: AsyncClient, db_session: AsyncSession,
        test_parking_lot: ParkingLot, auth_headers: dict,
    ):
        await client.post(
            f"{API}/sessions/checkin",
            json={"parking_lot_id": test_parking_lot.id},
            headers=auth_headers,
        )
        r = await client.get(f"{API}/sessions/current", headers=auth_headers)
        assert r.json()["is_active"] is True

        await client.post(f"{API}/sessions/checkout", headers=auth_headers)

        r = await client.get(f"{API}/sessions/current", headers=auth_headers)
        assert r.json() is None

    async def test_session_history_grows_with_completed_sessions(
        self, client: AsyncClient, db_session: AsyncSession,
        auth_headers: dict, verified_device: Device,
    ):
        lot_a = await _create_lot(db_session, "Hist A", "HSA1")
        lot_b = await _create_lot(db_session, "Hist B", "HSB1")

        # Create sessions with explicit timestamps so ordering is deterministic
        # (SQLite func.now() has second-level precision; two fast API calls
        # can land on the same second, making order non-deterministic).
        now = datetime.now(timezone.utc)
        s1 = ParkingSession(
            device_id=verified_device.id,
            parking_lot_id=lot_a.id,
            checked_in_at=now - timedelta(hours=3),
            checked_out_at=now - timedelta(hours=2),
        )
        s2 = ParkingSession(
            device_id=verified_device.id,
            parking_lot_id=lot_b.id,
            checked_in_at=now - timedelta(hours=1),
            checked_out_at=now - timedelta(minutes=30),
        )
        db_session.add_all([s1, s2])
        await db_session.commit()

        r = await client.get(f"{API}/sessions/history", headers=auth_headers)
        history = r.json()
        assert len(history) == 2
        # Most recent first
        assert history[0]["parking_lot_id"] == lot_b.id
        assert history[1]["parking_lot_id"] == lot_a.id
