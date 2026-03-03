"""
Device model representing registered user devices.
Stores minimal information - just enough to send notifications.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Device(Base):
    """
    Represents a registered device that can receive notifications.

    We store minimal user data per requirements:
    - device_id: Unique identifier for the device
    - email_verified: Whether a valid UC Davis email was verified
    - push_token: APNs token for push notifications (optional)

    Attributes:
        id: Primary key
        device_id: Unique device identifier (UUID from iOS)
        email_verified: True if UC Davis email was verified
        push_token: APNs push notification token (nullable)
        is_push_enabled: Whether push notifications are enabled
        created_at: Timestamp when device was registered
        last_seen_at: Timestamp of last API interaction
    """

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255), nullable=False, unique=True, index=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    push_token = Column(String(255), nullable=True)
    is_push_enabled = Column(Boolean, default=False, nullable=False)
    activity_push_token = Column(String(255), nullable=True)  # iOS Live Activity push token
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    parking_sessions = relationship("ParkingSession", back_populates="device")
    taps_sightings = relationship("TapsSighting", back_populates="reported_by_device")
    notifications = relationship("Notification", back_populates="device")
    votes = relationship("Vote", back_populates="device")

    def __repr__(self):
        return f"<Device(id={self.id}, device_id='{self.device_id[:8]}...', verified={self.email_verified})>"
