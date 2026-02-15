"""
Tests for push notification sending: FCM (Android) and APNs (iOS).

Covers NotificationService.send_push_notification, _send_fcm, _send_apns,
_is_fcm_token, send_checkout_reminder, and notify_parked_users.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.notification import Notification, NotificationType
from app.models.parking_lot import ParkingLot
from app.models.parking_session import ParkingSession
from app.services.notification import NotificationService


# ---------------------------------------------------------------------------
# _is_fcm_token
# ---------------------------------------------------------------------------

class TestIsFcmToken:
    """Tests for FCM vs APNs token detection."""

    def test_fcm_token_detected(self):
        """Long token with colon → FCM (Android)."""
        fcm_token = "dGVzdDp0b2tlbjp3aXRoOmNvbG9ucw:APA91bExampleTokenHere1234567890"
        assert NotificationService._is_fcm_token(fcm_token) is True

    def test_apns_token_detected(self):
        """64-char hex string → APNs (iOS)."""
        apns_token = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
        assert NotificationService._is_fcm_token(apns_token) is False

    def test_short_non_hex_token_is_fcm(self):
        """Short but non-hex token → FCM (can't be APNs)."""
        token = "not-hex-at-all"
        assert NotificationService._is_fcm_token(token) is True


# ---------------------------------------------------------------------------
# send_push_notification (routes to _send_fcm or _send_apns)
# ---------------------------------------------------------------------------

class TestSendPushNotification:
    """Tests for the routing logic in send_push_notification."""

    @pytest.mark.asyncio
    async def test_routes_to_fcm_for_fcm_token(self):
        """FCM token → _send_fcm called."""
        fcm_token = "dGVzdDp0b2tlbjp3aXRoOmNvbG9ucw:APA91bExample"
        with patch.object(
            NotificationService, "_send_fcm", new_callable=AsyncMock, return_value=True
        ) as mock_fcm, patch.object(
            NotificationService, "_send_apns", new_callable=AsyncMock
        ) as mock_apns:
            result = await NotificationService.send_push_notification(
                fcm_token, "Title", "Body"
            )

            assert result is True
            mock_fcm.assert_called_once_with(fcm_token, "Title", "Body", None)
            mock_apns.assert_not_called()

    @pytest.mark.asyncio
    async def test_routes_to_apns_for_apns_token(self):
        """APNs token → _send_apns called."""
        apns_token = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
        with patch.object(
            NotificationService, "_send_apns", new_callable=AsyncMock, return_value=True
        ) as mock_apns, patch.object(
            NotificationService, "_send_fcm", new_callable=AsyncMock
        ) as mock_fcm:
            result = await NotificationService.send_push_notification(
                apns_token, "Title", "Body"
            )

            assert result is True
            mock_apns.assert_called_once_with(apns_token, "Title", "Body", None)
            mock_fcm.assert_not_called()

    @pytest.mark.asyncio
    async def test_passes_data_payload(self):
        """Extra data dict is forwarded to the underlying sender."""
        fcm_token = "dGVzdDp0b2tlbjp3aXRoOmNvbG9ucw:APA91bExample"
        data = {"type": "TAPS_SPOTTED", "lot_id": 1}
        with patch.object(
            NotificationService, "_send_fcm", new_callable=AsyncMock, return_value=True
        ) as mock_fcm:
            await NotificationService.send_push_notification(
                fcm_token, "Title", "Body", data
            )

            mock_fcm.assert_called_once_with(fcm_token, "Title", "Body", data)

    @pytest.mark.asyncio
    async def test_returns_false_on_send_failure(self):
        """If underlying sender returns False, so does send_push_notification."""
        fcm_token = "dGVzdDp0b2tlbjp3aXRoOmNvbG9ucw:APA91bExample"
        with patch.object(
            NotificationService, "_send_fcm", new_callable=AsyncMock, return_value=False
        ):
            result = await NotificationService.send_push_notification(
                fcm_token, "Title", "Body"
            )

            assert result is False


# ---------------------------------------------------------------------------
# _send_fcm
# ---------------------------------------------------------------------------

class TestSendFcm:
    """Tests for FCM sending with firebase_admin mocked."""

    @pytest.mark.asyncio
    async def test_send_fcm_success(self):
        """Successful FCM send returns True."""
        with patch("app.services.notification.FCM_IMPORTABLE", True), \
             patch("app.services.notification.firebase_admin") as mock_admin, \
             patch("app.services.notification.fcm_messaging") as mock_messaging:
            mock_admin.get_app.return_value = MagicMock()
            mock_messaging.Message = MagicMock()
            mock_messaging.Notification = MagicMock()
            mock_messaging.AndroidConfig = MagicMock()
            mock_messaging.AndroidNotification = MagicMock()
            mock_messaging.send = MagicMock(return_value="projects/test/messages/123")

            result = await NotificationService._send_fcm(
                "fcm-token:example", "Title", "Body"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_fcm_not_importable(self):
        """Firebase not installed → returns False."""
        with patch("app.services.notification.FCM_IMPORTABLE", False):
            result = await NotificationService._send_fcm(
                "fcm-token:example", "Title", "Body"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_fcm_not_initialized(self):
        """Firebase app not initialized → returns False."""
        with patch("app.services.notification.FCM_IMPORTABLE", True), \
             patch("app.services.notification.firebase_admin") as mock_admin:
            mock_admin.get_app.side_effect = ValueError("No app")

            result = await NotificationService._send_fcm(
                "fcm-token:example", "Title", "Body"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_fcm_send_error(self):
        """FCM send raises exception → returns False."""

        class _UnregisteredError(Exception):
            pass

        with patch("app.services.notification.FCM_IMPORTABLE", True), \
             patch("app.services.notification.firebase_admin") as mock_admin, \
             patch("app.services.notification.fcm_messaging") as mock_messaging:
            mock_admin.get_app.return_value = MagicMock()
            mock_messaging.Message = MagicMock()
            mock_messaging.Notification = MagicMock()
            mock_messaging.AndroidConfig = MagicMock()
            mock_messaging.AndroidNotification = MagicMock()
            mock_messaging.UnregisteredError = _UnregisteredError
            mock_messaging.send = MagicMock(side_effect=Exception("send failed"))

            result = await NotificationService._send_fcm(
                "fcm-token:example", "Title", "Body"
            )

            assert result is False


# ---------------------------------------------------------------------------
# _send_apns
# ---------------------------------------------------------------------------

class TestSendApns:
    """Tests for APNs sending with aioapns mocked."""

    @pytest.mark.asyncio
    async def test_send_apns_success(self):
        """Successful APNs send returns True."""
        mock_response = MagicMock()
        mock_response.is_successful = True

        mock_client = AsyncMock()
        mock_client.send_notification = AsyncMock(return_value=mock_response)

        with patch.object(
            NotificationService, "_get_apns_client", return_value=mock_client
        ):
            result = await NotificationService._send_apns(
                "a1b2c3d4" * 8, "Title", "Body"
            )

            assert result is True
            mock_client.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_apns_failure_response(self):
        """APNs returns unsuccessful → returns False."""
        mock_response = MagicMock()
        mock_response.is_successful = False
        mock_response.description = "BadDeviceToken"

        mock_client = AsyncMock()
        mock_client.send_notification = AsyncMock(return_value=mock_response)

        with patch.object(
            NotificationService, "_get_apns_client", return_value=mock_client
        ):
            result = await NotificationService._send_apns(
                "a1b2c3d4" * 8, "Title", "Body"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_apns_no_client(self):
        """APNs not configured (client is None) → returns False."""
        with patch.object(
            NotificationService, "_get_apns_client", return_value=None
        ):
            result = await NotificationService._send_apns(
                "a1b2c3d4" * 8, "Title", "Body"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_send_apns_exception(self):
        """APNs send raises exception → returns False."""
        mock_client = AsyncMock()
        mock_client.send_notification = AsyncMock(side_effect=Exception("conn error"))

        with patch.object(
            NotificationService, "_get_apns_client", return_value=mock_client
        ):
            result = await NotificationService._send_apns(
                "a1b2c3d4" * 8, "Title", "Body"
            )

            assert result is False


# ---------------------------------------------------------------------------
# send_checkout_reminder
# ---------------------------------------------------------------------------

class TestSendCheckoutReminder:
    """Tests for the checkout reminder flow."""

    @pytest.mark.asyncio
    async def test_sends_reminder_with_push(
        self, db_session: AsyncSession, active_session: ParkingSession,
        verified_device: Device, test_parking_lot: ParkingLot
    ):
        """Device with push enabled → in-app notification + push sent."""
        # Enable push on the device
        verified_device.is_push_enabled = True
        verified_device.push_token = "fcm-token:example"
        await db_session.commit()

        with patch.object(
            NotificationService, "send_push_notification",
            new_callable=AsyncMock, return_value=True,
        ) as mock_push:
            result = await NotificationService.send_checkout_reminder(
                db=db_session,
                session=active_session,
                device=verified_device,
                parking_lot_name=test_parking_lot.name,
            )

            assert result is True
            assert active_session.reminder_sent is True
            mock_push.assert_called_once()

    @pytest.mark.asyncio
    async def test_sends_reminder_without_push_token(
        self, db_session: AsyncSession, active_session: ParkingSession,
        verified_device: Device, test_parking_lot: ParkingLot
    ):
        """Device without push token → in-app notification only, no push."""
        verified_device.push_token = None
        verified_device.is_push_enabled = False
        await db_session.commit()

        with patch.object(
            NotificationService, "send_push_notification",
            new_callable=AsyncMock,
        ) as mock_push:
            result = await NotificationService.send_checkout_reminder(
                db=db_session,
                session=active_session,
                device=verified_device,
                parking_lot_name=test_parking_lot.name,
            )

            assert result is True
            assert active_session.reminder_sent is True
            mock_push.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_in_app_notification(
        self, db_session: AsyncSession, active_session: ParkingSession,
        verified_device: Device, test_parking_lot: ParkingLot
    ):
        """Reminder always creates a CHECKOUT_REMINDER notification in DB."""
        with patch.object(
            NotificationService, "send_push_notification",
            new_callable=AsyncMock, return_value=False,
        ):
            await NotificationService.send_checkout_reminder(
                db=db_session,
                session=active_session,
                device=verified_device,
                parking_lot_name=test_parking_lot.name,
            )

        from sqlalchemy import select
        result = await db_session.execute(
            select(Notification).where(
                Notification.device_id == verified_device.id,
                Notification.notification_type == NotificationType.CHECKOUT_REMINDER,
            )
        )
        notification = result.scalar_one()
        assert test_parking_lot.name in notification.message


# ---------------------------------------------------------------------------
# notify_parked_users
# ---------------------------------------------------------------------------

class TestNotifyParkedUsers:
    """Tests for notifying all users parked at a lot."""

    @pytest.mark.asyncio
    async def test_notify_single_parked_user(
        self, db_session: AsyncSession, active_session: ParkingSession,
        verified_device: Device, test_parking_lot: ParkingLot
    ):
        """One user parked → one notification created, returns 1."""
        with patch.object(
            NotificationService, "send_push_notification",
            new_callable=AsyncMock, return_value=True,
        ):
            count = await NotificationService.notify_parked_users(
                db=db_session,
                parking_lot_id=test_parking_lot.id,
                parking_lot_name=test_parking_lot.name,
            )

            assert count == 1

        from sqlalchemy import select
        result = await db_session.execute(
            select(Notification).where(
                Notification.device_id == verified_device.id,
                Notification.notification_type == NotificationType.TAPS_SPOTTED,
            )
        )
        assert result.scalar_one() is not None

    @pytest.mark.asyncio
    async def test_notify_no_parked_users(
        self, db_session: AsyncSession, test_parking_lot: ParkingLot
    ):
        """No active sessions → returns 0, no notifications created."""
        with patch.object(
            NotificationService, "send_push_notification",
            new_callable=AsyncMock,
        ) as mock_push:
            count = await NotificationService.notify_parked_users(
                db=db_session,
                parking_lot_id=test_parking_lot.id,
                parking_lot_name=test_parking_lot.name,
            )

            assert count == 0
            mock_push.assert_not_called()

    @pytest.mark.asyncio
    async def test_push_only_for_enabled_devices(
        self, db_session: AsyncSession, active_session: ParkingSession,
        verified_device: Device, test_parking_lot: ParkingLot
    ):
        """Device with push disabled → in-app notification but no push call."""
        verified_device.is_push_enabled = False
        verified_device.push_token = None
        await db_session.commit()

        with patch.object(
            NotificationService, "send_push_notification",
            new_callable=AsyncMock,
        ) as mock_push:
            count = await NotificationService.notify_parked_users(
                db=db_session,
                parking_lot_id=test_parking_lot.id,
                parking_lot_name=test_parking_lot.name,
            )

            assert count == 1  # still counted as notified (in-app)
            mock_push.assert_not_called()

    @pytest.mark.asyncio
    async def test_notify_multiple_users(
        self, db_session: AsyncSession, test_parking_lot: ParkingLot
    ):
        """Three users parked → three notifications, returns 3."""
        import uuid

        devices = []
        for _ in range(3):
            device = Device(
                device_id=str(uuid.uuid4()),
                email_verified=True,
                is_push_enabled=False,
            )
            db_session.add(device)
            await db_session.flush()
            devices.append(device)

            session = ParkingSession(
                device_id=device.id,
                parking_lot_id=test_parking_lot.id,
                checked_in_at=datetime.now(timezone.utc) - timedelta(hours=1),
                reminder_sent=False,
            )
            db_session.add(session)

        await db_session.commit()

        with patch.object(
            NotificationService, "send_push_notification",
            new_callable=AsyncMock, return_value=True,
        ):
            count = await NotificationService.notify_parked_users(
                db=db_session,
                parking_lot_id=test_parking_lot.id,
                parking_lot_name=test_parking_lot.name,
            )

            assert count == 3
