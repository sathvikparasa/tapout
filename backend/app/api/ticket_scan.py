"""
Ticket scan API endpoint.

Accepts a ticket image, extracts date/time/location via Anthropic VLM,
and creates a TapsSighting if the location maps to a known parking lot.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.device import Device
from app.models.taps_sighting import TapsSighting
from app.schemas.ticket_scan import TicketScanResponse
from app.services.auth import require_verified_device
from app.services.notification import NotificationService
from app.services.ticket_ocr import TicketOCRService
from app.api.auth import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ticket-scan", tags=["Ticket Scan"])

FEED_WINDOW_HOURS = 3
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}

# Pacific timezone (UTC-8 / UTC-7 DST)
try:
    from zoneinfo import ZoneInfo
    PACIFIC = ZoneInfo("America/Los_Angeles")
except ImportError:
    from datetime import tzinfo
    # Fallback: fixed UTC-8 (no DST handling)
    PACIFIC = timezone(timedelta(hours=-8))


@router.post(
    "",
    response_model=TicketScanResponse,
    summary="Scan a parking ticket",
    description="Upload a ticket image to extract date/time/location and create a sighting.",
)
@limiter.limit("10/hour")
async def scan_ticket(
    request: Request,
    image: UploadFile = File(...),
    device: Device = Depends(require_verified_device),
    db: AsyncSession = Depends(get_db),
):
    # Validate content type
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be JPEG or PNG",
        )

    # Read and validate size
    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be under 10 MB",
        )

    # Extract ticket data via VLM
    try:
        ticket_data = TicketOCRService.extract_ticket_data(image_bytes, image.content_type)
    except ValueError as e:
        logger.warning(f"Ticket OCR failed: {e}")
        return TicketScanResponse(success=True, is_recent=False)
    except Exception as e:
        logger.error(f"Ticket OCR error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process ticket image",
        )

    # If VLM returned an error (e.g. not a ticket)
    if "error" in ticket_data:
        return TicketScanResponse(success=True, is_recent=False)

    ticket_date = ticket_data.get("date")
    ticket_time = ticket_data.get("time")
    ticket_location = ticket_data.get("location")

    # If we don't have a location, can't map to a lot
    if not ticket_location:
        return TicketScanResponse(
            success=True,
            ticket_date=ticket_date,
            ticket_time=ticket_time,
            ticket_location=ticket_location,
            is_recent=False,
        )

    # Map location to a parking lot
    lot = await TicketOCRService.map_location_to_lot(db, ticket_location)

    if lot is None:
        return TicketScanResponse(
            success=True,
            ticket_date=ticket_date,
            ticket_time=ticket_time,
            ticket_location=ticket_location,
            is_recent=False,
        )

    # Parse ticket datetime in Pacific timezone
    ticket_utc = None
    is_recent = False
    if ticket_date and ticket_time:
        try:
            naive_dt = datetime.strptime(f"{ticket_date} {ticket_time}", "%m/%d/%Y %H:%M")
            pacific_dt = naive_dt.replace(tzinfo=PACIFIC)
            ticket_utc = pacific_dt.astimezone(timezone.utc)
            is_recent = (datetime.now(timezone.utc) - ticket_utc) < timedelta(hours=FEED_WINDOW_HOURS)
        except (ValueError, OverflowError):
            # Bad date/time format — still create sighting with current time
            ticket_utc = datetime.now(timezone.utc)

    if ticket_utc is None:
        ticket_utc = datetime.now(timezone.utc)

    # Create sighting
    sighting = TapsSighting(
        parking_lot_id=lot.id,
        reported_by_device_id=device.id,
        reported_at=ticket_utc,
        notes=f"Ticket scan: {ticket_location}",
    )
    db.add(sighting)
    await db.commit()
    await db.refresh(sighting)

    # Notify if recent
    users_notified = 0
    if is_recent:
        users_notified = await NotificationService.notify_parked_users(
            db=db,
            parking_lot_id=lot.id,
            parking_lot_name=lot.name,
            parking_lot_code=lot.code,
        )

    return TicketScanResponse(
        success=True,
        ticket_date=ticket_date,
        ticket_time=ticket_time,
        ticket_location=ticket_location,
        mapped_lot_id=lot.id,
        mapped_lot_name=lot.name,
        mapped_lot_code=lot.code,
        is_recent=is_recent,
        sighting_id=sighting.id,
        users_notified=users_notified,
    )
