"""Vote model for Firestore."""
import enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


class VoteType(str, enum.Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


@dataclass
class Vote:
    id: str          # composite: "{device_id}_{sighting_id}"
    device_id: str
    sighting_id: str
    vote_type: VoteType
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict, doc_id: str = "") -> "Vote":
        vt = data.get("vote_type", "upvote")
        return cls(
            id=doc_id or data.get("id", ""),
            device_id=data.get("device_id", ""),
            sighting_id=data.get("sighting_id", ""),
            vote_type=VoteType(vt) if isinstance(vt, str) else vt,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "id": self.id,
            "device_id": self.device_id,
            "sighting_id": self.sighting_id,
            "vote_type": self.vote_type.value,
            "created_at": self.created_at or now,
            "updated_at": now,
        }
