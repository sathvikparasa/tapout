"""EmailOTP model for Firestore."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class EmailOTP:
    id: str
    device_id: str        # device UUID string (not int PK)
    email: str
    otp_code: str
    expires_at: datetime
    created_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    attempts: int = 0

    @classmethod
    def from_dict(cls, data: dict, doc_id: str = "") -> "EmailOTP":
        return cls(
            id=doc_id or data.get("id", ""),
            device_id=data.get("device_id", ""),
            email=data.get("email", ""),
            otp_code=data.get("otp_code", ""),
            expires_at=data.get("expires_at", datetime.now(timezone.utc)),
            created_at=data.get("created_at"),
            verified_at=data.get("verified_at"),
            attempts=data.get("attempts", 0),
        )

    def to_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "id": self.id,
            "device_id": self.device_id,
            "email": self.email,
            "otp_code": self.otp_code,
            "expires_at": self.expires_at,
            "created_at": self.created_at or now,
            "verified_at": self.verified_at,
            "attempts": self.attempts,
        }
