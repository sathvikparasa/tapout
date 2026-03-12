"""
API Blueprint modules.
"""

from app.api.auth import bp as auth_bp
from app.api.parking_lots import bp as parking_lots_bp
from app.api.parking_sessions import bp as parking_sessions_bp
from app.api.sightings import bp as sightings_bp
from app.api.notifications import bp as notifications_bp
from app.api.predictions import bp as predictions_bp
from app.api.feed import bp as feed_bp
from app.api.ticket_scan import bp as ticket_scan_bp
from app.api.chat import bp as chat_bp

__all__ = [
    "auth_bp",
    "parking_lots_bp",
    "parking_sessions_bp",
    "sightings_bp",
    "notifications_bp",
    "predictions_bp",
    "feed_bp",
    "ticket_scan_bp",
    "chat_bp",
]
