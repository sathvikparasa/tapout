"""
Parking sessions API endpoints.
"""

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, abort
from sqlalchemy import select

from app.database import AsyncSessionLocal
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

    async with AsyncSessionLocal() as db:
        device = await require_verified_device(db)

        result = await db.execute(select(ParkingLot).where(ParkingLot.id == session_data.parking_lot_id))
        lot = result.scalar_one_or_none()
        if lot is None:
            abort(404, description=f"Parking lot {session_data.parking_lot_id} not found")
        if not lot.is_active:
            abort(400, description=f"Parking lot {lot.name} is not currently active")

        existing_result = await db.execute(
            select(ParkingSession).where(
                ParkingSession.device_id == device.id,
                ParkingSession.checked_out_at.is_(None),
            )
        )
        existing_session = existing_result.scalar_one_or_none()
        if existing_session is not None:
            existing_lot_result = await db.execute(select(ParkingLot).where(ParkingLot.id == existing_session.parking_lot_id))
            existing_lot = existing_lot_result.scalar_one()
            abort(400, description=f"You already have an active parking session at {existing_lot.name}. Please check out first.")

        session = ParkingSession(device_id=device.id, parking_lot_id=lot.id)
        db.add(session)
        await db.commit()
        await db.refresh(session)

        return jsonify(ParkingSessionResponse.from_session(session, lot.name, lot.code).model_dump(mode="json")), 201


@bp.route("/checkout", methods=["POST"])
async def check_out():
    async with AsyncSessionLocal() as db:
        device = await require_verified_device(db)

        result = await db.execute(
            select(ParkingSession).where(
                ParkingSession.device_id == device.id,
                ParkingSession.checked_out_at.is_(None),
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            abort(400, description="You don't have an active parking session to check out from")

        checkout_time = datetime.now(timezone.utc)
        session.checked_out_at = checkout_time
        await db.commit()

        return jsonify(CheckoutResponse(
            success=True, message="Successfully checked out",
            session_id=session.id, checked_out_at=checkout_time,
        ).model_dump(mode="json"))


@bp.route("/current", methods=["GET"])
async def get_current_session():
    async with AsyncSessionLocal() as db:
        device = await require_verified_device(db)

        result = await db.execute(
            select(ParkingSession).where(
                ParkingSession.device_id == device.id,
                ParkingSession.checked_out_at.is_(None),
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            return jsonify(None)

        lot_result = await db.execute(select(ParkingLot).where(ParkingLot.id == session.parking_lot_id))
        lot = lot_result.scalar_one()
        return jsonify(ParkingSessionResponse.from_session(session, lot.name, lot.code).model_dump(mode="json"))


@bp.route("/history", methods=["GET"])
async def get_session_history():
    limit = request.args.get("limit", 20, type=int)

    async with AsyncSessionLocal() as db:
        device = await require_verified_device(db)

        result = await db.execute(
            select(ParkingSession)
            .where(ParkingSession.device_id == device.id)
            .order_by(ParkingSession.checked_in_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()

        lot_ids = {s.parking_lot_id for s in sessions}
        lots_result = await db.execute(select(ParkingLot).where(ParkingLot.id.in_(lot_ids)))
        lots = {lot.id: lot for lot in lots_result.scalars().all()}

        return jsonify([
            ParkingSessionResponse.from_session(s, lots[s.parking_lot_id].name, lots[s.parking_lot_id].code).model_dump(mode="json")
            for s in sessions
        ])
