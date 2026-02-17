"""
SQLAlchemy database models.
All models inherit from Base for unified table management.
"""

from app.models.parking_lot import ParkingLot
from app.models.device import Device
from app.models.parking_session import ParkingSession
from app.models.taps_sighting import TapsSighting
from app.models.notification import Notification
from app.models.vote import Vote, VoteType
from app.models.email_otp import EmailOTP

__all__ = [
    "ParkingLot",
    "Device",
    "ParkingSession",
    "TapsSighting",
    "Notification",
    "Vote",
    "VoteType",
    "EmailOTP",
]
