"""
WarnABrotha API - Main application entry point.

A parking enforcement tracking app for UC Davis students.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import settings
from app.database import init_db, close_db, AsyncSessionLocal, engine
from app.api import (
    auth_router,
    parking_lots_router,
    parking_sessions_router,
    sightings_router,
    notifications_router,
    predictions_router,
    feed_router,
)
from app.services.reminder import run_reminder_job
from app.models.parking_lot import ParkingLot
from app.database import Base

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Background scheduler for reminder jobs
scheduler = AsyncIOScheduler()


async def seed_initial_data():
    """
    Seed the database with initial parking lot data.
    Only adds data if the table is empty.
    """
    async with AsyncSessionLocal() as db:
        lots_to_seed = [
            {"name": "Pavilion Structure", "code": "HUTCH", "latitude": 38.5382, "longitude": -121.7617},
            {"name": "Quad Structure", "code": "MU", "latitude": 38.5425, "longitude": -121.7490},
            {"name": "Parking Lot 25", "code": "ARC", "latitude": 38.5433, "longitude": -121.7574},
        ]

        for lot_data in lots_to_seed:
            result = await db.execute(select(ParkingLot).where(ParkingLot.code == lot_data["code"]))
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(ParkingLot(**lot_data, is_active=True))
                logger.info(f"Seeded parking lot: {lot_data['name']}")
            elif existing.name != lot_data["name"]:
                existing.name = lot_data["name"]
                logger.info(f"Updated parking lot name: {lot_data['code']} -> {lot_data['name']}")

        await db.commit()


async def run_scheduled_reminder_job():
    """Wrapper to run the reminder job with a database session."""
    async with AsyncSessionLocal() as db:
        await run_reminder_job(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Manages startup and shutdown events.
    """
    # Startup
    logger.info("Starting WarnABrotha API...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Seed initial data
    await seed_initial_data()

    # Start background scheduler for reminders
    # Run every 5 minutes to check for sessions needing reminders
    scheduler.add_job(
        run_scheduled_reminder_job,
        'interval',
        minutes=5,
        id='checkout_reminder',
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down WarnABrotha API...")
    scheduler.shutdown()
    await close_db()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    WarnABrotha API - A parking enforcement tracking app for UC Davis.

    ## Features

    - **Device Registration**: Register your device and verify UC Davis email
    - **Parking Sessions**: Check in when you park, check out when you leave
    - **TAPS Sightings**: Report TAPS sightings to warn other parkers
    - **Feed**: View recent sightings (last 3 hours) with upvote/downvote voting
    - **Notifications**: Receive alerts when TAPS is spotted at your lot
    - **Predictions**: AI-powered probability predictions for TAPS presence

    ## Authentication

    All endpoints (except registration) require a Bearer token.
    Register your device first, then use the returned token in the
    Authorization header: `Authorization: Bearer <token>`
    """,
    version=settings.api_version,
    lifespan=lifespan,
)

# Add CORS middleware for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix=f"/api/{settings.api_version}")
app.include_router(parking_lots_router, prefix=f"/api/{settings.api_version}")
app.include_router(parking_sessions_router, prefix=f"/api/{settings.api_version}")
app.include_router(sightings_router, prefix=f"/api/{settings.api_version}")
app.include_router(notifications_router, prefix=f"/api/{settings.api_version}")
app.include_router(predictions_router, prefix=f"/api/{settings.api_version}")
app.include_router(feed_router, prefix=f"/api/{settings.api_version}")


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.api_version,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "scheduler": "running" if scheduler.running else "stopped",
    }
