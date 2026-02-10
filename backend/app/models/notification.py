"""
Notification model for storing notifications for in-app polling.
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications that can be sent."""
    TAPS_SPOTTED = "taps_spotted"  # TAPS was seen at user's parked lot
    CHECKOUT_REMINDER = "checkout_reminder"  # 3-hour reminder to check out


class Notification(Base):
    """
    Stores notifications for in-app polling fallback.

    When push notifications fail or aren't available, the app polls
    this table to check for new notifications.

    Attributes:
        id: Primary key
        device_id: FK to the device that should receive this notification
        notification_type: Type of notification (TAPS_SPOTTED, CHECKOUT_REMINDER)
        title: Notification title
        message: Notification body text
        parking_lot_id: FK to related parking lot (nullable)
        created_at: When the notification was created
        read_at: When the user acknowledged the notification (NULL if unread)
        is_read: Computed property
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    notification_type = Column(
        Enum(NotificationType, name="notification_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    parking_lot_id = Column(Integer, ForeignKey("parking_lots.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    device = relationship("Device", back_populates="notifications")

    @property
    def is_read(self) -> bool:
        """Returns True if the notification has been read."""
        return self.read_at is not None

    def __repr__(self):
        status = "read" if self.is_read else "unread"
        return f"<Notification(id={self.id}, type={self.notification_type}, status={status})>"
