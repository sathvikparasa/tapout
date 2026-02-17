"""
Feed API endpoints.

Provides recent TAPS sightings feed with voting information,
grouped by parking lot location.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.schemas.feed import FeedSighting, FeedResponse, AllFeedsResponse
from app.schemas.vote import VoteType, VoteCreate, VoteResponse, VoteResult
from app.models.taps_sighting import TapsSighting
from app.models.parking_lot import ParkingLot
from app.models.vote import Vote, VoteType as VoteTypeModel
from app.models.device import Device
from app.services.auth import get_current_device, require_verified_device

router = APIRouter(prefix="/feed", tags=["Feed"])

# Feed window in hours (shows sightings from last 3 hours)
FEED_WINDOW_HOURS = 3


async def get_sighting_with_votes(
    db: AsyncSession,
    sighting: TapsSighting,
    device: Device,
    lot_name: str,
    lot_code: str
) -> FeedSighting:
    """
    Build a FeedSighting with vote counts and user's vote.

    Args:
        db: Database session
        sighting: The sighting to build response for
        device: Current user's device
        lot_name: Parking lot name
        lot_code: Parking lot code

    Returns:
        FeedSighting with vote information
    """
    # Count upvotes and downvotes using ORM queries
    upvote_result = await db.execute(
        select(func.count()).select_from(Vote).where(
            Vote.sighting_id == sighting.id,
            Vote.vote_type == VoteTypeModel.UPVOTE
        )
    )
    downvote_result = await db.execute(
        select(func.count()).select_from(Vote).where(
            Vote.sighting_id == sighting.id,
            Vote.vote_type == VoteTypeModel.DOWNVOTE
        )
    )
    upvotes = upvote_result.scalar() or 0
    downvotes = downvote_result.scalar() or 0

    # Get user's vote on this sighting
    user_vote_result = await db.execute(
        select(Vote.vote_type)
        .where(
            Vote.sighting_id == sighting.id,
            Vote.device_id == device.id
        )
    )
    user_vote_row = user_vote_result.scalar_one_or_none()
    user_vote = VoteType(user_vote_row.value) if user_vote_row else None

    # Calculate minutes ago
    now = datetime.now(timezone.utc)
    reported_at = sighting.reported_at
    if reported_at.tzinfo is None:
        reported_at = reported_at.replace(tzinfo=timezone.utc)
    minutes_ago = int((now - reported_at).total_seconds() / 60)

    return FeedSighting(
        id=sighting.id,
        parking_lot_id=sighting.parking_lot_id,
        parking_lot_name=lot_name,
        parking_lot_code=lot_code,
        reported_at=sighting.reported_at,
        notes=sighting.notes,
        upvotes=upvotes,
        downvotes=downvotes,
        net_score=upvotes - downvotes,
        user_vote=user_vote,
        minutes_ago=minutes_ago,
    )


@router.get(
    "",
    response_model=AllFeedsResponse,
    summary="Get all feeds",
    description="Get recent sightings (last 3 hours) grouped by parking lot."
)
async def get_all_feeds(
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db)
):
    """
    Get feeds for all parking lots with recent sightings.

    Returns sightings from the last 3 hours, grouped by lot,
    with vote counts and the current user's vote on each.
    """
    # Calculate cutoff time
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FEED_WINDOW_HOURS)

    # Get all active parking lots
    lots_result = await db.execute(
        select(ParkingLot)
        .where(ParkingLot.is_active == True)
        .order_by(ParkingLot.name)
    )
    lots = lots_result.scalars().all()

    feeds = []
    total_sightings = 0

    for lot in lots:
        # Get recent sightings for this lot
        sightings_result = await db.execute(
            select(TapsSighting)
            .where(
                TapsSighting.parking_lot_id == lot.id,
                TapsSighting.reported_at >= cutoff
            )
            .order_by(TapsSighting.reported_at.desc())
        )
        sightings = sightings_result.scalars().all()

        # Build feed sightings with vote info
        feed_sightings = []
        for sighting in sightings:
            feed_sighting = await get_sighting_with_votes(
                db, sighting, device, lot.name, lot.code
            )
            feed_sightings.append(feed_sighting)

        feeds.append(FeedResponse(
            parking_lot_id=lot.id,
            parking_lot_name=lot.name,
            parking_lot_code=lot.code,
            sightings=feed_sightings,
            total_sightings=len(feed_sightings),
        ))
        total_sightings += len(feed_sightings)

    return AllFeedsResponse(
        feeds=feeds,
        total_sightings=total_sightings,
    )


@router.get(
    "/{lot_id}",
    response_model=FeedResponse,
    summary="Get feed for specific lot",
    description="Get recent sightings (last 3 hours) for a specific parking lot."
)
async def get_lot_feed(
    lot_id: int,
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db)
):
    """
    Get feed for a specific parking lot.

    Returns sightings from the last 3 hours with vote counts
    and the current user's vote on each.
    """
    # Get parking lot
    lot_result = await db.execute(
        select(ParkingLot).where(ParkingLot.id == lot_id)
    )
    lot = lot_result.scalar_one_or_none()

    if lot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parking lot {lot_id} not found"
        )

    # Calculate cutoff time
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FEED_WINDOW_HOURS)

    # Get recent sightings
    sightings_result = await db.execute(
        select(TapsSighting)
        .where(
            TapsSighting.parking_lot_id == lot_id,
            TapsSighting.reported_at >= cutoff
        )
        .order_by(TapsSighting.reported_at.desc())
    )
    sightings = sightings_result.scalars().all()

    # Build feed sightings with vote info
    feed_sightings = []
    for sighting in sightings:
        feed_sighting = await get_sighting_with_votes(
            db, sighting, device, lot.name, lot.code
        )
        feed_sightings.append(feed_sighting)

    return FeedResponse(
        parking_lot_id=lot.id,
        parking_lot_name=lot.name,
        parking_lot_code=lot.code,
        sightings=feed_sightings,
        total_sightings=len(feed_sightings),
    )


@router.post(
    "/sightings/{sighting_id}/vote",
    response_model=VoteResult,
    summary="Vote on a sighting",
    description="Cast an upvote or downvote on a TAPS sighting."
)
async def vote_on_sighting(
    sighting_id: int,
    vote_data: VoteCreate,
    device: Device = Depends(require_verified_device),
    db: AsyncSession = Depends(get_db)
):
    """
    Vote on a TAPS sighting.

    - If you haven't voted, creates a new vote
    - If you vote the same way, removes your vote
    - If you vote differently, updates your vote

    Requires email verification.
    """
    # Verify sighting exists
    sighting_result = await db.execute(
        select(TapsSighting).where(TapsSighting.id == sighting_id)
    )
    sighting = sighting_result.scalar_one_or_none()

    if sighting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sighting {sighting_id} not found"
        )

    # Check if user already voted
    existing_vote_result = await db.execute(
        select(Vote)
        .where(
            Vote.sighting_id == sighting_id,
            Vote.device_id == device.id
        )
    )
    existing_vote = existing_vote_result.scalar_one_or_none()

    # Map schema VoteType to model VoteType
    vote_type_model = VoteTypeModel(vote_data.vote_type.value)

    if existing_vote is None:
        # Create new vote
        vote = Vote(
            device_id=device.id,
            sighting_id=sighting_id,
            vote_type=vote_type_model,
        )
        db.add(vote)
        await db.commit()
        return VoteResult(
            success=True,
            action="created",
            vote_type=vote_data.vote_type,
        )
    elif existing_vote.vote_type == vote_type_model:
        # Same vote - remove it (toggle behavior)
        await db.delete(existing_vote)
        await db.commit()
        return VoteResult(
            success=True,
            action="removed",
            vote_type=None,
        )
    else:
        # Different vote - update it
        existing_vote.vote_type = vote_type_model
        await db.commit()
        return VoteResult(
            success=True,
            action="updated",
            vote_type=vote_data.vote_type,
        )


@router.delete(
    "/sightings/{sighting_id}/vote",
    summary="Remove vote from sighting",
    description="Remove your vote from a TAPS sighting."
)
async def remove_vote(
    sighting_id: int,
    device: Device = Depends(require_verified_device),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove your vote from a sighting.
    """
    # Find existing vote
    existing_vote_result = await db.execute(
        select(Vote)
        .where(
            Vote.sighting_id == sighting_id,
            Vote.device_id == device.id
        )
    )
    existing_vote = existing_vote_result.scalar_one_or_none()

    if existing_vote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You haven't voted on this sighting"
        )

    await db.delete(existing_vote)
    await db.commit()

    return {"success": True, "message": "Vote removed"}


