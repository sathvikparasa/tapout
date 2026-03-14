"""Notification model for Firestore."""
import enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


class NotificationType(str, enum.Enum):
    TAPS_SPOTTED = "taps_spotted"
    CHECKOUT_REMINDER = "checkout_reminder"


@dataclass
class Notification:
    id: str
    device_id: str
    notification_type: NotificationType
    title: str
    message: str
    created_at: datetime
    parking_lot_id: Optional[int] = None
    read_at: Optional[datetime] = None

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    @classmethod
    def from_dict(cls, data: dict, doc_id: str = "") -> "Notification":
        nt = data.get("notification_type", "taps_spotted")
        return cls(
            id=doc_id or data.get("id", ""),
            device_id=data.get("device_id", ""),
            notification_type=NotificationType(nt) if isinstance(nt, str) else nt,
            title=data.get("title", ""),
            message=data.get("message", ""),
            created_at=data.get("created_at", datetime.now(timezone.utc)),
            parking_lot_id=data.get("parking_lot_id"),
            read_at=data.get("read_at"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_id": self.device_id,
            "notification_type": self.notification_type.value,
            "title": self.title,
            "message": self.message,
            "created_at": self.created_at,
            "parking_lot_id": self.parking_lot_id,
            "read_at": self.read_at,
        }
