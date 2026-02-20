"""
Parking lots API endpoints.

Handles parking lot listing and information retrieval.
"""

from typing import List
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.schemas.parking_lot import ParkingLotResponse, ParkingLotWithStats
from app.models.parking_lot import ParkingLot
from app.models.parking_session import ParkingSession
from app.models.taps_sighting import TapsSighting
from app.services.prediction import PredictionService
from app.services.auth import get_current_device
from app.models.device import Device
from app.services.cache import cache_get, cache_set, TTL_LOTS_LIST, TTL_LOT_STATS

router = APIRouter(prefix="/lots", tags=["Parking Lots"])


@router.get(
    "",
    response_model=List[ParkingLotResponse],
    summary="List parking lots",
    description="Get a list of all active parking lots."
)
async def list_parking_lots(
    db: AsyncSession = Depends(get_db),
    _device: Device = Depends(get_current_device)
):
    cached = await cache_get("lots:all")
    if cached is not None:
        return cached

    result = await db.execute(
        select(ParkingLot).where(ParkingLot.is_active == True).order_by(ParkingLot.name)
    )
    lots = result.scalars().all()
    data = [ParkingLotResponse.model_validate(lot).model_dump(mode="json") for lot in lots]
    await cache_set("lots:all", data, TTL_LOTS_LIST)
    return data


@router.get(
    "/{lot_id}",
    response_model=ParkingLotWithStats,
    summary="Get parking lot details",
    description="Get detailed information about a specific parking lot including real-time stats."
)
async def get_parking_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
    _device: Device = Depends(get_current_device)
):
    cached = await cache_get(f"lot_stats:{lot_id}")
    if cached is not None:
        return cached

    result = await db.execute(select(ParkingLot).where(ParkingLot.id == lot_id))
    lot = result.scalar_one_or_none()
    if lot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Parking lot {lot_id} not found")

    parkers_result = await db.execute(
        select(func.count(ParkingSession.id))
        .where(ParkingSession.parking_lot_id == lot_id, ParkingSession.checked_out_at.is_(None))
    )
    active_parkers = parkers_result.scalar() or 0

    one_day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    sightings_result = await db.execute(
        select(func.count(TapsSighting.id))
        .where(TapsSighting.parking_lot_id == lot_id, TapsSighting.reported_at >= one_day_ago)
    )
    recent_sightings = sightings_result.scalar() or 0

    try:
        prediction = await PredictionService.predict(db, lot_id=lot_id)
        taps_probability = prediction.probability
    except Exception:
        taps_probability = 0.0

    data = ParkingLotWithStats(
        id=lot.id,
        name=lot.name,
        code=lot.code,
        latitude=lot.latitude,
        longitude=lot.longitude,
        is_active=lot.is_active,
        active_parkers=active_parkers,
        recent_sightings=recent_sightings,
        taps_probability=taps_probability,
    ).model_dump(mode="json")

    await cache_set(f"lot_stats:{lot_id}", data, TTL_LOT_STATS)
    return data


@router.get(
    "/code/{code}",
    response_model=ParkingLotWithStats,
    summary="Get parking lot by code",
    description="Get detailed information about a parking lot by its code."
)
async def get_parking_lot_by_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    _device: Device = Depends(get_current_device)
):
    """
    Get parking lot by its short code (e.g., 'HUTCH').

    Same response as get_parking_lot but looks up by code instead of ID.
    """
    # Get the parking lot
    result = await db.execute(
        select(ParkingLot).where(ParkingLot.code == code.upper())
    )
    lot = result.scalar_one_or_none()

    if lot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parking lot with code '{code}' not found"
        )

    # Reuse the ID-based endpoint logic
    return await get_parking_lot(lot.id, db, _device)
