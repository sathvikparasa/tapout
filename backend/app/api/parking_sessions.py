"""
Parking sessions API endpoints.
"""

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, abort

from app.firestore_db import get_db
from app.schemas.parking_session import ParkingSessionCreate, ParkingSessionResponse, CheckoutResponse
from app.models.parking_session import ParkingSession
from app.models.parking_lot import ParkingLot
from app.services.auth import require_verified_device

bp = Blueprint("parking_sessions", __name__)


@bp.route("/checkin", methods=["POST"])
async def check_in():
    data = request.get_json(force=True, silent=True) or {}
    try:
        session_data = ParkingSessionCreate(**data)
    except Exception as e:
        abort(422, description=str(e))

    db = get_db()
    device = await require_verified_device(db)

    lot_doc = await db.collection("parking_lots").document(str(session_data.parking_lot_id)).get()
    if not lot_doc.exists:
        abort(404, description=f"Parking lot {session_data.parking_lot_id} not found")
    lot = ParkingLot.from_dict(lot_doc.to_dict(), doc_id=lot_doc.id)
    if not lot.is_active:
        abort(400, description=f"Parking lot {lot.name} is not currently active")

    # Check for existing active session
    existing_stream = db.collection("parking_sessions")\
        .where("device_id", "==", device.device_id)\
        .where("is_active", "==", True)\
        .limit(1)\
        .stream()
    existing_session = None
    async for doc in existing_stream:
        existing_session = ParkingSession.from_dict(doc.to_dict(), doc_id=doc.id)
        break

    if existing_session is not None:
        existing_lot_doc = await db.collection("parking_lots").document(str(existing_session.parking_lot_id)).get()
        existing_lot_name = existing_lot_doc.to_dict().get("name", "unknown") if existing_lot_doc.exists else "unknown"
        abort(400, description=f"You already have an active parking session at {existing_lot_name}. Please check out first.")

    now = datetime.now(timezone.utc)
    ref = db.collection("parking_sessions").document()
    session = ParkingSession(
        id=ref.id,
        device_id=device.device_id,
        parking_lot_id=lot.id,
        parking_lot_name=lot.name,
        parking_lot_code=lot.code,
        checked_in_at=now,
        is_active=True,
        reminder_sent=False,
    )
    await ref.set(session.to_dict())

    return jsonify(ParkingSessionResponse.from_session(session, lot.name, lot.code).model_dump(mode="json")), 201


@bp.route("/checkout", methods=["POST"])
async def check_out():
    db = get_db()
    device = await require_verified_device(db)

    # Find active session
    session_stream = db.collection("parking_sessions")\
        .where("device_id", "==", device.device_id)\
        .where("is_active", "==", True)\
        .limit(1)\
        .stream()
    session = None
    session_ref = None
    async for doc in session_stream:
        session = ParkingSession.from_dict(doc.to_dict(), doc_id=doc.id)
        session_ref = doc.reference
        break

    if session is None:
        abort(400, description="You don't have an active parking session to check out from")

    checkout_time = datetime.now(timezone.utc)
    await session_ref.update({"checked_out_at": checkout_time, "is_active": False})

    return jsonify(CheckoutResponse(
        success=True, message="Successfully checked out",
        session_id=session.id, checked_out_at=checkout_time,
    ).model_dump(mode="json"))


@bp.route("/current", methods=["GET"])
async def get_current_session():
    db = get_db()
    device = await require_verified_device(db)

    session_stream = db.collection("parking_sessions")\
        .where("device_id", "==", device.device_id)\
        .where("is_active", "==", True)\
        .limit(1)\
        .stream()
    session = None
    async for doc in session_stream:
        session = ParkingSession.from_dict(doc.to_dict(), doc_id=doc.id)
        break

    if session is None:
        return jsonify(None)

    return jsonify(ParkingSessionResponse.from_session(session, session.parking_lot_name, session.parking_lot_code).model_dump(mode="json"))


@bp.route("/history", methods=["GET"])
async def get_session_history():
    limit = request.args.get("limit", 20, type=int)

    db = get_db()
    device = await require_verified_device(db)

    sessions_stream = db.collection("parking_sessions")\
        .where("device_id", "==", device.device_id)\
        .stream()
    sessions = []
    async for doc in sessions_stream:
        sessions.append(ParkingSession.from_dict(doc.to_dict(), doc_id=doc.id))

    # Sort by checked_in_at descending and apply limit
    sessions.sort(key=lambda s: s.checked_in_at, reverse=True)
    sessions = sessions[:limit]

    return jsonify([
        ParkingSessionResponse.from_session(s, s.parking_lot_name, s.parking_lot_code).model_dump(mode="json")
        for s in sessions
    ])
