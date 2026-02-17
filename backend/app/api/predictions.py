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
    """
    Get TAPS risk prediction based on the most recent sighting globally.

    Returns:
    - Risk level (LOW, MEDIUM, HIGH)
    - Risk bars count (1-3) for UI display
    - Human-readable risk message
    """
    prediction = await PredictionService.predict(db=db)
    return prediction


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
    """
    Get TAPS risk prediction for a specific parking lot.

    Returns risk based on the most recent sighting at this lot today.
    """
    prediction = await PredictionService.predict(db=db, lot_id=lot_id)
    return prediction


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
    """
    Get TAPS risk prediction for a specific time.

    - **parking_lot_id**: Optional lot to filter by
    - **timestamp**: Time to predict for (defaults to now)
    """
    prediction = await PredictionService.predict(
        db=db,
        timestamp=request.timestamp or datetime.now(timezone.utc),
        lot_id=request.parking_lot_id,
    )
    return prediction
