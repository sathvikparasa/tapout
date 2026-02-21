"""
TAPS risk prediction API endpoints.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.models.device import Device
from app.services.auth import get_current_device
from app.services.prediction import PredictionService
from app.services.cache import cache_get, cache_set, TTL_PREDICTION

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get(
    "",
    response_model=PredictionResponse,
    summary="Get TAPS risk level",
    description="Get the current TAPS risk level based on the most recent sighting across all lots."
)
async def get_prediction_global(
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db)
):
    cached = await cache_get("prediction:global")
    if cached is not None:
        return cached

    prediction = await PredictionService.predict(db=db)
    data = prediction.model_dump(mode="json")
    await cache_set("prediction:global", data, TTL_PREDICTION)
    return data


@router.get(
    "/{lot_id}",
    response_model=PredictionResponse,
    summary="Get TAPS risk level for a lot",
    description="Get the current TAPS risk level filtered by a specific parking lot."
)
async def get_prediction(
    lot_id: int,
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db)
):
    cached = await cache_get(f"prediction:{lot_id}")
    if cached is not None:
        return cached

    prediction = await PredictionService.predict(db=db, lot_id=lot_id)
    data = prediction.model_dump(mode="json")
    await cache_set(f"prediction:{lot_id}", data, TTL_PREDICTION)
    return data


@router.post(
    "",
    response_model=PredictionResponse,
    summary="Get TAPS risk level for specific time",
    description="Get the TAPS risk level at a specific time."
)
async def predict_for_time(
    request: PredictionRequest,
    device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db)
):
    # Custom time predictions are not cached — they're one-off requests
    prediction = await PredictionService.predict(
        db=db,
        timestamp=request.timestamp or datetime.now(timezone.utc),
        lot_id=request.parking_lot_id,
    )
    return prediction
