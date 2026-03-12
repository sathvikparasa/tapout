"""
TAPS sightings API endpoints.
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, request, jsonify, abort
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.database import AsyncSessionLocal
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


def _insert_fn(db):
    try:
        dialect = db.get_bind().dialect.name
    except Exception:
        dialect = "postgresql"
    return sqlite_insert if dialect == "sqlite" else pg_insert


@bp.route("", methods=["POST"])
async def report_sighting():
    data = request.get_json(force=True, silent=True) or {}
    try:
        sighting_data = TapsSightingCreate(**data)
    except Exception as e:
        abort(422, description=str(e))

    async with AsyncSessionLocal() as db:
        device = await require_verified_device(db)

        result = await db.execute(select(ParkingLot).where(ParkingLot.id == sighting_data.parking_lot_id))
        lot = result.scalar_one_or_none()
        if lot is None:
            abort(404, description=f"Parking lot {sighting_data.parking_lot_id} not found")

        try:
            await db.execute(text("SELECT pg_advisory_xact_lock(:lot_id)"), {"lot_id": lot.id})
        except Exception:
            pass

        rate_limit_cutoff = datetime.now(timezone.utc) - timedelta(minutes=RATE_LIMIT_MINUTES)
        recent_result = await db.execute(
            select(TapsSighting)
            .where(TapsSighting.parking_lot_id == lot.id, TapsSighting.reported_at >= rate_limit_cutoff)
            .order_by(TapsSighting.reported_at.desc())
            .limit(1)
        )
        recent_sighting = recent_result.scalar_one_or_none()

        if recent_sighting is not None:
            stmt = (
                _insert_fn(db)(Vote)
                .values(device_id=device.id, sighting_id=recent_sighting.id, vote_type=VoteTypeModel.UPVOTE)
                .on_conflict_do_update(
                    index_elements=["device_id", "sighting_id"],
                    set_={"vote_type": VoteTypeModel.UPVOTE},
                )
            )
            await db.execute(stmt)
            await db.commit()
            await cache_delete(f"vote_counts:{recent_sighting.id}")

            payload = TapsSightingWithNotifications(
                id=recent_sighting.id,
                parking_lot_id=lot.id, parking_lot_name=lot.name, parking_lot_code=lot.code,
                reported_at=recent_sighting.reported_at, notes=recent_sighting.notes,
                users_notified=0, was_rate_limited=True,
            )
            return jsonify(payload.model_dump(mode="json")), 200

        sighting = TapsSighting(
            parking_lot_id=lot.id,
            reported_by_device_id=device.id,
            notes=sighting_data.notes,
        )
        db.add(sighting)
        await db.commit()
        await db.refresh(sighting)

        await cache_delete(f"lot_stats:{lot.id}", f"prediction:{lot.id}", "prediction:global")

        lot_id = lot.id
        lot_name = lot.name
        lot_code = lot.code

        if not _is_weekend():
            async def _notify():
                async with AsyncSessionLocal() as bg_db:
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

    async with AsyncSessionLocal() as db:
        await require_verified_device(db)

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = select(TapsSighting).where(TapsSighting.reported_at >= cutoff)
        if lot_id is not None:
            query = query.where(TapsSighting.parking_lot_id == lot_id)
        query = query.order_by(TapsSighting.reported_at.desc()).limit(limit)

        result = await db.execute(query)
        sightings = result.scalars().all()

        lot_ids = {s.parking_lot_id for s in sightings}
        if lot_ids:
            lots_result = await db.execute(select(ParkingLot).where(ParkingLot.id.in_(lot_ids)))
            lots = {lot.id: lot for lot in lots_result.scalars().all()}
        else:
            lots = {}

        return jsonify([
            TapsSightingResponse.from_sighting(s, lots[s.parking_lot_id].name, lots[s.parking_lot_id].code).model_dump(mode="json")
            for s in sightings
        ])


@bp.route("/latest/<int:lot_id>", methods=["GET"])
async def get_latest_sighting(lot_id: int):
    async with AsyncSessionLocal() as db:
        await require_verified_device(db)

        lot_result = await db.execute(select(ParkingLot).where(ParkingLot.id == lot_id))
        lot = lot_result.scalar_one_or_none()
        if lot is None:
            abort(404, description=f"Parking lot {lot_id} not found")

        result = await db.execute(
            select(TapsSighting).where(TapsSighting.parking_lot_id == lot_id)
            .order_by(TapsSighting.reported_at.desc()).limit(1)
        )
        sighting = result.scalar_one_or_none()
        if sighting is None:
            abort(404, description=f"No sightings found at {lot.name}")

        return jsonify(TapsSightingResponse.from_sighting(sighting, lot.name, lot.code).model_dump(mode="json"))
