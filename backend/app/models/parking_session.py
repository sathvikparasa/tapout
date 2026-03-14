"""ParkingSession model for Firestore."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ParkingSession:
    id: str
    device_id: str
    parking_lot_id: int
    parking_lot_name: str
    parking_lot_code: str
    checked_in_at: datetime
    is_active: bool = True
    checked_out_at: Optional[datetime] = None
    reminder_sent: bool = False

    @classmethod
    def from_dict(cls, data: dict, doc_id: str = "") -> "ParkingSession":
        return cls(
            id=doc_id or data.get("id", ""),
            device_id=data.get("device_id", ""),
            parking_lot_id=data.get("parking_lot_id", 0),
            parking_lot_name=data.get("parking_lot_name", ""),
            parking_lot_code=data.get("parking_lot_code", ""),
            checked_in_at=data.get("checked_in_at", datetime.now(timezone.utc)),
            is_active=data.get("is_active", True),
            checked_out_at=data.get("checked_out_at"),
            reminder_sent=data.get("reminder_sent", False),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_id": self.device_id,
            "parking_lot_id": self.parking_lot_id,
            "parking_lot_name": self.parking_lot_name,
            "parking_lot_code": self.parking_lot_code,
            "checked_in_at": self.checked_in_at,
            "is_active": self.is_active,
            "checked_out_at": self.checked_out_at,
            "reminder_sent": self.reminder_sent,
        }