@router.get(
    "/sightings/{sighting_id}/votes",
    summary="Get vote counts for sighting",
    description="Get the upvote and downvote counts for a specific sighting."
)
async def get_sighting_votes(
    sighting_id: int,
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db)
):
    """
    Get vote counts for a specific sighting.
    """
    # Verify sighting exists
    sighting_result = await db.execute(
        select(TapsSighting).where(TapsSighting.id == sighting_id)
    )
    sighting = sighting_result.scalar_one_or_none()

    if sighting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sighting {sighting_id} not found"
        )

    # Count votes using ORM queries
    upvote_result = await db.execute(
        select(func.count()).select_from(Vote).where(
            Vote.sighting_id == sighting_id,
            Vote.vote_type == VoteTypeModel.UPVOTE
        )
    )
    downvote_result = await db.execute(
        select(func.count()).select_from(Vote).where(
            Vote.sighting_id == sighting_id,
            Vote.vote_type == VoteTypeModel.DOWNVOTE
        )
    )
    upvotes = upvote_result.scalar() or 0
    downvotes = downvote_result.scalar() or 0

    # Get user's vote
    user_vote_result = await db.execute(
        select(Vote.vote_type)
        .where(
            Vote.sighting_id == sighting_id,
            Vote.device_id == device.id
        )
    )
    user_vote_row = user_vote_result.scalar_one_or_none()
    user_vote = user_vote_row.value if user_vote_row else None

    return {
        "sighting_id": sighting_id,
        "upvotes": upvotes,
        "downvotes": downvotes,
        "net_score": upvotes - downvotes,
        "user_vote": user_vote,
    }
