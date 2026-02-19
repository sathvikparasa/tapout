"""
Notification service for push notifications and in-app polling.

Handles:
- APNs push notifications for iOS devices
- Creating in-app notifications for polling fallback
- Managing notification state (read/unread)
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.device import Device
from app.models.notification import Notification, NotificationType
from app.models.parking_session import ParkingSession
from app.models.parking_lot import ParkingLot

# Conditional import for APNs
try:
    from aioapns import APNs, NotificationRequest, PushType
    APNS_AVAILABLE = True
except ImportError:
    APNS_AVAILABLE = False

# Conditional import for Firebase (FCM)
try:
    import firebase_admin
    from firebase_admin import messaging as fcm_messaging
    FCM_IMPORTABLE = True
except ImportError:
    FCM_IMPORTABLE = False

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications via APNs and in-app polling.
    """

    _apns_client: Optional["APNs"] = None

    @classmethod
    def _get_apns_client(cls) -> Optional["APNs"]:
        """
        Get or create APNs client instance.

        Returns:
            APNs client if configured, None otherwise
        """
        if not APNS_AVAILABLE:
            logger.warning("aioapns not available, push notifications disabled")
            return None

        if cls._apns_client is not None:
            return cls._apns_client

        # Check if APNs is configured
        import os
        logger.warning(
            "APNs env vars at request time: APNS_KEY_ID=%r APNS_TEAM_ID=%r "
            "APNS_BUNDLE_ID=%r APNS_KEY_CONTENT_set=%s",
            os.environ.get("APNS_KEY_ID"),
            os.environ.get("APNS_TEAM_ID"),
            os.environ.get("APNS_BUNDLE_ID"),
            "APNS_KEY_CONTENT" in os.environ,
        )
        logger.warning(
            "APNs settings at request time: key_id=%r team_id=%r "
            "key_path=%r bundle_id=%r key_content_set=%s",
            settings.apns_key_id,
            settings.apns_team_id,
            settings.apns_key_path,
            settings.apns_bundle_id,
            bool(settings.apns_key_content),
        )
        if not all([
            settings.apns_key_id,
            settings.apns_team_id,
            settings.apns_key_path,
            settings.apns_bundle_id,
        ]):
            logger.warning(
                "APNs not fully configured, push notifications disabled. "
                "key_id=%s team_id=%s key_path=%s bundle_id=%s",
                bool(settings.apns_key_id),
                bool(settings.apns_team_id),
                bool(settings.apns_key_path),
                bool(settings.apns_bundle_id),
            )
            return None

        try:
            cls._apns_client = APNs(
                key=settings.apns_key_path,
                key_id=settings.apns_key_id,
                team_id=settings.apns_team_id,
                topic=settings.apns_bundle_id,
                use_sandbox=settings.apns_use_sandbox,
            )
            return cls._apns_client
        except Exception as e:
            logger.error(f"Failed to initialize APNs client: {e}")
            return None

    @staticmethod
    def _is_fcm_token(token: str) -> bool:
        """
        Detect whether a push token is an FCM token (Android) or APNs token (iOS).

        APNs tokens are 64 hex characters.
        FCM tokens are longer and contain colons/alphanumeric characters.
        """
        if len(token) > 64 or ':' in token:
            return True
        # APNs tokens are exactly 64 hex chars
        try:
            int(token, 16)
            return len(token) != 64
        except ValueError:
            return True

    @classmethod
    async def send_push_notification(
        cls,
        push_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """
        Send a push notification via FCM (Android) or APNs (iOS),
        based on the token format.

        Args:
            push_token: Device push token
            title: Notification title
            body: Notification body
            data: Optional custom data payload

        Returns:
            True if notification was sent successfully
        """
        if cls._is_fcm_token(push_token):
            return await cls._send_fcm(push_token, title, body, data)
        else:
            return await cls._send_apns(push_token, title, body, data)

    @classmethod
    async def _send_apns(
        cls,
        push_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """Send a push notification via APNs (iOS)."""
        apns_client = cls._get_apns_client()
        if apns_client is None:
            logger.debug("APNs client not available, skipping push notification")
            return False

        try:
            request = NotificationRequest(
                device_token=push_token,
                message={
                    "aps": {
                        "alert": {
                            "title": title,
                            "body": body,
                        },
                        "sound": "default",
                        "badge": 1,
                    },
                    "data": data or {},
                },
                push_type=PushType.ALERT,
            )
            response = await apns_client.send_notification(request)

            if not response.is_successful:
                logger.warning(f"APNs push notification failed: {response.description}")
                return False

            return True
        except Exception as e:
            logger.error(f"Error sending APNs push notification: {e}")
            return False

    @classmethod
    async def _send_fcm(
        cls,
        push_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """Send a push notification via Firebase Cloud Messaging (Android)."""
        if not FCM_IMPORTABLE:
            logger.warning("firebase-admin not installed, skipping FCM notification")
            return False

        # Check if Firebase app is initialized (happens at runtime in lifespan)
        try:
            firebase_admin.get_app()
        except ValueError:
            logger.warning("Firebase Admin SDK not initialized, skipping FCM notification")
            return False

        try:
            import asyncio

            # FCM data values must all be strings
            str_data = {k: str(v) for k, v in (data or {}).items()}

            message = fcm_messaging.Message(
                token=push_token,
                notification=fcm_messaging.Notification(title=title, body=body),
                data=str_data,
                android=fcm_messaging.AndroidConfig(
                    priority="high",
                    notification=fcm_messaging.AndroidNotification(
                        channel_id="taps_alerts",
                        sound="default",
                    ),
                ),
            )

            # firebase_admin.messaging.send() is synchronous — run in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, fcm_messaging.send, message)
            logger.info(f"FCM notification sent successfully: {response}")
            return True
        except fcm_messaging.UnregisteredError:
            logger.warning(f"FCM token unregistered (stale): {push_token[:20]}...")
            return False
        except Exception as e:
            logger.error(f"Error sending FCM notification: {e}")
            return False

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        device: Device,
        notification_type: NotificationType,
        title: str,
        message: str,
        parking_lot_id: Optional[int] = None
    ) -> Notification:
        """
        Create an in-app notification for polling.

        Args:
            db: Database session
            device: Target device
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            parking_lot_id: Optional related parking lot ID

        Returns:
            Created Notification instance
        """
        notification = Notification(
            device_id=device.id,
            notification_type=notification_type,
            title=title,
            message=message,
            parking_lot_id=parking_lot_id,
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @classmethod
    async def notify_parked_users(
        cls,
        db: AsyncSession,
        parking_lot_id: int,
        parking_lot_name: str,
        parking_lot_code: str = ""
    ) -> int:
        """
        Notify all users currently parked at a lot that TAPS was spotted.

        Args:
            db: Database session
            parking_lot_id: ID of the parking lot
            parking_lot_name: Name of the parking lot for notification
            parking_lot_code: Code of the parking lot

        Returns:
            Number of users notified
        """
        # Get all active parking sessions at this lot with their devices
        result = await db.execute(
            select(ParkingSession)
            .where(
                ParkingSession.parking_lot_id == parking_lot_id,
                ParkingSession.checked_out_at.is_(None)  # Active sessions
            )
            .options(selectinload(ParkingSession.device))
        )
        active_sessions = result.scalars().all()

        notified_count = 0
        title = "⚠️ TAPS Alert!"
        message = f"TAPS spotted at {parking_lot_name}! Tap to pay for parking."

        for session in active_sessions:
            device = session.device

            # Create in-app notification (always)
            await cls.create_notification(
                db=db,
                device=device,
                notification_type=NotificationType.TAPS_SPOTTED,
                title=title,
                message=message,
                parking_lot_id=parking_lot_id,
            )

            # Try to send push notification if enabled
            if device.is_push_enabled and device.push_token:
                await cls.send_push_notification(
                    push_token=device.push_token,
                    title=title,
                    body=message,
                    data={
                        "type": "TAPS_SPOTTED",
                        "parking_lot_id": parking_lot_id,
                        "parking_lot_name": parking_lot_name,
                        "parking_lot_code": parking_lot_code,
                    }
                )

            notified_count += 1

        return notified_count

    @staticmethod
    async def get_unread_notifications(
        db: AsyncSession,
        device: Device,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get unread notifications for a device.

        Args:
            db: Database session
            device: Target device
            limit: Maximum number of notifications to return

        Returns:
            List of unread Notification instances
        """
        result = await db.execute(
            select(Notification)
            .where(
                Notification.device_id == device.id,
                Notification.read_at.is_(None)
            )
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_all_notifications(
        db: AsyncSession,
        device: Device,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Notification], int, int]:
        """
        Get all notifications for a device with pagination.

        Args:
            db: Database session
            device: Target device
            limit: Maximum number of notifications
            offset: Number of notifications to skip

        Returns:
            Tuple of (notifications, unread_count, total_count)
        """
        # Get notifications
        result = await db.execute(
            select(Notification)
            .where(Notification.device_id == device.id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        notifications = list(result.scalars().all())

        # Get unread count
        from sqlalchemy import func
        unread_result = await db.execute(
            select(func.count(Notification.id))
            .where(
                Notification.device_id == device.id,
                Notification.read_at.is_(None)
            )
        )
        unread_count = unread_result.scalar() or 0

        # Get total count
        total_result = await db.execute(
            select(func.count(Notification.id))
            .where(Notification.device_id == device.id)
        )
        total_count = total_result.scalar() or 0

        return notifications, unread_count, total_count

    @staticmethod
    async def mark_notifications_read(
        db: AsyncSession,
        device: Device,
        notification_ids: List[int]
    ) -> int:
        """
        Mark notifications as read.

        Args:
            db: Database session
            device: Device making the request
            notification_ids: IDs of notifications to mark read

        Returns:
            Number of notifications marked read
        """
        result = await db.execute(
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.device_id == device.id,  # Security: only own notifications
                Notification.read_at.is_(None)
            )
            .values(read_at=datetime.now(timezone.utc))
        )
        await db.commit()
        return result.rowcount

    @classmethod
    async def send_checkout_reminder(
        cls,
        db: AsyncSession,
        session: ParkingSession,
        device: Device,
        parking_lot_name: str
    ) -> bool:
        """
        Send a checkout reminder notification.

        Args:
            db: Database session
            session: The parking session
            device: The device to notify
            parking_lot_name: Name of the parking lot

        Returns:
            True if reminder was sent
        """
        title = "🚗 Still parked?"
        message = f"You've been parked at {parking_lot_name} for 3 hours. Don't forget to check out when you leave!"

        # Create in-app notification
        await cls.create_notification(
            db=db,
            device=device,
            notification_type=NotificationType.CHECKOUT_REMINDER,
            title=title,
            message=message,
            parking_lot_id=session.parking_lot_id,
        )

        # Try push notification
        if device.is_push_enabled and device.push_token:
            await cls.send_push_notification(
                push_token=device.push_token,
                title=title,
                body=message,
                data={
                    "type": "CHECKOUT_REMINDER",
                    "parking_lot_id": session.parking_lot_id,
                    "session_id": session.id,
                }
            )

        # Mark reminder as sent
        session.reminder_sent = True
        await db.commit()

        return True
