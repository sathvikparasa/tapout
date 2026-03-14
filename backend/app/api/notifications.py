"""
Notifications API endpoints.
"""

from flask import Blueprint, request, jsonify, abort

from app.firestore_db import get_db
from app.schemas.notification import NotificationResponse, NotificationList, MarkReadRequest
from app.services.auth import get_current_device
from app.services.notification import NotificationService

bp = Blueprint("notifications", __name__)


@bp.route("", methods=["GET"])
async def get_notifications():
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    db = get_db()
    device = await get_current_device(db)
    notifications, unread_count, total = await NotificationService.get_all_notifications(
        db=db, device=device, limit=limit, offset=offset,
    )
    return jsonify(NotificationList(
        notifications=[
            NotificationResponse(
                id=n.id, notification_type=n.notification_type.value,
                title=n.title, message=n.message, parking_lot_id=n.parking_lot_id,
                created_at=n.created_at, read_at=n.read_at, is_read=n.is_read,
            )
            for n in notifications
        ],
        unread_count=unread_count, total=total,
    ).model_dump(mode="json"))


@bp.route("/unread", methods=["GET"])
async def get_unread_notifications():
    limit = request.args.get("limit", 50, type=int)

    db = get_db()
    device = await get_current_device(db)
    notifications = await NotificationService.get_unread_notifications(db=db, device=device, limit=limit)
    return jsonify(NotificationList(
        notifications=[
            NotificationResponse(
                id=n.id, notification_type=n.notification_type.value,
                title=n.title, message=n.message, parking_lot_id=n.parking_lot_id,
                created_at=n.created_at, read_at=n.read_at, is_read=n.is_read,
            )
            for n in notifications
        ],
        unread_count=len(notifications), total=len(notifications),
    ).model_dump(mode="json"))


@bp.route("/read", methods=["POST"])
async def mark_notifications_read():
    data = request.get_json(force=True, silent=True) or {}
    try:
        req = MarkReadRequest(**data)
    except Exception as e:
        abort(422, description=str(e))

    db = get_db()
    device = await get_current_device(db)
    marked_count = await NotificationService.mark_notifications_read(
        db=db, device=device, notification_ids=req.notification_ids,
    )
    return jsonify({"success": True, "marked_count": marked_count})


@bp.route("/read/all", methods=["POST"])
async def mark_all_notifications_read():
    db = get_db()
    device = await get_current_device(db)
    notifications = await NotificationService.get_unread_notifications(db=db, device=device, limit=1000)
    if not notifications:
        return jsonify({"success": True, "marked_count": 0})
    notification_ids = [n.id for n in notifications]
    marked_count = await NotificationService.mark_notifications_read(
        db=db, device=device, notification_ids=notification_ids,
    )
    return jsonify({"success": True, "marked_count": marked_count})
