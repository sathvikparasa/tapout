"""
Reminder service for sending checkout reminders.

Handles the background task that checks for users who have been
parked for more than 3 hours and sends them a reminder to check out.
"""

import logging
from datetime import datetime, timedelta, timezone

from google.cloud.firestore_v1 import AsyncClient

from app.config import settings
from app.models.parking_session import ParkingSession
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


class ReminderService:
    """
    Service for managing checkout reminders.
    """

    @staticmethod
    async def process_pending_reminders(db: AsyncClient) -> int:
        """
        Find sessions that need reminders and send them.

        Criteria:
        - Session is active (is_active == True)
        - Session started more than 3 hours ago
        - Reminder has not been sent yet

        Args:
            db: Firestore async client

        Returns:
            Number of reminders sent
        """
        reminder_hours = settings.parking_reminder_hours
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=reminder_hours)

        # Find sessions that need reminders
        sessions_stream = db.collection("parking_sessions")\
            .where("is_active", "==", True)\
            .where("checked_in_at", "<=", cutoff_time)\
            .where("reminder_sent", "==", False)\
            .stream()

        sessions = []
        async for doc in sessions_stream:
            sessions.append(ParkingSession.from_dict(doc.to_dict(), doc_id=doc.id))

        reminders_sent = 0

        for session in sessions:
            try:
                reminders_sent += 1
                logger.info(
                    f"Sent checkout reminder for session {session.id} "
                    f"at {session.parking_lot_name}"
                )
            except Exception as e:
                logger.error(f"Failed to send reminder for session {session.id}: {e}")

        return reminders_sent

    @staticmethod
    async def auto_checkout_expired_sessions(db: AsyncClient) -> int:
        """
        Auto-checkout all sessions that are still active.

        Called nightly at 10 PM PT to close sessions where users forgot to
        check out, preventing stale counts in active_parkers.

        Args:
            db: Firestore async client

        Returns:
            Number of sessions closed
        """
        sessions_stream = db.collection("parking_sessions").where("is_active", "==", True).stream()
        batch = db.batch()
        now = datetime.now(timezone.utc)
        count = 0
        async for doc in sessions_stream:
            batch.update(doc.reference, {"checked_out_at": now, "is_active": False})
            count += 1
        if count > 0:
            await batch.commit()
        logger.info(f"Auto-checkout closed {count} expired session(s)")
        return count


async def run_reminder_job(db: AsyncClient):
    """
    Job function to be called by the scheduler.

    Args:
        db: Firestore async client
    """
    logger.info("Running checkout reminder job")
    try:
        count = await ReminderService.process_pending_reminders(db)
        logger.info(f"Checkout reminder job completed: {count} reminders sent")
    except Exception as e:
        logger.error(f"Checkout reminder job failed: {e}")
