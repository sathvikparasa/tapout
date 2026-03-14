"""TapsSighting model for Firestore."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TapsSighting:
    id: str
    parking_lot_id: int
    parking_lot_name: str
    parking_lot_code: str
    reported_at: datetime
    reported_by_device_id: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict, doc_id: str = "") -> "TapsSighting":
        return cls(
            id=doc_id or data.get("id", ""),
            parking_lot_id=data.get("parking_lot_id", 0),
            parking_lot_name=data.get("parking_lot_name", ""),
            parking_lot_code=data.get("parking_lot_code", ""),
            reported_at=data.get("reported_at", datetime.now(timezone.utc)),
            reported_by_device_id=data.get("reported_by_device_id"),
            notes=data.get("notes"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "parking_lot_id": self.parking_lot_id,
            "parking_lot_name": self.parking_lot_name,
            "parking_lot_code": self.parking_lot_code,
            "reported_at": self.reported_at,
            "reported_by_device_id": self.reported_by_device_id,
            "notes": self.notes,
        }
