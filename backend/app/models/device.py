"""Device model for Firestore."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Device:
    device_id: str
    email_verified: bool = False
    is_push_enabled: bool = False
    push_token: Optional[str] = None
    created_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict, doc_id: str = "") -> "Device":
        return cls(
            device_id=doc_id or data.get("device_id", ""),
            email_verified=data.get("email_verified", False),
            is_push_enabled=data.get("is_push_enabled", False),
            push_token=data.get("push_token"),
            created_at=data.get("created_at"),
            last_seen_at=data.get("last_seen_at"),
        )

    def to_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "device_id": self.device_id,
            "email_verified": self.email_verified,
            "is_push_enabled": self.is_push_enabled,
            "push_token": self.push_token,
            "created_at": self.created_at or now,
            "last_seen_at": self.last_seen_at or now,
        }
