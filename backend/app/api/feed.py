"""
Feed API endpoints.

Provides recent TAPS sightings feed with voting information,
grouped by parking lot location.
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, abort
from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.database import AsyncSessionLocal
from app.schemas.feed import FeedSighting, FeedResponse, AllFeedsResponse
from app.schemas.vote import VoteType, VoteCreate, VoteResponse, VoteResult
from app.models.taps_sighting import TapsSighting
from app.models.parking_lot import ParkingLot
from app.models.vote import Vote, VoteType as VoteTypeModel
from app.models.device import Device
from app.services.auth import get_current_device, require_verified_device
from app.services.cache import cache_get, cache_set, cache_delete, TTL_VOTE_COUNTS

bp = Blueprint("feed", __name__)

# Feed window in hours (shows sightings from last 3 hours)
FEED_WINDOW_HOURS = 3


def _insert_fn(db):
    """Return dialect-appropriate insert (PostgreSQL in prod, SQLite in tests)."""
    try:
        dialect = db.get_bind().dialect.name
    except Exception:
        dialect = "postgresql"
    return sqlite_insert if dialect == "sqlite" else pg_insert


async def _batch_build_feed_sightings(
    db,
    sightings: list,
    device: Device,
    lot_by_id: dict,
) -> list:
    """
    Build FeedSighting objects for a list of sightings using at most 2 DB
    queries (batch vote counts + batch user votes) regardless of list length.

    Vote counts are cached per sighting with a 30-second TTL and invalidated
    whenever a vote is cast or removed.
    """
    if not sightings:
        return []

    sighting_ids = [s.id for s in sightings]
    now = datetime.now(timezone.utc)

    # ── 1. Vote counts — try cache first, batch-fetch misses ────────────────
    vote_data: dict = {}
    cache_misses: list = []

    for sid in sighting_ids:
        cached = await cache_get(f"vote_counts:{sid}")
        if cached is not None:
            vote_data[sid] = cached
        else:
            cache_misses.append(sid)
            vote_data[sid] = {"up": 0, "down": 0}

    if cache_misses:
        rows = await db.execute(
            select(Vote.sighting_id, Vote.vote_type, func.count().label("n"))
            .where(Vote.sighting_id.in_(cache_misses))
            .group_by(Vote.sighting_id, Vote.vote_type)
        )
        for row in rows:
            if row.vote_type == VoteTypeModel.UPVOTE:
                vote_data[row.sighting_id]["up"] = row.n
            else:
                vote_data[row.sighting_id]["down"] = row.n

        # Store freshly loaded counts in cache
        for sid in cache_misses:
            await cache_set(f"vote_counts:{sid}", vote_data[sid], TTL_VOTE_COUNTS)

    # ── 2. User's own votes — always live (personal, low cost) ─────────────
    user_vote_rows = await db.execute(
        select(Vote.sighting_id, Vote.vote_type)
        .where(Vote.sighting_id.in_(sighting_ids), Vote.device_id == device.id)
    )
    user_votes: dict = {r.sighting_id: r.vote_type for r in user_vote_rows}

    # ── 3. Assemble ─────────────────────────────────────────────────────────
    result = []
    for sighting in sightings:
        lot = lot_by_id[sighting.parking_lot_id]
        counts = vote_data[sighting.id]
        user_vote_raw = user_votes.get(sighting.id)
        user_vote = VoteType(user_vote_raw.value) if user_vote_raw else None

        reported_at = sighting.reported_at
        if reported_at.tzinfo is None:
            reported_at = reported_at.replace(tzinfo=timezone.utc)
        minutes_ago = int((now - reported_at).total_seconds() / 60)

        result.append(FeedSighting(
            id=sighting.id,
            parking_lot_id=sighting.parking_lot_id,
            parking_lot_name=lot.name,
            parking_lot_code=lot.code,
            reported_at=sighting.reported_at,
            notes=sighting.notes,
            upvotes=counts["up"],
            downvotes=counts["down"],
            net_score=counts["up"] - counts["down"],
            user_vote=user_vote,
            minutes_ago=minutes_ago,
        ))

    return result


@bp.route("", methods=["GET"])
async def get_all_feeds():
    async with AsyncSessionLocal() as db:
        device = await get_current_device(db)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=FEED_WINDOW_HOURS)

        # 1 query: all active lots
        lots_result = await db.execute(
            select(ParkingLot).where(ParkingLot.is_active == True).order_by(ParkingLot.name)
        )
        lots = lots_result.scalars().all()
        lot_by_id = {lot.id: lot for lot in lots}

        # 1 query: all recent sightings across every lot
        sightings_result = await db.execute(
            select(TapsSighting)
            .where(
                TapsSighting.parking_lot_id.in_(lot_by_id.keys()),
                TapsSighting.reported_at >= cutoff,
            )
            .order_by(TapsSighting.reported_at.desc())
        )
        all_sightings = sightings_result.scalars().all()

        # Batch build with at most 2 more DB queries total
        feed_sightings_all = await _batch_build_feed_sightings(
            db, all_sightings, device, lot_by_id
        )

        # Re-group built sightings by lot for response
        built_by_lot: dict = {lot.id: [] for lot in lots}
        for fs in feed_sightings_all:
            built_by_lot[fs.parking_lot_id].append(fs)

        feeds = [
            FeedResponse(
                parking_lot_id=lot.id,
                parking_lot_name=lot.name,
                parking_lot_code=lot.code,
                sightings=built_by_lot[lot.id],
                total_sightings=len(built_by_lot[lot.id]),
            )
            for lot in lots
        ]

        return jsonify(AllFeedsResponse(
            feeds=feeds,
            total_sightings=len(all_sightings),
        ).model_dump(mode="json"))


@bp.route("/<int:lot_id>", methods=["GET"])
async def get_lot_feed(lot_id: int):
    async with AsyncSessionLocal() as db:
        device = await get_current_device(db)

        lot_result = await db.execute(select(ParkingLot).where(ParkingLot.id == lot_id))
        lot = lot_result.scalar_one_or_none()
        if lot is None:
            abort(404, description=f"Parking lot {lot_id} not found")

        cutoff = datetime.now(timezone.utc) - timedelta(hours=FEED_WINDOW_HOURS)
        sightings_result = await db.execute(
            select(TapsSighting)
            .where(TapsSighting.parking_lot_id == lot_id, TapsSighting.reported_at >= cutoff)
            .order_by(TapsSighting.reported_at.desc())
        )
        sightings = sightings_result.scalars().all()

        feed_sightings = await _batch_build_feed_sightings(db, sightings, device, {lot.id: lot})

        return jsonify(FeedResponse(
            parking_lot_id=lot.id,
            parking_lot_name=lot.name,
            parking_lot_code=lot.code,
            sightings=feed_sightings,
            total_sightings=len(feed_sightings),
        ).model_dump(mode="json"))


@bp.route("/sightings/<int:sighting_id>/vote", methods=["POST"])
async def vote_on_sighting(sighting_id: int):
    data = request.get_json(force=True, silent=True) or {}
    try:
        vote_data = VoteCreate(**data)
    except Exception as e:
        abort(422, description=str(e))

    async with AsyncSessionLocal() as db:
        device = await require_verified_device(db)

        sighting_result = await db.execute(select(TapsSighting).where(TapsSighting.id == sighting_id))
        sighting = sighting_result.scalar_one_or_none()
        if sighting is None:
            abort(404, description=f"Sighting {sighting_id} not found")

        existing_vote_result = await db.execute(
            select(Vote).where(Vote.sighting_id == sighting_id, Vote.device_id == device.id)
        )
        existing_vote = existing_vote_result.scalar_one_or_none()
        vote_type_model = VoteTypeModel(vote_data.vote_type.value)

        # Toggle: same vote type clicked again → remove
        if existing_vote is not None and existing_vote.vote_type == vote_type_model:
            await db.execute(
                sa_delete(Vote).where(
                    Vote.device_id == device.id,
                    Vote.sighting_id == sighting_id,
                )
            )
            await db.commit()
            action = "removed"
            result_vote = None
        else:
            stmt = (
                _insert_fn(db)(Vote)
                .values(device_id=device.id, sighting_id=sighting_id, vote_type=vote_type_model)
                .on_conflict_do_update(
                    index_elements=["device_id", "sighting_id"],
                    set_={"vote_type": vote_type_model},
                )
            )
            await db.execute(stmt)
            await db.commit()
            action = "created" if existing_vote is None else "updated"
            result_vote = vote_data.vote_type

        # Invalidate cached vote count for this sighting
        await cache_delete(f"vote_counts:{sighting_id}")

        return jsonify(VoteResult(success=True, action=action, vote_type=result_vote).model_dump(mode="json"))


@bp.route("/sightings/<int:sighting_id>/vote", methods=["DELETE"])
async def remove_vote(sighting_id: int):
    async with AsyncSessionLocal() as db:
        device = await require_verified_device(db)

        existing_vote_result = await db.execute(
            select(Vote).where(Vote.sighting_id == sighting_id, Vote.device_id == device.id)
        )
        existing_vote = existing_vote_result.scalar_one_or_none()
        if existing_vote is None:
            abort(404, description="You haven't voted on this sighting")

        await db.delete(existing_vote)
        await db.commit()
        await cache_delete(f"vote_counts:{sighting_id}")

        return jsonify({"success": True, "message": "Vote removed"})


@bp.route("/sightings/<int:sighting_id>/votes", methods=["GET"])
async def get_sighting_votes(sighting_id: int):
    async with AsyncSessionLocal() as db:
        device = await get_current_device(db)

        sighting_result = await db.execute(select(TapsSighting).where(TapsSighting.id == sighting_id))
        sighting = sighting_result.scalar_one_or_none()
        if sighting is None:
            abort(404, description=f"Sighting {sighting_id} not found")

        cached = await cache_get(f"vote_counts:{sighting_id}")
        if cached:
            upvotes, downvotes = cached["up"], cached["down"]
        else:
            upvote_result = await db.execute(
                select(func.count()).select_from(Vote).where(
                    Vote.sighting_id == sighting_id, Vote.vote_type == VoteTypeModel.UPVOTE
                )
            )
            downvote_result = await db.execute(
                select(func.count()).select_from(Vote).where(
                    Vote.sighting_id == sighting_id, Vote.vote_type == VoteTypeModel.DOWNVOTE
                )
            )
            upvotes = upvote_result.scalar() or 0
            downvotes = downvote_result.scalar() or 0
            await cache_set(f"vote_counts:{sighting_id}", {"up": upvotes, "down": downvotes}, TTL_VOTE_COUNTS)

        user_vote_result = await db.execute(
            select(Vote.vote_type).where(Vote.sighting_id == sighting_id, Vote.device_id == device.id)
        )
        user_vote_row = user_vote_result.scalar_one_or_none()

        return jsonify({
            "sighting_id": sighting_id,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "net_score": upvotes - downvotes,
            "user_vote": user_vote_row.value if user_vote_row else None,
        })
