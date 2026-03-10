"""
ChatMessage model for the global anonymous chat.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    is_flagged = Column(Boolean, default=False, nullable=False)
    flagged_reason = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, sent_at={self.sent_at})>"
