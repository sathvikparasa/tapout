"""
EmailOTP model for storing OTP codes sent to users for email verification.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from app.database import Base


class EmailOTP(Base):
    """
    Stores OTP codes for email verification.

    Attributes:
        id: Primary key
        device_id: FK to devices.id
        email: Email address the OTP was sent to
        otp_code: Hashed 6-digit OTP code
        created_at: When the OTP was created
        expires_at: When the OTP expires (10 minutes after creation)
        verified_at: When the OTP was successfully verified (nullable)
        attempts: Number of verification attempts made
    """

    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    email = Column(String(255), nullable=False)
    otp_code = Column(String(6), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    attempts = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("ix_email_otps_device_id", "device_id"),
        Index("ix_email_otps_email", "email"),
    )
