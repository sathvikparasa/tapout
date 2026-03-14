"""
TAPS sightings API endpoints.
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, request, jsonify, abort

from app.firestore_db import get_db
from app.schemas.taps_sighting import TapsSightingCreate, TapsSightingResponse, TapsSightingWithNotifications
from app.models.taps_sighting import TapsSighting
from app.models.parking_lot import ParkingLot
from app.models.vote import Vote, VoteType as VoteTypeModel
from app.services.auth import require_verified_device
from app.services.notification import NotificationService
from app.services.cache import cache_delete

logger = logging.getLogger(__name__)
bp = Blueprint("sightings", __name__)

RATE_LIMIT_MINUTES = 10
_PACIFIC = ZoneInfo("America/Los_Angeles")


def _is_weekend() -> bool:
    return datetime.now(_PACIFIC).weekday() >= 5


def _run_background(coro):
    """Run an async coroutine in a background thread."""
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()
    threading.Thread(target=_run, daemon=True).start()


@bp.route("", methods=["POST"])
async def report_sighting():
    data = request.get_json(force=True, silent=True) or {}
    try:
        sighting_data = TapsSightingCreate(**data)
    except Exception as e:
        abort(422, description=str(e))

    db = get_db()
    device = await require_verified_device(db)

    lot_doc = await db.collection("parking_lots").document(str(sighting_data.parking_lot_id)).get()
    if not lot_doc.exists:
        abort(404, description=f"Parking lot {sighting_data.parking_lot_id} not found")
    lot = ParkingLot.from_dict(lot_doc.to_dict(), doc_id=lot_doc.id)

    # Rate limit check: find recent sighting at this lot within last 10 minutes
    rate_limit_cutoff = datetime.now(timezone.utc) - timedelta(minutes=RATE_LIMIT_MINUTES)
    recent_stream = db.collection("taps_sightings")\
        .where("parking_lot_id", "==", lot.id)\
        .where("reported_at", ">=", rate_limit_cutoff)\
        .stream()

    recent_sighting = None
    async for doc in recent_stream:
        s = TapsSighting.from_dict(doc.to_dict(), doc_id=doc.id)
        if recent_sighting is None or s.reported_at > recent_sighting.reported_at:
            recent_sighting = s

    if recent_sighting is not None:
        # Upsert vote using composite doc ID for uniqueness
        vote_doc_id = f"{device.device_id}_{recent_sighting.id}"
        vote_ref = db.collection("votes").document(vote_doc_id)
        now = datetime.now(timezone.utc)
        vote_data = {
            "id": vote_doc_id,
            "device_id": device.device_id,
            "sighting_id": recent_sighting.id,
            "vote_type": VoteTypeModel.UPVOTE.value,
            "updated_at": now,
        }
        existing_vote_doc = await vote_ref.get()
        if not existing_vote_doc.exists:
            vote_data["created_at"] = now
        await vote_ref.set(vote_data, merge=True)
        await cache_delete(f"vote_counts:{recent_sighting.id}")

        payload = TapsSightingWithNotifications(
            id=recent_sighting.id,
            parking_lot_id=lot.id, parking_lot_name=lot.name, parking_lot_code=lot.code,
            reported_at=recent_sighting.reported_at, notes=recent_sighting.notes,
            users_notified=0, was_rate_limited=True,
        )
        return jsonify(payload.model_dump(mode="json")), 200

    # Create new sighting
    now = datetime.now(timezone.utc)
    ref = db.collection("taps_sightings").document()
    sighting = TapsSighting(
        id=ref.id,
        parking_lot_id=lot.id,
        parking_lot_name=lot.name,
        parking_lot_code=lot.code,
        reported_at=now,
        reported_by_device_id=device.device_id,
        notes=sighting_data.notes,
    )
    await ref.set(sighting.to_dict())

    await cache_delete(f"lot_stats:{lot.id}", f"prediction:{lot.id}", "prediction:global")

    lot_id = lot.id
    lot_name = lot.name
    lot_code = lot.code

    if not _is_weekend():
        async def _notify():
            from app.firestore_db import get_db as _get_db
            bg_db = _get_db()
            await NotificationService.notify_parked_users(
                db=bg_db,
                parking_lot_id=lot_id,
                parking_lot_name=lot_name,
                parking_lot_code=lot_code,
            )
        _run_background(_notify())

    return jsonify(TapsSightingWithNotifications(
        id=sighting.id,
        parking_lot_id=lot.id, parking_lot_name=lot.name, parking_lot_code=lot.code,
        reported_at=sighting.reported_at, notes=sighting.notes,
        users_notified=0,
    ).model_dump(mode="json")), 201


@bp.route("", methods=["GET"])
async def list_sightings():
    hours = request.args.get("hours", 24, type=int)
    lot_id = request.args.get("lot_id", type=int)
    limit = request.args.get("limit", 50, type=int)

    db = get_db()
    await require_verified_device(db)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = db.collection("taps_sightings").where("reported_at", ">=", cutoff)
    if lot_id is not None:
        query = query.where("parking_lot_id", "==", lot_id)

    sightings = []
    async for doc in query.stream():
        sightings.append(TapsSighting.from_dict(doc.to_dict(), doc_id=doc.id))

    # Sort by reported_at descending and apply limit
    sightings.sort(key=lambda s: s.reported_at, reverse=True)
    sightings = sightings[:limit]

    return jsonify([
        TapsSightingResponse.from_sighting(s, s.parking_lot_name, s.parking_lot_code).model_dump(mode="json")
        for s in sightings
    ])


@bp.route("/latest/<int:lot_id>", methods=["GET"])
async def get_latest_sighting(lot_id: int):
    db = get_db()
    await require_verified_device(db)

    lot_doc = await db.collection("parking_lots").document(str(lot_id)).get()
    if not lot_doc.exists:
        abort(404, description=f"Parking lot {lot_id} not found")
    lot = ParkingLot.from_dict(lot_doc.to_dict(), doc_id=lot_doc.id)

    sightings_stream = db.collection("taps_sightings")\
        .where("parking_lot_id", "==", lot_id)\
        .stream()
    sightings = []
    async for doc in sightings_stream:
        sightings.append(TapsSighting.from_dict(doc.to_dict(), doc_id=doc.id))

    if not sightings:
        abort(404, description=f"No sightings found at {lot.name}")

    sightings.sort(key=lambda s: s.reported_at, reverse=True)
    sighting = sightings[0]

    return jsonify(TapsSightingResponse.from_sighting(sighting, lot.name, lot.code).model_dump(mode="json"))
