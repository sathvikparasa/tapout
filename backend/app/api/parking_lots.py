"""
Parking lots API endpoints.
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, abort

from app.database import AsyncSessionLocal
from app.schemas.parking_lot import ParkingLotResponse, ParkingLotWithStats
from app.models.parking_lot import ParkingLot
from app.models.parking_session import ParkingSession
from app.models.taps_sighting import TapsSighting
from app.services.auth import get_current_device
from app.services.prediction import PredictionService
from app.services.cache import cache_get, cache_set, TTL_LOTS_LIST, TTL_LOT_STATS
from sqlalchemy import select, func

bp = Blueprint("parking_lots", __name__)


async def _build_lot_stats(db, lot) -> dict:
    lot_id = lot.id
    parkers_result = await db.execute(
        select(func.count(ParkingSession.id)).where(
            ParkingSession.parking_lot_id == lot_id,
            ParkingSession.checked_out_at.is_(None),
        )
    )
    active_parkers = parkers_result.scalar() or 0

    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    sightings_result = await db.execute(
        select(func.count(TapsSighting.id)).where(
            TapsSighting.parking_lot_id == lot_id,
            TapsSighting.reported_at >= one_hour_ago,
        )
    )
    recent_sightings = sightings_result.scalar() or 0

    try:
        prediction = await PredictionService.predict(db, lot_id=lot_id)
        taps_probability = prediction.probability
    except Exception:
        taps_probability = 0.0

    return ParkingLotWithStats(
        id=lot.id, name=lot.name, code=lot.code,
        latitude=lot.latitude, longitude=lot.longitude,
        is_active=lot.is_active,
        active_parkers=active_parkers,
        recent_sightings=recent_sightings,
        taps_probability=taps_probability,
    ).model_dump(mode="json")


@bp.route("", methods=["GET"])
async def list_parking_lots():
    cached = await cache_get("lots:all")
    if cached is not None:
        return jsonify(cached)

    async with AsyncSessionLocal() as db:
        await get_current_device(db)
        result = await db.execute(
            select(ParkingLot).where(ParkingLot.is_active == True).order_by(ParkingLot.name)
        )
        lots = result.scalars().all()
        data = [ParkingLotResponse.model_validate(lot).model_dump(mode="json") for lot in lots]
        await cache_set("lots:all", data, TTL_LOTS_LIST)
        return jsonify(data)


@bp.route("/<int:lot_id>", methods=["GET"])
async def get_parking_lot(lot_id: int):
    cached = await cache_get(f"lot_stats:{lot_id}")
    if cached is not None:
        return jsonify(cached)

    async with AsyncSessionLocal() as db:
        await get_current_device(db)
        result = await db.execute(select(ParkingLot).where(ParkingLot.id == lot_id))
        lot = result.scalar_one_or_none()
        if lot is None:
            abort(404, description=f"Parking lot {lot_id} not found")
        data = await _build_lot_stats(db, lot)
        await cache_set(f"lot_stats:{lot_id}", data, TTL_LOT_STATS)
        return jsonify(data)


@bp.route("/code/<string:code>", methods=["GET"])
async def get_parking_lot_by_code(code: str):
    async with AsyncSessionLocal() as db:
        await get_current_device(db)
        result = await db.execute(select(ParkingLot).where(ParkingLot.code == code.upper()))
        lot = result.scalar_one_or_none()
        if lot is None:
            abort(404, description=f"Parking lot with code '{code}' not found")

        cached = await cache_get(f"lot_stats:{lot.id}")
        if cached is not None:
            return jsonify(cached)

        data = await _build_lot_stats(db, lot)
        await cache_set(f"lot_stats:{lot.id}", data, TTL_LOT_STATS)
        return jsonify(data)
