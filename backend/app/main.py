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
from sqlalchemy import select, delete as sa_delete

from app.config import settings
from app.database import init_db, close_db, AsyncSessionLocal, engine, Base
from app.models.parking_lot import ParkingLot
from app.models.chat_message import ChatMessage
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
    async with AsyncSessionLocal() as db:
        lots_to_seed = [
            {"name": "Pavilion Structure", "code": "HUTCH", "latitude": 38.539674579414715, "longitude": -121.75836514704442},
            {"name": "Quad Structure", "code": "MU", "latitude": 38.54451981723509, "longitude": -121.74950799295135},
            {"name": "Lot 25", "code": "ARC", "latitude": 38.5433, "longitude": -121.7574},
            {"name": "Lot 47", "code": "TERCERO", "latitude": 38.534834, "longitude": -121.756463},
        ]
        for lot_data in lots_to_seed:
            result = await db.execute(select(ParkingLot).where(ParkingLot.code == lot_data["code"]))
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(ParkingLot(**lot_data, is_active=True))
                logger.info(f"Seeded parking lot: {lot_data['name']}")
            else:
                updated = False
                if existing.name != lot_data["name"]:
                    existing.name = lot_data["name"]
                    updated = True
                if round(existing.latitude or 0, 6) != round(lot_data["latitude"], 6) or \
                        round(existing.longitude or 0, 6) != round(lot_data["longitude"], 6):
                    existing.latitude = lot_data["latitude"]
                    existing.longitude = lot_data["longitude"]
                    updated = True
                if updated:
                    logger.info(f"Updated parking lot: {lot_data['code']}")
        await db.commit()


def _scheduled_reminder_job():
    async def _job():
        async with AsyncSessionLocal() as db:
            await run_reminder_job(db)
    _run_async(_job())


def _scheduled_auto_checkout_job():
    async def _job():
        async with AsyncSessionLocal() as db:
            await ReminderService.auto_checkout_expired_sessions(db)
    _run_async(_job())


def _scheduled_clear_chat_job():
    async def _job():
        async with AsyncSessionLocal() as db:
            await db.execute(sa_delete(ChatMessage))
            await db.commit()
        await cache_delete("chat:messages")
        logger.info("Chat messages cleared")
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
            "database": "connected",
            "scheduler": "running" if scheduler.running else "stopped",
        })

    return app


def _startup():
    """Initialize app resources at startup."""
    logger.info("Starting WarnABrotha API...")

    # Firebase
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

    # Database
    async def _init_and_seed():
        await init_db()
        await _seed_initial_data()
    _run_async(_init_and_seed())
    logger.info("Database initialized")

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
    _run_async(close_db())
    logger.info("Shutdown complete")


# Module-level app instance (for gunicorn: app.main:app)
app = create_app()
_startup()
atexit.register(_shutdown)
