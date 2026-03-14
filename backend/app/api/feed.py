"""
Feed API endpoints.

Provides recent TAPS sightings feed with voting information,
grouped by parking lot location.
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, abort

from app.firestore_db import get_db
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
        # Fetch votes in chunks of 30 (Firestore "in" operator limit)
        chunks = [cache_misses[i:i+30] for i in range(0, len(cache_misses), 30)]
        for chunk in chunks:
            votes_stream = db.collection("votes").where("sighting_id", "in", chunk).stream()
            async for doc in votes_stream:
                vote = Vote.from_dict(doc.to_dict(), doc_id=doc.id)
                if vote.sighting_id in vote_data:
                    if vote.vote_type == VoteTypeModel.UPVOTE:
                        vote_data[vote.sighting_id]["up"] += 1
                    else:
                        vote_data[vote.sighting_id]["down"] += 1

        # Store freshly loaded counts in cache
        for sid in cache_misses:
            await cache_set(f"vote_counts:{sid}", vote_data[sid], TTL_VOTE_COUNTS)

    # ── 2. User's own votes — always live (personal, low cost) ─────────────
    user_votes: dict = {}
    if sighting_ids:
        chunks = [sighting_ids[i:i+30] for i in range(0, len(sighting_ids), 30)]
        for chunk in chunks:
            user_votes_stream = db.collection("votes")\
                .where("sighting_id", "in", chunk)\
                .where("device_id", "==", device.device_id)\
                .stream()
            async for doc in user_votes_stream:
                vote = Vote.from_dict(doc.to_dict(), doc_id=doc.id)
                user_votes[vote.sighting_id] = vote.vote_type

    # ── 3. Assemble ─────────────────────────────────────────────────────────
    result = []
    for sighting in sightings:
        lot = lot_by_id.get(sighting.parking_lot_id)
        if lot is None:
            continue
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
    db = get_db()
    device = await get_current_device(db)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FEED_WINDOW_HOURS)

    # Fetch all active lots
    lots_stream = db.collection("parking_lots").where("is_active", "==", True).stream()
    lots = []
    async for doc in lots_stream:
        lots.append(ParkingLot.from_dict(doc.to_dict(), doc_id=doc.id))
    lots.sort(key=lambda l: l.name)
    lot_by_id = {lot.id: lot for lot in lots}

    # Fetch all recent sightings across every lot
    all_sightings = []
    if lot_by_id:
        sightings_stream = db.collection("taps_sightings")\
            .where("reported_at", ">=", cutoff)\
            .stream()
        async for doc in sightings_stream:
            s = TapsSighting.from_dict(doc.to_dict(), doc_id=doc.id)
            if s.parking_lot_id in lot_by_id:
                all_sightings.append(s)
        all_sightings.sort(key=lambda s: s.reported_at, reverse=True)

    # Batch build with at most 2 more DB queries total
    feed_sightings_all = await _batch_build_feed_sightings(
        db, all_sightings, device, lot_by_id
    )

    # Re-group built sightings by lot for response
    built_by_lot: dict = {lot.id: [] for lot in lots}
    for fs in feed_sightings_all:
        if fs.parking_lot_id in built_by_lot:
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
    db = get_db()
    device = await get_current_device(db)

    lot_doc = await db.collection("parking_lots").document(str(lot_id)).get()
    if not lot_doc.exists:
        abort(404, description=f"Parking lot {lot_id} not found")
    lot = ParkingLot.from_dict(lot_doc.to_dict(), doc_id=lot_doc.id)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=FEED_WINDOW_HOURS)
    sightings_stream = db.collection("taps_sightings")\
        .where("parking_lot_id", "==", lot_id)\
        .where("reported_at", ">=", cutoff)\
        .stream()
    sightings = []
    async for doc in sightings_stream:
        sightings.append(TapsSighting.from_dict(doc.to_dict(), doc_id=doc.id))
    sightings.sort(key=lambda s: s.reported_at, reverse=True)

    feed_sightings = await _batch_build_feed_sightings(db, sightings, device, {lot.id: lot})

    return jsonify(FeedResponse(
        parking_lot_id=lot.id,
        parking_lot_name=lot.name,
        parking_lot_code=lot.code,
        sightings=feed_sightings,
        total_sightings=len(feed_sightings),
    ).model_dump(mode="json"))


@bp.route("/sightings/<string:sighting_id>/vote", methods=["POST"])
async def vote_on_sighting(sighting_id: str):
    data = request.get_json(force=True, silent=True) or {}
    try:
        vote_data = VoteCreate(**data)
    except Exception as e:
        abort(422, description=str(e))

    db = get_db()
    device = await require_verified_device(db)

    sighting_doc = await db.collection("taps_sightings").document(sighting_id).get()
    if not sighting_doc.exists:
        abort(404, description=f"Sighting {sighting_id} not found")

    vote_doc_id = f"{device.device_id}_{sighting_id}"
    vote_ref = db.collection("votes").document(vote_doc_id)
    existing_vote_doc = await vote_ref.get()

    vote_type_model = VoteTypeModel(vote_data.vote_type.value)

    # Toggle: same vote type clicked again → remove
    if existing_vote_doc.exists:
        existing_vote = Vote.from_dict(existing_vote_doc.to_dict(), doc_id=existing_vote_doc.id)
        if existing_vote.vote_type == vote_type_model:
            await vote_ref.delete()
            await cache_delete(f"vote_counts:{sighting_id}")
            return jsonify(VoteResult(success=True, action="removed", vote_type=None).model_dump(mode="json"))
        else:
            # Update vote type
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            await vote_ref.update({"vote_type": vote_type_model.value, "updated_at": now})
            await cache_delete(f"vote_counts:{sighting_id}")
            return jsonify(VoteResult(success=True, action="updated", vote_type=vote_data.vote_type).model_dump(mode="json"))
    else:
        # Create new vote
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        new_vote = Vote(
            id=vote_doc_id,
            device_id=device.device_id,
            sighting_id=sighting_id,
            vote_type=vote_type_model,
            created_at=now,
            updated_at=now,
        )
        await vote_ref.set(new_vote.to_dict())
        await cache_delete(f"vote_counts:{sighting_id}")
        return jsonify(VoteResult(success=True, action="created", vote_type=vote_data.vote_type).model_dump(mode="json"))


@bp.route("/sightings/<string:sighting_id>/vote", methods=["DELETE"])
async def remove_vote(sighting_id: str):
    db = get_db()
    device = await require_verified_device(db)

    vote_doc_id = f"{device.device_id}_{sighting_id}"
    vote_ref = db.collection("votes").document(vote_doc_id)
    existing_vote_doc = await vote_ref.get()
    if not existing_vote_doc.exists:
        abort(404, description="You haven't voted on this sighting")

    await vote_ref.delete()
    await cache_delete(f"vote_counts:{sighting_id}")

    return jsonify({"success": True, "message": "Vote removed"})


@bp.route("/sightings/<string:sighting_id>/votes", methods=["GET"])
async def get_sighting_votes(sighting_id: str):
    db = get_db()
    device = await get_current_device(db)

    sighting_doc = await db.collection("taps_sightings").document(sighting_id).get()
    if not sighting_doc.exists:
        abort(404, description=f"Sighting {sighting_id} not found")

    cached = await cache_get(f"vote_counts:{sighting_id}")
    if cached:
        upvotes, downvotes = cached["up"], cached["down"]
    else:
        votes_stream = db.collection("votes").where("sighting_id", "==", sighting_id).stream()
        upvotes = 0
        downvotes = 0
        async for doc in votes_stream:
            vote = Vote.from_dict(doc.to_dict(), doc_id=doc.id)
            if vote.vote_type == VoteTypeModel.UPVOTE:
                upvotes += 1
            else:
                downvotes += 1
        await cache_set(f"vote_counts:{sighting_id}", {"up": upvotes, "down": downvotes}, TTL_VOTE_COUNTS)

    # Get user's own vote
    vote_doc_id = f"{device.device_id}_{sighting_id}"
    user_vote_doc = await db.collection("votes").document(vote_doc_id).get()
    user_vote_value = None
    if user_vote_doc.exists:
        user_vote = Vote.from_dict(user_vote_doc.to_dict(), doc_id=user_vote_doc.id)
        user_vote_value = user_vote.vote_type.value

    return jsonify({
        "sighting_id": sighting_id,
        "upvotes": upvotes,
        "downvotes": downvotes,
        "net_score": upvotes - downvotes,
        "user_vote": user_vote_value,
    })
