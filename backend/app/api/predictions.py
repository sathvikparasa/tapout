"""
TAPS risk prediction API endpoints.
"""

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, abort

from app.firestore_db import get_db
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.auth import get_current_device
from app.services.prediction import PredictionService
from app.services.cache import cache_get, cache_set, TTL_PREDICTION

bp = Blueprint("predictions", __name__)


@bp.route("", methods=["GET"])
async def get_prediction_global():
    cached = await cache_get("prediction:global")
    if cached is not None:
        return jsonify(cached)

    db = get_db()
    await get_current_device(db)
    prediction = await PredictionService.predict(db=db)
    data = prediction.model_dump(mode="json")
    await cache_set("prediction:global", data, TTL_PREDICTION)
    return jsonify(data)


@bp.route("/<int:lot_id>", methods=["GET"])
async def get_prediction(lot_id: int):
    cached = await cache_get(f"prediction:{lot_id}")
    if cached is not None:
        return jsonify(cached)

    db = get_db()
    await get_current_device(db)
    prediction = await PredictionService.predict(db=db, lot_id=lot_id)
    data = prediction.model_dump(mode="json")
    await cache_set(f"prediction:{lot_id}", data, TTL_PREDICTION)
    return jsonify(data)


@bp.route("", methods=["POST"])
async def predict_for_time():
    data = request.get_json(force=True, silent=True) or {}
    try:
        req = PredictionRequest(**data)
    except Exception as e:
        abort(422, description=str(e))

    db = get_db()
    await get_current_device(db)
    prediction = await PredictionService.predict(
        db=db,
        timestamp=req.timestamp or datetime.now(timezone.utc),
        lot_id=req.parking_lot_id,
    )
    return jsonify(prediction.model_dump(mode="json"))
