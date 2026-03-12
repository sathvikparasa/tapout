"""
Parking lots API endpoints.
"""

import math
import random
from typing import List
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, abort

from app.database import AsyncSessionLocal
from app.schemas.parking_lot import ParkingLotResponse, ParkingLotWithStats
from app.models.parking_lot import ParkingLot
from app.models.parking_session import ParkingSession
from app.models.taps_sighting import TapsSighting
from app.services.auth import get_current_device
from app.services.prediction import PredictionService
from app.services.cache import cache_get, cache_set, TTL_LOTS_LIST, TTL_LOT_STATS


_PT = ZoneInfo("America/Los_Angeles")


def _ghost_parker_count(lot_id: int) -> int:
    """
    Return the synthetic baseline parker count for a lot at the current moment.

    Each lot gets a stable draw from Normal(mean=15, variance=4) seeded by its
    lot ID (so the number never changes between restarts).  The baseline is only
    active on weekdays (Mon–Fri) between 06:58 and 22:03 Pacific time; outside
    those windows it returns 0.
    """
    now = datetime.now(_PT)

    # Weekends: never active
    if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return 0

    start    = now.replace(hour=6,  minute=58, second=0, microsecond=0)
    half_out = now.replace(hour=17, minute=17, second=0, microsecond=0)
    end      = now.replace(hour=22, minute=3,  second=0, microsecond=0)

    if not (start <= now <= end):
        return 0

    # Stable per-lot value: seed the RNG with the lot ID so it never drifts
    rng = random.Random(lot_id)
    value = rng.gauss(mu=10, sigma=3)
    full_count = max(0, math.floor(value))

    # After 5:17 PM, half the ghost users have left
    if now >= half_out:
        return full_count // 2
    return full_count

router = APIRouter(prefix="/lots", tags=["Parking Lots"])


@router.get(
    "",
    response_model=List[ParkingLotResponse],
    summary="List parking lots",
    description="Get a list of all active parking lots.",
)
async def list_parking_lots(
    db: AsyncSession = Depends(get_db), _device: Device = Depends(get_current_device)
):
    cached = await cache_get("lots:all")
    if cached is not None:
        return cached

    result = await db.execute(
        select(ParkingLot).where(ParkingLot.is_active == True).order_by(ParkingLot.name)
    )
    lots = result.scalars().all()
    data = [
        ParkingLotResponse.model_validate(lot).model_dump(mode="json") for lot in lots
    ]
    await cache_set("lots:all", data, TTL_LOTS_LIST)
    return data


@router.get(
    "/{lot_id}",
    response_model=ParkingLotWithStats,
    summary="Get parking lot details",
    description="Get detailed information about a specific parking lot including real-time stats.",
)
async def get_parking_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    _device: Device = Depends(get_current_device),
):
    cached = await cache_get(f"lot_stats:{lot_id}")
    if cached is not None:
        return cached

    result = await db.execute(select(ParkingLot).where(ParkingLot.id == lot_id))
    """
    Get detailed information about a parking lot.

    Includes:
    - Basic lot information
    - Number of currently parked users
    - Recent sightings count (last hour)
    - Current TAPS probability prediction
    """
    # Get the parking lot
    result = await db.execute(select(ParkingLot).where(ParkingLot.id == lot_id))
    lot = result.scalar_one_or_none()
    if lot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parking lot {lot_id} not found",
        )

    parkers_result = await db.execute(
        select(func.count(ParkingSession.id)).where(
            ParkingSession.parking_lot_id == lot_id,
            ParkingSession.checked_out_at.is_(None),
        )
    )
    active_parkers = (parkers_result.scalar() or 0) + _ghost_parker_count(lot_id)

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
