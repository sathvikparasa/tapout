"""
Pydantic schemas for request/response validation.
"""

from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    TokenResponse,
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.schemas.parking_lot import (
    ParkingLotCreate,
    ParkingLotResponse,
    ParkingLotWithStats,
)
from app.schemas.parking_session import (
    ParkingSessionCreate,
    ParkingSessionResponse,
    CheckoutResponse,
)
from app.schemas.taps_sighting import (
    TapsSightingCreate,
    TapsSightingResponse,
    TapsSightingWithNotifications,
)
from app.schemas.notification import (
    NotificationResponse,
    NotificationList,
    MarkReadRequest,
)
from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    PredictionFactors,
)
from app.schemas.vote import (
    VoteType,
    VoteCreate,
    VoteResponse,
    VoteResult,
)
from app.schemas.feed import (
    FeedSighting,
    FeedResponse,
    AllFeedsResponse,
)
from app.schemas.ticket_scan import TicketScanResponse

__all__ = [
    # Device
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "EmailVerificationRequest",
    "EmailVerificationResponse",
    "TokenResponse",
    "SendOTPRequest",
    "SendOTPResponse",
    "VerifyOTPRequest",
    "VerifyOTPResponse",
    # Parking Lot
    "ParkingLotCreate",
    "ParkingLotResponse",
    "ParkingLotWithStats",
    # Parking Session
    "ParkingSessionCreate",
    "ParkingSessionResponse",
    "CheckoutResponse",
    # TAPS Sighting
    "TapsSightingCreate",
    "TapsSightingResponse",
    "TapsSightingWithNotifications",
    # Notification
    "NotificationResponse",
    "NotificationList",
    "MarkReadRequest",
    # Prediction
    "PredictionRequest",
    "PredictionResponse",
    "PredictionFactors",
    # Vote
    "VoteType",
    "VoteCreate",
    "VoteResponse",
    "VoteResult",
    # Feed
    "FeedSighting",
    "FeedResponse",
    "AllFeedsResponse",
    # Ticket Scan
    "TicketScanResponse",
]
