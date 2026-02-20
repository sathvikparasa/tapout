"""
Reminder service for sending checkout reminders.

Handles the background task that checks for users who have been
parked for more than 3 hours and sends them a reminder to check out.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.parking_session import ParkingSession
from app.models.parking_lot import ParkingLot
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


class ReminderService:
    """
    Service for managing checkout reminders.
    """

    @staticmethod
    async def process_pending_reminders(db: AsyncSession) -> int:
        """
        Find sessions that need reminders and send them.

        Criteria:
        - Session is active (not checked out)
        - Session started more than 3 hours ago
        - Reminder has not been sent yet

        Args:
            db: Database session

        Returns:
            Number of reminders sent
        """
        # Calculate the cutoff time (3 hours ago)
        reminder_hours = settings.parking_reminder_hours
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=reminder_hours)

        # Find sessions that need reminders
        result = await db.execute(
            select(ParkingSession)
            .where(
                ParkingSession.checked_out_at.is_(None),  # Still active
                ParkingSession.checked_in_at <= cutoff_time,  # Parked for 3+ hours
                ParkingSession.reminder_sent == False,  # Reminder not yet sent
            )
            .options(
                selectinload(ParkingSession.device),
                selectinload(ParkingSession.parking_lot),
            )
        )
        sessions = result.scalars().all()

        reminders_sent = 0

        for session in sessions:
            try:
                await NotificationService.send_checkout_reminder(
                    db=db,
                    session=session,
                    device=session.device,
                    parking_lot_name=session.parking_lot.name,
                )
                reminders_sent += 1
                logger.info(
                    f"Sent checkout reminder for session {session.id} "
                    f"at {session.parking_lot.name}"
                )
            except Exception as e:
                logger.error(f"Failed to send reminder for session {session.id}: {e}")

        return reminders_sent

    @staticmethod
    async def auto_checkout_expired_sessions(db: AsyncSession) -> int:
        """
        Auto-checkout all sessions that are still active.

        Called nightly at 10 PM PT to close sessions where users forgot to
        check out, preventing stale counts in active_parkers.

        Args:
            db: Database session

        Returns:
            Number of sessions closed
        """
        result = await db.execute(
            update(ParkingSession)
            .where(ParkingSession.checked_out_at.is_(None))
            .values(checked_out_at=datetime.now(timezone.utc))
        )
        await db.commit()
        closed = result.rowcount
        logger.info(f"Auto-checkout closed {closed} expired session(s)")
        return closed


async def run_reminder_job(db: AsyncSession):
    """
    Job function to be called by the scheduler.

    Args:
        db: Database session
    """
    logger.info("Running checkout reminder job")
    try:
        count = await ReminderService.process_pending_reminders(db)
        logger.info(f"Checkout reminder job completed: {count} reminders sent")
    except Exception as e:
        logger.error(f"Checkout reminder job failed: {e}")
