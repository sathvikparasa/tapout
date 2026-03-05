"""
TAPS sightings API endpoints.

Handles reporting TAPS sightings and listing recent sightings.
"""

from typing import List
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.database import get_db
from app.schemas.taps_sighting import (
    TapsSightingCreate,
    TapsSightingResponse,
    TapsSightingWithNotifications,
)
from app.models.taps_sighting import TapsSighting
from app.models.parking_lot import ParkingLot
from app.models.device import Device
from app.models.vote import Vote, VoteType as VoteTypeModel
from app.services.auth import require_verified_device
from app.services.notification import NotificationService
from app.services.cache import cache_delete

router = APIRouter(prefix="/sightings", tags=["TAPS Sightings"])

# Any report at a lot within this window is treated as an upvote on the existing sighting
RATE_LIMIT_MINUTES = 10

_PACIFIC = ZoneInfo("America/Los_Angeles")


def _is_weekend() -> bool:
    """Returns True if it's currently Saturday or Sunday in Pacific Time.

    TAPS does not ticket on weekends, so no notifications should be sent.
    """
    return datetime.now(_PACIFIC).weekday() >= 5  # 5=Sat, 6=Sun


def _insert_fn(db: AsyncSession):
    """Return dialect-appropriate insert (PostgreSQL in prod, SQLite in tests)."""
    try:
        dialect = db.get_bind().dialect.name
    except Exception:
        dialect = "postgresql"
    return sqlite_insert if dialect == "sqlite" else pg_insert


@router.post(
    "",
    response_model=TapsSightingWithNotifications,
    status_code=status.HTTP_201_CREATED,
    summary="Report TAPS sighting",
    description="Report that TAPS has been spotted at a parking lot.",
    responses={
        200: {
            "model": TapsSightingWithNotifications,
            "description": "Report converted to an upvote — a sighting already exists at this lot within the last 10 minutes.",
        }
    },
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
    If a sighting was already reported at this lot within the last 10 minutes,
    this report is converted to an upvote on the existing sighting instead.

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

    # Acquire a per-lot advisory lock (PostgreSQL) so concurrent reports for the
    # same lot are serialized through the rate-limit check.  SQLite (used in tests)
    # doesn't support advisory locks, so we swallow the error gracefully.
    try:
        await db.execute(text("SELECT pg_advisory_xact_lock(:lot_id)"), {"lot_id": lot.id})
    except Exception:
        pass

    # Soft rate limit: if there's already a sighting at this lot within the last
    # RATE_LIMIT_MINUTES, upvote it instead of creating a new sighting.
    rate_limit_cutoff = datetime.now(timezone.utc) - timedelta(minutes=RATE_LIMIT_MINUTES)
    recent_result = await db.execute(
        select(TapsSighting)
        .where(
            TapsSighting.parking_lot_id == lot.id,
            TapsSighting.reported_at >= rate_limit_cutoff,
        )
        .order_by(TapsSighting.reported_at.desc())
        .limit(1)
    )
    recent_sighting = recent_result.scalar_one_or_none()

    if recent_sighting is not None:
        # Upsert an upvote on the existing sighting (idempotent for the same device)
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
            parking_lot_id=lot.id,
            parking_lot_name=lot.name,
            parking_lot_code=lot.code,
            reported_at=recent_sighting.reported_at,
            notes=recent_sighting.notes,
            users_notified=0,
            was_rate_limited=True,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(payload))

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

    # Fire notifications in the background — don't block the response.
    # Skip on weekends: TAPS doesn't ticket Saturday/Sunday.
    if not _is_weekend():
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
