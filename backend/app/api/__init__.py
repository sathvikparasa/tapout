"""
API route modules.
"""

from app.api.auth import router as auth_router
from app.api.parking_lots import router as parking_lots_router
from app.api.parking_sessions import router as parking_sessions_router
from app.api.sightings import router as sightings_router
from app.api.notifications import router as notifications_router
from app.api.predictions import router as predictions_router
from app.api.feed import router as feed_router
from app.api.ticket_scan import router as ticket_scan_router

__all__ = [
    "auth_router",
    "parking_lots_router",
    "parking_sessions_router",
    "sightings_router",
    "notifications_router",
    "predictions_router",
    "feed_router",
    "ticket_scan_router",
]
