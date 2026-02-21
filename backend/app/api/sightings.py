"""
TAPS sightings API endpoints.

Handles reporting TAPS sightings and listing recent sightings.
"""

from typing import List
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas.taps_sighting import (
    TapsSightingCreate,
    TapsSightingResponse,
    TapsSightingWithNotifications,
)
from app.models.taps_sighting import TapsSighting
from app.models.parking_lot import ParkingLot
from app.models.device import Device
from app.services.auth import require_verified_device
from app.services.notification import NotificationService
from app.services.cache import cache_delete

router = APIRouter(prefix="/sightings", tags=["TAPS Sightings"])


@router.post(
    "",
    response_model=TapsSightingWithNotifications,
    status_code=status.HTTP_201_CREATED,
    summary="Report TAPS sighting",
    description="Report that TAPS has been spotted at a parking lot."
)
async def report_sighting(
    sighting_data: TapsSightingCreate,
    background_tasks: BackgroundTasks,
    device: Device = Depends(require_verified_device),
    db: AsyncSession = Depends(get_db)
):
    """
    Report a TAPS sighting.

    This will notify all users currently parked at the specified lot.

    - **parking_lot_id**: ID of the parking lot where TAPS was spotted
    - **notes**: Optional notes about the sighting
    """
    # Verify parking lot exists
    result = await db.execute(
        select(ParkingLot).where(ParkingLot.id == sighting_data.parking_lot_id)
    )
    lot = result.scalar_one_or_none()

    if lot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parking lot {sighting_data.parking_lot_id} not found"
        )

    # Check for spam: prevent same device from reporting multiple times within cooldown period
    # TODO: change back to minutes=5 after testing
    five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=0)
    spam_check = await db.execute(
        select(TapsSighting)
        .where(
            TapsSighting.reported_by_device_id == device.id,
            TapsSighting.parking_lot_id == lot.id,
            TapsSighting.reported_at >= five_minutes_ago
        )
    )
    if spam_check.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You already reported TAPS at this lot within the last 5 minutes"
        )

    # Create sighting record
    sighting = TapsSighting(
        parking_lot_id=lot.id,
        reported_by_device_id=device.id,
        notes=sighting_data.notes,
    )
    db.add(sighting)
    await db.commit()
    await db.refresh(sighting)

    # Bust caches — lot stats and prediction are now stale
    await cache_delete(f"lot_stats:{lot.id}", f"prediction:{lot.id}", "prediction:global")

    # Fire notifications in the background — don't block the response
    background_tasks.add_task(
        NotificationService.notify_parked_users,
        db=db,
        parking_lot_id=lot.id,
        parking_lot_name=lot.name,
        parking_lot_code=lot.code,
    )

    return TapsSightingWithNotifications(
        id=sighting.id,
        parking_lot_id=lot.id,
        parking_lot_name=lot.name,
        parking_lot_code=lot.code,
        reported_at=sighting.reported_at,
        notes=sighting.notes,
        users_notified=0,
    )


@router.get(
    "",
    response_model=List[TapsSightingResponse],
    summary="List recent sightings",
    description="Get recent TAPS sightings across all lots."
)
async def list_sightings(
    hours: int = 24,
    lot_id: int = None,
    limit: int = 50,
    device: Device = Depends(require_verified_device),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent TAPS sightings.

    - **hours**: How many hours back to look (default 24)
    - **lot_id**: Optional filter by parking lot ID
    - **limit**: Maximum number of sightings to return
    """
    # Calculate time cutoff
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Build query
    query = select(TapsSighting).where(TapsSighting.reported_at >= cutoff)

    if lot_id is not None:
        query = query.where(TapsSighting.parking_lot_id == lot_id)

    query = query.order_by(TapsSighting.reported_at.desc()).limit(limit)

    result = await db.execute(query)
    sightings = result.scalars().all()

    # Get lot details
    lot_ids = {s.parking_lot_id for s in sightings}
    if lot_ids:
        lots_result = await db.execute(
            select(ParkingLot).where(ParkingLot.id.in_(lot_ids))
        )
        lots = {lot.id: lot for lot in lots_result.scalars().all()}
    else:
        lots = {}

    return [
        TapsSightingResponse.from_sighting(
            sighting,
            lots[sighting.parking_lot_id].name,
            lots[sighting.parking_lot_id].code
        )
        for sighting in sightings
    ]


@router.get(
    "/latest/{lot_id}",
    response_model=TapsSightingResponse,
    summary="Get latest sighting at lot",
    description="Get the most recent TAPS sighting at a specific parking lot."
)
async def get_latest_sighting(
    lot_id: int,
    device: Device = Depends(require_verified_device),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the most recent TAPS sighting at a specific parking lot.
    """
    # Verify lot exists
    lot_result = await db.execute(
        select(ParkingLot).where(ParkingLot.id == lot_id)
    )
    lot = lot_result.scalar_one_or_none()

    if lot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parking lot {lot_id} not found"
        )

    # Get latest sighting
    result = await db.execute(
        select(TapsSighting)
        .where(TapsSighting.parking_lot_id == lot_id)
        .order_by(TapsSighting.reported_at.desc())
        .limit(1)
    )
    sighting = result.scalar_one_or_none()

    if sighting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sightings found at {lot.name}"
        )

    return TapsSightingResponse.from_sighting(sighting, lot.name, lot.code)
