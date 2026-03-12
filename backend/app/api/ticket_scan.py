"""
Ticket scan API endpoint.

Accepts a ticket image, extracts date/time/location via Anthropic VLM,
and creates a TapsSighting if the location maps to a known parking lot.
"""

import logging
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, abort

from app.database import AsyncSessionLocal
from app.models.taps_sighting import TapsSighting
from app.schemas.ticket_scan import TicketScanResponse
from app.services.auth import require_verified_device
from app.services.notification import NotificationService
from app.services.ticket_ocr import TicketOCRService, ImageTooLargeError, CorruptImageError
from app.api.auth import limiter

logger = logging.getLogger(__name__)

bp = Blueprint("ticket_scan", __name__)

FEED_WINDOW_HOURS = 3
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}

# Pacific timezone (UTC-8 / UTC-7 DST)
try:
    from zoneinfo import ZoneInfo
    PACIFIC = ZoneInfo("America/Los_Angeles")
except ImportError:
    PACIFIC = timezone(timedelta(hours=-8))


@bp.route("", methods=["POST"])
@limiter.limit("10/hour")
async def scan_ticket():
    image = request.files.get("image")
    if image is None:
        abort(400, description="No image file provided")

    # Validate content type
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        abort(400, description="Image must be JPEG or PNG")

    # Read and validate size
    image_bytes = image.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        return jsonify(TicketScanResponse(
            success=False,
            error_code="image_too_large",
            error_message="Your photo is too large. Please use a smaller image (under 10 MB).",
            is_recent=False,
        ).model_dump(mode="json"))

    async with AsyncSessionLocal() as db:
        device = await require_verified_device(db)

        # Extract ticket data via VLM
        try:
            ticket_data = TicketOCRService.extract_ticket_data(image_bytes, image.content_type)
        except ImageTooLargeError:
            logger.warning("Ticket image could not be compressed to fit API limits")
            return jsonify(TicketScanResponse(
                success=False,
                error_code="image_too_large",
                error_message="Your photo is too large to process. Please try a lower-resolution image.",
                is_recent=False,
            ).model_dump(mode="json"))
        except CorruptImageError:
            logger.warning("Ticket image could not be opened — likely corrupt or unsupported format")
            return jsonify(TicketScanResponse(
                success=False,
                error_code="invalid_image",
                error_message="We couldn't read your photo. Make sure it's a valid JPEG or PNG.",
                is_recent=False,
            ).model_dump(mode="json"))
        except ValueError as e:
            logger.warning(f"Ticket OCR validation failed: {e}")
            return jsonify(TicketScanResponse(
                success=False,
                error_code="ocr_failed",
                error_message="We had trouble reading the ticket. Please make sure the photo is clear and well-lit.",
                is_recent=False,
            ).model_dump(mode="json"))
        except Exception as e:
            logger.error(f"Ticket OCR error: {e}")
            return jsonify(TicketScanResponse(
                success=False,
                error_code="ocr_failed",
                error_message="Something went wrong while processing your ticket. Please try again.",
                is_recent=False,
            ).model_dump(mode="json"))

        # If VLM returned an error (e.g. not a ticket)
        if "error" in ticket_data:
            error_type = ticket_data["error"]
            if error_type == "not_a_ticket":
                return jsonify(TicketScanResponse(
                    success=False,
                    error_code="not_a_ticket",
                    error_message="This doesn't look like a UC Davis parking ticket. Please scan a valid TAPS parking notice.",
                    is_recent=False,
                ).model_dump(mode="json"))
            return jsonify(TicketScanResponse(
                success=False,
                error_code="ocr_failed",
                error_message="We couldn't extract ticket details. Please make sure the photo is clear and shows a UC Davis parking ticket.",
                is_recent=False,
            ).model_dump(mode="json"))

        ticket_date = ticket_data.get("date")
        ticket_time = ticket_data.get("time")
        ticket_location = ticket_data.get("location")

        # If all fields are null, the ticket was unreadable
        if not any([ticket_date, ticket_time, ticket_location]):
            return jsonify(TicketScanResponse(
                success=False,
                error_code="fields_unreadable",
                error_message="We detected a ticket but couldn't read the details. Try retaking the photo in better lighting.",
                is_recent=False,
            ).model_dump(mode="json"))

        # If we don't have a location, can't map to a lot
        if not ticket_location:
            return jsonify(TicketScanResponse(
                success=True,
                ticket_date=ticket_date,
                ticket_time=ticket_time,
                ticket_location=ticket_location,
                is_recent=False,
            ).model_dump(mode="json"))

        # Map location to a parking lot
        lot = await TicketOCRService.map_location_to_lot(db, ticket_location)

        if lot is None:
            return jsonify(TicketScanResponse(
                success=True,
                ticket_date=ticket_date,
                ticket_time=ticket_time,
                ticket_location=ticket_location,
                is_recent=False,
            ).model_dump(mode="json"))

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

        return jsonify(TicketScanResponse(
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
        ).model_dump(mode="json"))
