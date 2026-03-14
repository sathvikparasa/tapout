"""
WarnABrotha API - Main application entry point (Flask).
"""

import atexit
import asyncio
import json
import logging

from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.firestore_db import get_db
from app.services.cache import cache_delete, init_cache, close_cache
from app.services.reminder import run_reminder_job, ReminderService

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _run_async(coro):
    """Run an async coroutine synchronously in a new event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _seed_initial_data():
    """Seed the database with initial parking lot data."""
    db = get_db()
    lots_to_seed = [
        {"id": 1, "name": "Pavilion Structure", "code": "HUTCH", "latitude": 38.539674579414715, "longitude": -121.75836514704442},
        {"id": 2, "name": "Quad Structure", "code": "MU", "latitude": 38.54451981723509, "longitude": -121.74950799295135},
        {"id": 3, "name": "Lot 25", "code": "ARC", "latitude": 38.5433, "longitude": -121.7574},
        {"id": 4, "name": "Lot 47", "code": "TERCERO", "latitude": 38.534834, "longitude": -121.756463},
    ]
    for lot_data in lots_to_seed:
        ref = db.collection("parking_lots").document(str(lot_data["id"]))
        doc = await ref.get()
        if not doc.exists:
            await ref.set({**lot_data, "is_active": True})
            logger.info(f"Seeded parking lot: {lot_data['name']}")
        else:
            existing = doc.to_dict()
            updates = {}
            if existing.get("name") != lot_data["name"]:
                updates["name"] = lot_data["name"]
            if existing.get("latitude") != lot_data["latitude"] or existing.get("longitude") != lot_data["longitude"]:
                updates["latitude"] = lot_data["latitude"]
                updates["longitude"] = lot_data["longitude"]
            if updates:
                await ref.update(updates)
                logger.info(f"Updated parking lot: {lot_data['code']}")


def _scheduled_reminder_job():
    from app.firestore_db import get_db as _get_db
    async def _job():
        db = _get_db()
        await run_reminder_job(db)
    _run_async(_job())


def _scheduled_auto_checkout_job():
    from app.firestore_db import get_db as _get_db
    async def _job():
        db = _get_db()
        await ReminderService.auto_checkout_expired_sessions(db)
    _run_async(_job())


def _scheduled_clear_chat_job():
    from app.firestore_db import get_db as _get_db
    async def _job():
        db = _get_db()
        # Delete all chat messages
        batch = db.batch()
        count = 0
        async for doc in db.collection("chat_messages").stream():
            batch.delete(doc.reference)
            count += 1
            if count % 500 == 0:
                await batch.commit()
                batch = db.batch()
        if count % 500 != 0:
            await batch.commit()
        await cache_delete("chat:messages")
        logger.info(f"Chat messages cleared ({count} deleted)")
    _run_async(_job())


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    CORS(app, resources={r"/*": {"origins": "*"}})

    # Rate limiter
    from app.api.auth import limiter
    limiter.init_app(app)

    # JSON error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"detail": e.description or "Bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"detail": e.description or "Unauthorized"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"detail": e.description or "Forbidden"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"detail": e.description or "Not found"}), 404

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"detail": e.description or "Unprocessable entity"}), 422

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"detail": "Too many requests. Please slow down."}), 429

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"detail": "Internal server error"}), 500

    # Register blueprints
    from app.api import (
        auth_bp, parking_lots_bp, parking_sessions_bp,
        sightings_bp, notifications_bp, predictions_bp,
        feed_bp, ticket_scan_bp, chat_bp,
    )
    prefix = f"/api/{settings.api_version}"
    app.register_blueprint(auth_bp, url_prefix=f"{prefix}/auth")
    app.register_blueprint(parking_lots_bp, url_prefix=f"{prefix}/lots")
    app.register_blueprint(parking_sessions_bp, url_prefix=f"{prefix}/sessions")
    app.register_blueprint(sightings_bp, url_prefix=f"{prefix}/sightings")
    app.register_blueprint(notifications_bp, url_prefix=f"{prefix}/notifications")
    app.register_blueprint(predictions_bp, url_prefix=f"{prefix}/predictions")
    app.register_blueprint(feed_bp, url_prefix=f"{prefix}/feed")
    app.register_blueprint(ticket_scan_bp, url_prefix=f"{prefix}/ticket-scan")
    app.register_blueprint(chat_bp, url_prefix=f"{prefix}/chat")

    @app.route("/")
    def root():
        return jsonify({
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.api_version,
        })

    @app.route("/health")
    def health_check():
        return jsonify({
            "status": "healthy",
            "database": "firestore",
            "scheduler": "running" if scheduler.running else "stopped",
        })

    return app


def _startup():
    """Initialize app resources at startup."""
    logger.info("Starting WarnABrotha API...")

    # Firebase — must be initialized BEFORE Firestore client is used
    if settings.firebase_credentials_json:
        try:
            import firebase_admin
            from firebase_admin import credentials
            cred_value = settings.firebase_credentials_json
            if cred_value.strip().startswith("{"):
                cred = credentials.Certificate(json.loads(cred_value))
            else:
                cred = credentials.Certificate(cred_value)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
    else:
        logger.warning("Firebase credentials not configured, FCM push notifications disabled")

    # Redis
    if settings.redis_host:
        init_cache(settings.redis_host, settings.redis_port)
    else:
        logger.warning("REDIS_HOST not set — caching disabled")

    # Seed initial data (Firestore — no table creation needed)
    _run_async(_seed_initial_data())
    logger.info("Initial data seeded")

    # Scheduler
    scheduler.add_job(_scheduled_reminder_job, "interval", minutes=5, id="checkout_reminder", replace_existing=True)
    scheduler.add_job(_scheduled_auto_checkout_job, CronTrigger(hour=22, minute=0, timezone="America/Los_Angeles"), id="auto_checkout", replace_existing=True)
    scheduler.add_job(_scheduled_clear_chat_job, CronTrigger(hour=2, minute=0, timezone="America/Los_Angeles"), id="clear_chat", replace_existing=True)
    scheduler.start()
    logger.info("Background scheduler started")


def _shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down WarnABrotha API...")
    if scheduler.running:
        scheduler.shutdown()
    _run_async(close_cache())
    logger.info("Shutdown complete")


# Module-level app instance (for gunicorn: app.main:app)
app = create_app()
_startup()
atexit.register(_shutdown)
