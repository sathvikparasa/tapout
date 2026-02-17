"""
Tests for the reminder service (checkout reminders).

ReminderService.process_pending_reminders finds sessions where:
  - checked_out_at IS NULL (still active)
  - checked_in_at <= now - 3 hours
  - reminder_sent = False
and sends a checkout reminder for each.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.parking_lot import ParkingLot
from app.models.parking_session import ParkingSession
from app.services.notification import NotificationService
from app.services.reminder import ReminderService, run_reminder_job


# ---------------------------------------------------------------------------
# Helper to create sessions at specific check-in times
# ---------------------------------------------------------------------------

async def _create_session(
    db: AsyncSession,
    device: Device,
    lot: ParkingLot,
    hours_ago: float,
    reminder_sent: bool = False,
    checked_out: bool = False,
) -> ParkingSession:
    """Create a ParkingSession checked in `hours_ago` hours before now."""
    session = ParkingSession(
        device_id=device.id,
        parking_lot_id=lot.id,
        checked_in_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
        reminder_sent=reminder_sent,
    )
    if checked_out:
        session.checked_out_at = datetime.now(timezone.utc) - timedelta(hours=hours_ago / 2)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


# ---------------------------------------------------------------------------
# process_pending_reminders
# ---------------------------------------------------------------------------

class TestProcessPendingReminders:
    """Tests for finding and sending checkout reminders."""

    @pytest.mark.asyncio
    async def test_no_pending_reminders(
        self, db_session: AsyncSession
    ):
        """No sessions at all → returns 0."""
        with patch.object(
            NotificationService, "send_checkout_reminder",
            new_callable=AsyncMock, return_value=True,
        ) as mock_remind:
            count = await ReminderService.process_pending_reminders(db_session)

            assert count == 0
            mock_remind.assert_not_called()

    @pytest.mark.asyncio
    async def test_session_under_3_hours(
        self, db_session: AsyncSession, verified_device: Device, test_parking_lot: ParkingLot
    ):
        """Session checked in 2h ago → not yet due, returns 0."""
        await _create_session(db_session, verified_device, test_parking_lot, hours_ago=2.0)

        with patch.object(
            NotificationService, "send_checkout_reminder",
            new_callable=AsyncMock, return_value=True,
        ) as mock_remind:
            count = await ReminderService.process_pending_reminders(db_session)

            assert count == 0
            mock_remind.assert_not_called()

    @pytest.mark.asyncio
    async def test_session_over_3_hours(
        self, db_session: AsyncSession, verified_device: Device, test_parking_lot: ParkingLot
    ):
        """Session checked in 4h ago, reminder not sent → sends reminder, returns 1."""
        session = await _create_session(
            db_session, verified_device, test_parking_lot, hours_ago=4.0
        )

        with patch.object(
            NotificationService, "send_checkout_reminder",
            new_callable=AsyncMock, return_value=True,
        ) as mock_remind:
            count = await ReminderService.process_pending_reminders(db_session)

            assert count == 1
            mock_remind.assert_called_once()
            # Verify correct session and device were passed
            call_kwargs = mock_remind.call_args.kwargs
            assert call_kwargs["session"].id == session.id
            assert call_kwargs["device"].id == verified_device.id
            assert call_kwargs["parking_lot_name"] == test_parking_lot.name

    @pytest.mark.asyncio
    async def test_session_already_reminded(
        self, db_session: AsyncSession, verified_device: Device, test_parking_lot: ParkingLot
    ):
        """Session 4h ago but reminder_sent=True → skips, returns 0."""
        await _create_session(
            db_session, verified_device, test_parking_lot,
            hours_ago=4.0, reminder_sent=True,
        )

        with patch.object(
            NotificationService, "send_checkout_reminder",
            new_callable=AsyncMock, return_value=True,
        ) as mock_remind:
            count = await ReminderService.process_pending_reminders(db_session)

            assert count == 0
            mock_remind.assert_not_called()

    @pytest.mark.asyncio
    async def test_session_already_checked_out(
        self, db_session: AsyncSession, verified_device: Device, test_parking_lot: ParkingLot
    ):
        """Checked-out session → skipped even if old."""
        await _create_session(
            db_session, verified_device, test_parking_lot,
            hours_ago=5.0, checked_out=True,
        )

        with patch.object(
            NotificationService, "send_checkout_reminder",
            new_callable=AsyncMock, return_value=True,
        ) as mock_remind:
            count = await ReminderService.process_pending_reminders(db_session)

            assert count == 0
            mock_remind.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_sessions_due(
        self, db_session: AsyncSession, test_parking_lot: ParkingLot
    ):
        """3 sessions all due → sends 3 reminders, returns 3."""
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

            await _create_session(db_session, device, test_parking_lot, hours_ago=4.0)

        with patch.object(
            NotificationService, "send_checkout_reminder",
            new_callable=AsyncMock, return_value=True,
        ) as mock_remind:
            count = await ReminderService.process_pending_reminders(db_session)

            assert count == 3
            assert mock_remind.call_count == 3

    @pytest.mark.asyncio
    async def test_mixed_sessions(
        self, db_session: AsyncSession, test_parking_lot: ParkingLot
    ):
        """1 due + 1 not due + 1 already reminded → returns 1."""
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

        # Due: 4h ago, not reminded
        await _create_session(db_session, devices[0], test_parking_lot, hours_ago=4.0)
        # Not due: 1h ago
        await _create_session(db_session, devices[1], test_parking_lot, hours_ago=1.0)
        # Already reminded: 5h ago, reminder_sent=True
        await _create_session(
            db_session, devices[2], test_parking_lot,
            hours_ago=5.0, reminder_sent=True,
        )

        with patch.object(
            NotificationService, "send_checkout_reminder",
            new_callable=AsyncMock, return_value=True,
        ) as mock_remind:
            count = await ReminderService.process_pending_reminders(db_session)

            assert count == 1
            assert mock_remind.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_send_failure_gracefully(
        self, db_session: AsyncSession, verified_device: Device, test_parking_lot: ParkingLot
    ):
        """If send_checkout_reminder raises, it's caught and doesn't crash."""
        await _create_session(
            db_session, verified_device, test_parking_lot, hours_ago=4.0
        )

        with patch.object(
            NotificationService, "send_checkout_reminder",
            new_callable=AsyncMock, side_effect=Exception("DB error"),
        ):
            # Should not raise
            count = await ReminderService.process_pending_reminders(db_session)

            # The failed reminder is not counted
            assert count == 0


# ---------------------------------------------------------------------------
# run_reminder_job
# ---------------------------------------------------------------------------

class TestRunReminderJob:
    """Tests for the scheduler wrapper function."""

    @pytest.mark.asyncio
    async def test_calls_process_pending_reminders(self, db_session: AsyncSession):
        """run_reminder_job delegates to ReminderService.process_pending_reminders."""
        with patch.object(
            ReminderService, "process_pending_reminders",
            new_callable=AsyncMock, return_value=5,
        ) as mock_process:
            await run_reminder_job(db_session)

            mock_process.assert_called_once_with(db_session)

    @pytest.mark.asyncio
    async def test_handles_errors(self, db_session: AsyncSession):
        """run_reminder_job catches exceptions (doesn't crash the scheduler)."""
        with patch.object(
            ReminderService, "process_pending_reminders",
            new_callable=AsyncMock, side_effect=Exception("unexpected"),
        ):
            # Should not raise
            await run_reminder_job(db_session)
