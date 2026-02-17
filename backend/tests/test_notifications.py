"""
Tests for notification endpoints and services.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parking_lot import ParkingLot
from app.models.device import Device
from app.models.notification import Notification, NotificationType
from app.services.notification import NotificationService


class TestNotificationService:
    """Tests for NotificationService class."""

    @pytest.mark.asyncio
    async def test_create_notification(
        self,
        db_session: AsyncSession,
        verified_device: Device,
        test_parking_lot: ParkingLot
    ):
        """Test creating a notification."""
        notification = await NotificationService.create_notification(
            db=db_session,
            device=verified_device,
            notification_type=NotificationType.TAPS_SPOTTED,
            title="Test Alert",
            message="Test message",
            parking_lot_id=test_parking_lot.id,
        )

        assert notification.id is not None
        assert notification.device_id == verified_device.id
        assert notification.notification_type == NotificationType.TAPS_SPOTTED
        assert notification.title == "Test Alert"
        assert notification.is_read is False

    @pytest.mark.asyncio
    async def test_get_unread_notifications(
        self,
        db_session: AsyncSession,
        verified_device: Device
    ):
        """Test getting unread notifications."""
        # Create some notifications
        for i in range(3):
            await NotificationService.create_notification(
                db=db_session,
                device=verified_device,
                notification_type=NotificationType.TAPS_SPOTTED,
                title=f"Alert {i}",
                message=f"Message {i}",
            )

        unread = await NotificationService.get_unread_notifications(
            db=db_session,
            device=verified_device,
        )

        assert len(unread) == 3

    @pytest.mark.asyncio
    async def test_mark_notifications_read(
        self,
        db_session: AsyncSession,
        verified_device: Device
    ):
        """Test marking notifications as read."""
        # Create notification
        notification = await NotificationService.create_notification(
            db=db_session,
            device=verified_device,
            notification_type=NotificationType.TAPS_SPOTTED,
            title="Test",
            message="Test",
        )

        # Mark as read
        marked = await NotificationService.mark_notifications_read(
            db=db_session,
            device=verified_device,
            notification_ids=[notification.id],
        )

        assert marked == 1

        # Verify it's read
        unread = await NotificationService.get_unread_notifications(
            db=db_session,
            device=verified_device,
        )
        assert len(unread) == 0

    @pytest.mark.asyncio
    async def test_create_notification_checkout_reminder(
        self,
        db_session: AsyncSession,
        verified_device: Device,
        test_parking_lot: ParkingLot,
    ):
        """Test creating a CHECKOUT_REMINDER notification."""
        notification = await NotificationService.create_notification(
            db=db_session,
            device=verified_device,
            notification_type=NotificationType.CHECKOUT_REMINDER,
            title="Still parked?",
            message="You've been parked for 3 hours",
            parking_lot_id=test_parking_lot.id,
        )

        assert notification.notification_type == NotificationType.CHECKOUT_REMINDER
        assert notification.parking_lot_id == test_parking_lot.id

    @pytest.mark.asyncio
    async def test_get_unread_respects_limit(
        self,
        db_session: AsyncSession,
        verified_device: Device,
    ):
        """Limit parameter caps number of returned notifications."""
        for i in range(5):
            await NotificationService.create_notification(
                db=db_session,
                device=verified_device,
                notification_type=NotificationType.TAPS_SPOTTED,
                title=f"Alert {i}",
                message=f"Message {i}",
            )

        unread = await NotificationService.get_unread_notifications(
            db=db_session, device=verified_device, limit=2
        )

        assert len(unread) == 2

    @pytest.mark.asyncio
    async def test_get_all_notifications_pagination(
        self,
        db_session: AsyncSession,
        verified_device: Device,
    ):
        """Offset and limit paginate correctly."""
        for i in range(5):
            await NotificationService.create_notification(
                db=db_session,
                device=verified_device,
                notification_type=NotificationType.TAPS_SPOTTED,
                title=f"Alert {i}",
                message=f"Message {i}",
            )

        notifications, unread_count, total_count = await NotificationService.get_all_notifications(
            db=db_session, device=verified_device, limit=2, offset=0
        )

        assert len(notifications) == 2
        assert total_count == 5
        assert unread_count == 5

    @pytest.mark.asyncio
    async def test_mark_empty_list_read(
        self,
        db_session: AsyncSession,
        verified_device: Device,
    ):
        """Marking an empty list of IDs → 0 updated."""
        marked = await NotificationService.mark_notifications_read(
            db=db_session, device=verified_device, notification_ids=[]
        )

        assert marked == 0

    @pytest.mark.asyncio
    async def test_get_unread_empty(
        self,
        db_session: AsyncSession,
        verified_device: Device,
    ):
        """No notifications → empty list."""
        unread = await NotificationService.get_unread_notifications(
            db=db_session, device=verified_device
        )

        assert len(unread) == 0


class TestNotificationEndpoints:
    """Tests for notification API endpoints."""

    @pytest.mark.asyncio
    async def test_get_notifications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device
    ):
        """Test getting all notifications."""
        # Create notifications
        for i in range(3):
            await NotificationService.create_notification(
                db=db_session,
                device=verified_device,
                notification_type=NotificationType.TAPS_SPOTTED,
                title=f"Alert {i}",
                message=f"Message {i}",
            )

        response = await client.get(
            "/api/v1/notifications",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["unread_count"] == 3
        assert len(data["notifications"]) == 3

    @pytest.mark.asyncio
    async def test_get_unread_notifications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device
    ):
        """Test getting only unread notifications."""
        # Create notifications
        notification = await NotificationService.create_notification(
            db=db_session,
            device=verified_device,
            notification_type=NotificationType.TAPS_SPOTTED,
            title="Alert",
            message="Message",
        )

        response = await client.get(
            "/api/v1/notifications/unread",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["unread_count"] == 1

    @pytest.mark.asyncio
    async def test_mark_notifications_read(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device
    ):
        """Test marking notifications as read."""
        # Create notification
        notification = await NotificationService.create_notification(
            db=db_session,
            device=verified_device,
            notification_type=NotificationType.TAPS_SPOTTED,
            title="Alert",
            message="Message",
        )

        response = await client.post(
            "/api/v1/notifications/read",
            headers=auth_headers,
            json={"notification_ids": [notification.id]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["marked_count"] == 1

    @pytest.mark.asyncio
    async def test_mark_all_notifications_read(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        verified_device: Device
    ):
        """Test marking all notifications as read."""
        # Create notifications
        for i in range(3):
            await NotificationService.create_notification(
                db=db_session,
                device=verified_device,
                notification_type=NotificationType.TAPS_SPOTTED,
                title=f"Alert {i}",
                message=f"Message {i}",
            )

        response = await client.post(
            "/api/v1/notifications/read/all",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["marked_count"] == 3

    @pytest.mark.asyncio
    async def test_cannot_read_other_devices_notifications(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        auth_headers: dict,
        test_device: Device
    ):
        """Test that you can't mark another device's notifications as read."""
        # Create notification for different device
        notification = await NotificationService.create_notification(
            db=db_session,
            device=test_device,  # Different device
            notification_type=NotificationType.TAPS_SPOTTED,
            title="Alert",
            message="Message",
        )

        # Try to mark it read (should not affect it)
        response = await client.post(
            "/api/v1/notifications/read",
            headers=auth_headers,  # Auth for verified_device
            json={"notification_ids": [notification.id]}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["marked_count"] == 0  # None marked
