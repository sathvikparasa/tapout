"""ChatMessage model for Firestore."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ChatMessage:
    id: str
    content: str
    sent_at: datetime
    is_flagged: bool = False
    flagged_reason: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict, doc_id: str = "") -> "ChatMessage":
        return cls(
            id=doc_id or data.get("id", ""),
            content=data.get("content", ""),
            sent_at=data.get("sent_at", datetime.now(timezone.utc)),
            is_flagged=data.get("is_flagged", False),
            flagged_reason=data.get("flagged_reason"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "sent_at": self.sent_at,
            "is_flagged": self.is_flagged,
            "flagged_reason": self.flagged_reason,
        }
