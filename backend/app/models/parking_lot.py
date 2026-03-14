"""ParkingLot model for Firestore."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParkingLot:
    id: int
    name: str
    code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True

    @classmethod
    def from_dict(cls, data: dict, doc_id: str = "") -> "ParkingLot":
        return cls(
            id=data.get("id", int(doc_id) if doc_id.isdigit() else 0),
            name=data.get("name", ""),
            code=data.get("code", ""),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            is_active=data.get("is_active", True),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_active": self.is_active,
        }
